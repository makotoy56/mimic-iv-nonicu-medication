"""Explicit Firth sensitivity fits; never replace the historical primary MLE.

All admission rows remain local/in memory. Only model-level aggregates are returned.
Frequency compression combines identical design/outcome rows exactly, not sampling.
"""
from importlib.metadata import version
import warnings
import numpy as np
import pandas as pd
from scipy.special import expit
from firthmodels import FirthLogisticRegression

NUMERIC = ["age"]
CATEGORIES = ["gender", "race_group", "admission_type", "insurance", "anchor_year_group"]


def model_inputs(frame, with_proxy=False):
    work = frame.copy()
    categories = CATEGORIES + (["admission_location"] if with_proxy else [])
    for column in categories:
        work[column] = work[column].fillna("Unknown")
    # Keep the previous sensitivity model's encoding and numeric-missing rule.
    encoded = pd.get_dummies(work, columns=categories, drop_first=True).dropna(subset=NUMERIC)
    columns = ["exposure"] + NUMERIC
    for column in categories:
        columns += [c for c in encoded if c.startswith(f"{column}_")]
    X = encoded[columns].astype(float)
    y = pd.to_numeric(encoded["outcome"], errors="raise")
    if not y.isin([0, 1]).all():
        raise ValueError("Outcome must be observed binary data; unknown outcomes cannot be coded as survival")
    y = y.to_numpy(dtype=int)
    # Affine age transformation improves conditioning without changing covariates.
    X["age"] = (X["age"] - 60.0) / 10.0
    return X, y


def frequency_compress(X, y):
    unique, counts = np.unique(np.column_stack([np.asarray(X, dtype=float), y]),
                               axis=0, return_counts=True)
    return unique[:, :-1], unique[:, -1].astype(int), counts.astype(float)


def adjusted_score(X, y, counts, coef, intercept):
    """Independent score check for the Jeffreys-penalized likelihood."""
    design = np.column_stack([X, np.ones(len(X))])
    beta = np.r_[coef, intercept]
    probability = expit(design @ beta)
    weight = counts * probability * (1.0 - probability)
    info = design.T @ (weight[:, None] * design)
    leverage = weight * np.einsum("ij,ji->i", design, np.linalg.solve(info, design.T))
    score = design.T @ (counts * (y - probability) + leverage * (0.5 - probability))
    return float(np.max(np.abs(score)))


def fit_firth(frame, label, with_proxy=False):
    X, y = model_inputs(frame, with_proxy)
    compressed_X, compressed_y, counts = frequency_compress(X, y)
    design = np.column_stack([compressed_X, np.ones(len(compressed_X))])
    rank = int(np.linalg.matrix_rank(design))
    if rank != design.shape[1]:
        raise ValueError("Firth fit requires a full-rank design; no columns are silently dropped")
    direction = np.zeros(design.shape[1])
    direction[-1] = -1.0
    for i, column in enumerate(X.columns):
        if column.startswith("admission_type_"):
            direction[i] = 1.0
    margins = (2 * compressed_y - 1) * (design @ direction)
    separation_certificate = bool((margins >= 0).all() and (margins > 0).any())
    model = FirthLogisticRegression(backend="numpy", max_iter=200, gtol=1e-7, xtol=1e-7)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(compressed_X, compressed_y, sample_weight=counts)
        ci = model.conf_int(method="pl", features=[0], max_iter=100, tol=1e-7)[0]
        model.lrt(features=[0])
    score = adjusted_score(compressed_X, compressed_y, counts, model.coef_, model.intercept_)
    point = float(np.exp(model.coef_[0]))
    interval = np.exp(ci)
    warning_names = sorted({type(w.message).__name__ for w in caught})
    valid = bool(model.converged_ and np.isfinite([point, *interval, model.lrt_pvalues_[0]]).all()
                 and 0 < interval[0] <= point <= interval[1]
                 and score < 1e-5 and "ConvergenceWarning" not in warning_names)
    row = dict(model=label, method="Firth (Jeffreys penalty)", ci_method="penalized profile likelihood",
               cohort_n=len(frame), n=len(y), deaths=int(y.sum()), dropped_numeric=len(frame)-len(y),
               OR=point, CI_lower=float(interval[0]), CI_upper=float(interval[1]),
               p_value=float(model.lrt_pvalues_[0]), converged=bool(model.converged_),
               inference_valid=valid, iterations=int(model.n_iter_), max_adjusted_score=score,
               design_rank=rank, parameters=int(design.shape[1]),
               compression_rows=len(counts), frequency_sum=int(counts.sum()),
               separation_certificate=separation_certificate, warnings=", ".join(warning_names),
               firthmodels_version=version("firthmodels"))
    return model, row


def export_firth_figure(results, path):
    """Draw only numerically checked Firth/profile results, with explicit labels."""
    from pathlib import Path
    if not results["inference_valid"].all():
        print("Firth figure not refreshed: model/profile checks did not pass.")
        return None
    import matplotlib.pyplot as plt
    selected = results.set_index("model").loc[
        ["Primary cohort", "24h landmark", "24h landmark + proxy"]]
    labels = ["Primary cohort", "24h landmark", "24h landmark + admission source"]
    labels = [f"{label}\nN={int(row.n):,}; deaths={int(row.deaths):,}"
              for label, row in zip(labels, selected.itertuples())]
    positions = np.arange(len(selected))
    fig, ax = plt.subplots(figsize=(9.0, 4.0))
    ax.errorbar(selected["OR"], positions,
                xerr=[selected["OR"]-selected["CI_lower"], selected["CI_upper"]-selected["OR"]],
                fmt="o", color="#2563eb", capsize=5, elinewidth=2)
    ax.axvline(1, color="#64748b", linestyle="--", linewidth=1.2)
    ax.set_xscale("log")
    ax.set_xlim(0.2,1.2)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Early RAAS prescription exposure OR (log scale)")
    ax.set_title("Firth sensitivity analysis: 95% penalized profile intervals")
    ax.spines[["top","right","left"]].set_visible(False)
    ax.tick_params(axis="y",length=0)
    fig.text(.03,.02,"Supplementary estimator; original unpenalized primary fit retained. Observational associations.",
             fontsize=9,color="#475569")
    fig.tight_layout(rect=[0,.06,1,1])
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=200,bbox_inches="tight")
    plt.close(fig)
    return path
