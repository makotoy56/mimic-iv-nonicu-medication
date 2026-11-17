"""Synthetic boundary checks; no MIMIC records are used."""
import json
from pathlib import Path
import pandas as pd

base = pd.Timestamp("2020-01-01")
def t(hours):
    return None if hours is None else base + pd.Timedelta(hours=hours)

# name, admission hour, discharge hour, death hour, flag, expected reason
cases = [
    ("survivor", 0, 48, None, 0, "included"),
    ("later_death", 0, 48, 36, 1, "included"),
    ("death_at_discharge", 0, 48, 48, 1, "included"),
    ("live_early", 0, 12, None, 0, "discharge_at_or_before_24h"),
    ("live_boundary", 0, 24, None, 0, "discharge_at_or_before_24h"),
    ("live_just_after", 0, 24.000001, None, 0, "included"),
    ("early_death", 0, 48, 12, 1, "death_at_or_before_24h"),
    ("death_boundary", 0, 48, 24, 1, "death_at_or_before_24h"),
    ("death_just_after", 0, 48, 24.000001, 1, "included"),
    ("death_unknown", 0, 48, None, 1, "death_flag_without_deathtime"),
    ("death_inconsistent_flag", 0, 48, 36, 0, "survival_flag_with_deathtime"),
    ("death_before_admit", 0, 48, -1, 1, "death_before_admission"),
    ("death_after_discharge", 0, 48, 49, 1, "death_after_discharge"),
    ("missing_discharge", 0, None, None, 0, "missing_dischtime"),
    ("missing_admission", None, 48, None, 0, "missing_admittime"),
    ("discharge_before_admit", 0, -1, None, 0, "discharge_before_admission"),
    ("missing_flag", 0, 48, None, None, "invalid_or_missing_expire_flag"),
    ("invalid_flag", 0, 48, None, 2, "invalid_or_missing_expire_flag"),
]
df = pd.DataFrame([dict(admittime=t(a), dischtime=t(d), deathtime=t(e), hospital_expire_flag=f)
                   for _, a, d, e, f, _ in cases])
ns = {"pd": pd}
notebook = json.loads((Path(__file__).resolve().parents[1] / "notebooks/04b_multivariable_outcomes.ipynb").read_text())
classifier = next("".join(c["source"]) for c in notebook["cells"]
                  if c["cell_type"] == "code" and "def classify_landmark(data):" in "".join(c["source"]))
exec(classifier, ns)
classify = ns["classify_landmark"]
old, new, reason, diagnostics, flow = classify(df)
assert reason.tolist() == [c[-1] for c in cases], reason.tolist()
assert old.iloc[3] and old.iloc[4] and old.iloc[9]  # previously admitted erroneous cases
assert not old.iloc[7]  # old death boundary was already strict
assert int(new.sum()) == 5
assert diagnostics.set_index("issue").loc["live_discharge_at_or_before_24h", "retained_by_original"] == 2
assert diagnostics.set_index("issue").loc["death_exactly_24h", "retained_by_original"] == 0
assert flow["admissions"].sum() == len(df)
for col in ["admittime", "dischtime", "deathtime"]:
    bad = df.iloc[[0]].copy().astype({col: "object"})
    bad.loc[bad.index[0], col] = "not-a-time"
    assert classify(bad)[2].iloc[0] == f"invalid_{col}"
try:
    classify(df.drop(columns="dischtime"))
except ValueError:
    pass
else:
    raise AssertionError("Missing required schema must fail closed")
# Non-default index, timezone conversion and input immutability.
copy = df.copy(deep=True)
classify(df.set_axis(range(100, 100+len(df))))
assert df.equals(copy)
zoned = df.copy()
for col in ["admittime", "dischtime", "deathtime"]:
    zoned[col] = pd.to_datetime(zoned[col], utc=True).dt.tz_convert("Asia/Tokyo")
assert classify(zoned)[1].tolist() == new.tolist()
print("PASS: 18 boundary/cohort cases, 3 invalid-time cases, schema failure, timezone, index and immutability")

# Exercise the notebook's actual refit helper on synthetic data, including failed fits.
import numpy as np
import warnings
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import PerfectSeparationError
rng = np.random.default_rng(42)
count = 2400
synthetic = pd.DataFrame({"age": rng.normal(60, 10, count),
                          "exposure": rng.integers(0, 2, count)})
synthetic["outcome"] = rng.binomial(1, .10, count)
categories = ["gender", "race_group", "admission_type", "insurance", "anchor_year_group"]
for c in categories + ["admission_location"]:
    synthetic[c] = rng.choice(["A", "B"], count)
synthetic.loc[0, "age"] = np.nan
synthetic.loc[1:100, "admission_location"] = None
model_cell = next("".join(c["source"]) for c in notebook["cells"]
                  if c["cell_type"] == "code" and "def fit_landmark_model(" in "".join(c["source"]))
model_ns = dict(pd=pd, np=np, sm=sm, warnings=warnings, cat_vars=categories, num_vars=["age"])
exec(model_cell.split("df_lm_original =", 1)[0], model_ns)
for proxy in [False, True]:
    fitted, result = model_ns["fit_landmark_model"](synthetic, "synthetic", proxy)
    assert fitted is not None and result["converged"] and result["inference_valid"]
    assert result["n"] == count - 1 and result["dropped_numeric"] == 1
    assert result["deaths"] == int(synthetic.iloc[1:]["outcome"].sum())
    assert result["CI_lower"] <= result["OR"] <= result["CI_upper"]
degenerate = synthetic.copy()
degenerate["exposure"] = 0  # zero column gives a singular design
_, failed = model_ns["fit_landmark_model"](degenerate, "synthetic singular")
assert not failed["inference_valid"] and failed["fit_error"] == "LinAlgError"
invalid = synthetic.copy()
invalid.loc[1, "outcome"] = np.nan
_, invalid_result = model_ns["fit_landmark_model"](invalid, "synthetic unknown outcome")
assert invalid_result["invalid_outcome"] == 1 and invalid_result["fit_error"] == "InvalidOutcome"
assert not invalid_result["inference_valid"]
print("PASS: ordinary/proxy synthetic refits, missing covariate counts, convergence and singular-fit reporting")

# Integrate the diagnostic decisions with all four fits and the presentation table.
synthetic["admittime"] = base
synthetic["dischtime"] = base + pd.Timedelta(hours=48)
synthetic["deathtime"] = pd.NaT
synthetic.loc[synthetic["outcome"].eq(1), "deathtime"] = base + pd.Timedelta(hours=36)
early = synthetic["outcome"].eq(0) & (synthetic.index < 100)
synthetic.loc[early, "dischtime"] = base + pd.Timedelta(hours=12)
synthetic["hospital_expire_flag"] = synthetic["outcome"]
synthetic["raas_any_early"] = synthetic["exposure"]
old_mask, corrected_mask, *_ = classify(synthetic)
primary_fit, _ = model_ns["fit_landmark_model"](synthetic, "synthetic primary")
conf = primary_fit.conf_int()
or_ci = pd.DataFrame({"OR": np.exp(primary_fit.params), "CI_lower": np.exp(conf[0]),
                      "CI_upper": np.exp(conf[1]), "p_value": primary_fit.pvalues})
integration = dict(model_ns, df=synthetic, model=primary_fit, or_ci=or_ci,
                   original_lm_mask=old_mask, corrected_lm_mask=corrected_mask,
                   display=lambda table: None)
exec(model_cell, integration)
comparison = integration["landmark_model_comparison"].set_index("model")
assert len(comparison) == 4 and len(integration["compare_or"]) == 3
assert comparison["inference_valid"].all()
assert comparison.loc["24h landmark", "n"] == int((corrected_mask & synthetic["age"].notna()).sum())
assert comparison.loc["24h landmark + proxy", "n"] == comparison.loc["24h landmark", "n"]
assert comparison.loc["Original condition", "cohort_n"] - comparison.loc["24h landmark", "cohort_n"] == int(early.sum())
assert integration["df_lm"]["dischtime"].gt(base + pd.Timedelta(hours=24)).all()
print("PASS: full original/corrected ordinary/proxy comparison and primary presentation integration")


# Failed convergence must skip the historical-figure export and allow later cells.
figure_cell = next("".join(c["source"]) for c in notebook["cells"]
                   if c["cell_type"] == "code" and "Landmark figure not refreshed:" in "".join(c["source"]))
exec(figure_cell, {"compare_raw": pd.DataFrame({"inference_valid": [False, False, False]})})
print("PASS: unconverged real-data state skips figure export without stopping subsequent cells")
