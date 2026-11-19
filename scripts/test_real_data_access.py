"""Offline access-failure checks; no credentials, source rows or real queries."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import ast
import json
import runpy
import socket
import sys
from unittest.mock import Mock, patch

import pandas as pd
import google.auth
from google.api_core import exceptions as api_errors
from google.auth import exceptions as auth_errors
from google.cloud import bigquery

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from real_data_access import (RealDataAccessError, real_data_access, real_data_errors,
                              real_data_io, read_prediction_inputs, require_destination)
from nonicu_notebook_results import NotebookResults
import prediction_time_validation as prediction


def forbidden(*args, **kwargs):
    raise AssertionError("Network/credential access is forbidden in this test")


socket.create_connection = forbidden
socket.socket.connect = forbidden
google.auth.default = forbidden


def expect_stopped(action, *fragments):
    try:
        action()
    except RealDataAccessError as error:
        text = str(error)
        assert all(part in text for part in fragments), text
        assert "Next:" in text and "No synthetic/demo data or saved results were substituted" in text
        assert "PRIVATE_REQUEST_MARKER" not in text
        return error
    raise AssertionError("Access failure was silently accepted")


def guarded_failure(error):
    with real_data_access("approved-project", "analysis"):
        raise error


for project, dataset in [(None, "analysis"), ("", "analysis"), ("YOUR_PROJECT", "analysis"),
                          ("approved-project", None), ("approved-project", ""),
                          ("approved-project", "YOUR_DATASET"), ("approved-project", "bad.dataset")]:
    called = Mock()
    def action():
        with real_data_access(project, dataset):
            called()
    expect_stopped(action, "configuration", "Set PROJECT_ID")
    called.assert_not_called()
expect_stopped(lambda: require_destination("missing_dataset_part"), "PROJECT.DATASET")
print("PASS: 8 missing/placeholder/invalid destination cases stop before authentication or I/O")

errors = [
    (auth_errors.DefaultCredentialsError("PRIVATE_REQUEST_MARKER"), "gcloud auth application-default login"),
    (auth_errors.RefreshError("PRIVATE_REQUEST_MARKER"), "gcloud auth application-default login"),
    (api_errors.Unauthorized("PRIVATE_REQUEST_MARKER"), "gcloud auth application-default login"),
    (api_errors.Forbidden("PRIVATE_REQUEST_MARKER"), "PhysioNet/MIMIC approval"),
    (api_errors.NotFound("PRIVATE_REQUEST_MARKER"), "60 days"),
    (api_errors.BadRequest("PRIVATE_REQUEST_MARKER"), "do not disable or raise safety limits"),
    (api_errors.DeadlineExceeded("PRIVATE_REQUEST_MARKER"), "timed out"),
    (api_errors.ServiceUnavailable("PRIVATE_REQUEST_MARKER"), "service status"),
    (FileNotFoundError("PRIVATE_REQUEST_MARKER"), "repository location"),
    (ValueError("Expected US source/destination location"), "US dataset"),
    (RuntimeError("Prediction input source scan exceeds 10 GiB"), "10 GiB"),
]
for error, next_step in errors:
    stopped = expect_stopped(lambda: guarded_failure(error), next_step)
    assert stopped.__suppress_context__
original = AssertionError("Synthetic data-quality rejection")
try:
    guarded_failure(original)
except AssertionError as error:
    assert error is original
else:
    raise AssertionError("A data-quality exception was swallowed")
print("PASS: 11 access failures explain next steps safely; unrelated analysis errors propagate unchanged")


@real_data_io
def wrapped_validation_failure():
    try:
        raise api_errors.Forbidden("PRIVATE_REQUEST_MARKER")
    except api_errors.Forbidden as error:
        raise RuntimeError("Step failed") from error


expect_stopped(wrapped_validation_failure, "BigQuery denied access")
events = []
view = NotebookResults({}, emit=events.append)
def failed_cell():
    with view.capture("Table 00.1", {}):
        print("No completed result")
        raise api_errors.Forbidden("PRIVATE_REQUEST_MARKER")
expect_stopped(failed_cell, "BigQuery denied access")
assert not events
print("PASS: nested CLI errors and asynchronous notebook failures stop without a stale-result display")

# All seven direct-client notebook entry cells must catch missing ADC before
# creating a client. Execute their actual source with mocked SDK boundaries.
authentication_checks = 0
for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    nb = json.loads(path.read_text())
    sources = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    if path.name.startswith("04c"):
        assert any("from real_data_access import read_prediction_inputs as read_inputs" in s for s in sources)
        continue
    source = next(s for s in sources if "bigquery.Client(" in s)
    assert "with real_data_access(" in source
    missing = Mock(side_effect=auth_errors.DefaultCredentialsError("PRIVATE_REQUEST_MARKER"))
    client = Mock(side_effect=AssertionError("Client creation must not follow missing ADC"))
    namespace = {"default": missing, "bigquery": bigquery, "project_id": "approved-project",
                 "dataset_id": "analysis", "LOCATION": "US"}
    with patch.object(google.auth, "default", missing), patch.object(bigquery, "Client", client):
        expect_stopped(lambda: exec(compile(source, str(path), "exec"), namespace),
                       "gcloud auth application-default login")
    assert missing.call_count == 1
    client.assert_not_called()
    authentication_checks += 1
assert authentication_checks == 7
print("PASS: all 7 direct-client notebooks stop on mocked missing ADC; 04c uses the guarded loader")

# Exercise the actual decorated notebook I/O helpers after authentication,
# including delayed job/dataframe errors. Do not execute setup/query cells.
helper_checks = 0
for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    nb = json.loads(path.read_text())
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        for function in ast.parse("".join(cell["source"])).body:
            if not isinstance(function, ast.FunctionDef) or function.name not in {"run_sql_script", "query_to_df"}:
                continue
            assert any(isinstance(n, ast.Name) and n.id == "real_data_io" for n in function.decorator_list)
            client = Mock()
            client.query.return_value.result.side_effect = api_errors.Forbidden("PRIVATE_REQUEST_MARKER")
            client.query.return_value.to_dataframe.side_effect = api_errors.NotFound("PRIVATE_REQUEST_MARKER")
            namespace = {"Path": Path, "pd": pd, "client": client, "real_data_io": real_data_io}
            exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
            argument = ROOT / "sql/03_define_exposure_raas_early.sql" if function.name == "run_sql_script" else "SELECT 1"
            with redirect_stdout(StringIO()):
                expect_stopped(lambda: namespace[function.name](argument),
                               "denied access" if function.name == "run_sql_script" else "not found")
            assert client.query.call_count == 1
            helper_checks += 1
assert helper_checks == 7
nb = json.loads((ROOT / "notebooks/00_setup.ipynb").read_text())
definitions = [node for cell in nb["cells"] if cell["cell_type"] == "code"
               for node in ast.parse("".join(cell["source"])).body
               if isinstance(node, ast.FunctionDef) and node.name in {"dataset_reference", "ensure_dataset_exists"}]
client = Mock(); client.get_dataset.side_effect = api_errors.Forbidden("PRIVATE_REQUEST_MARKER")
namespace = {"client": client, "bigquery": bigquery, "NotFound": api_errors.NotFound,
             "project_id": "approved-project", "dataset_id": "analysis", "LOCATION": "US", "real_data_io": real_data_io}
exec(compile(ast.Module(body=definitions, type_ignores=[]), "dataset setup helpers", "exec"), namespace)
expect_stopped(namespace["ensure_dataset_exists"], "denied access")
client.create_dataset.assert_not_called()
print("PASS: 7 actual SQL/dataframe helpers stop on delayed permission/missing-table failures; denied dataset access never attempts creation")

# The adapter forwards successful real inputs unchanged and never supplies a
# DataFrame of its own. A failed load cannot reach fitting or exporting.
sentinel = object()
with patch.object(prediction, "read_inputs", return_value=sentinel) as load:
    assert read_prediction_inputs(ROOT, "approved-project", "analysis") is sentinel
    load.assert_called_once_with(root=ROOT, project="approved-project", dataset="analysis")
fit, export = Mock(), Mock()
def pipeline():
    data = read_prediction_inputs(ROOT, "approved-project", "analysis")
    export(fit(data))
with patch.object(prediction, "read_inputs", side_effect=api_errors.Forbidden("PRIVATE_REQUEST_MARKER")):
    expect_stopped(pipeline, "BigQuery denied access")
fit.assert_not_called(); export.assert_not_called()
with patch.object(prediction, "read_inputs") as load:
    expect_stopped(lambda: read_prediction_inputs(ROOT, "YOUR_PROJECT", "analysis"), "configuration")
    load.assert_not_called()
print("PASS: prediction input identity/arguments are retained; failed or invalid inputs never reach fitting/export")

# Exercise the unchanged loader's real dry-run and dataset checks through a
# fake BigQuery client; do not weaken its 10 GiB cap or US restriction.
client = Mock()
client.get_dataset.return_value.location = "US"
client.query.return_value.total_bytes_processed = prediction.LIMIT + 1
with patch.object(bigquery, "Client", return_value=client):
    expect_stopped(lambda: read_prediction_inputs(ROOT, "approved-project", "analysis"), "10 GiB")
assert client.query.call_count == 1
config = client.query.call_args.kwargs["job_config"]
assert config.dry_run and config.use_query_cache is False
assert client.query.call_args.kwargs["location"] == "US"
client = Mock(); client.get_dataset.return_value.location = "EU"
with patch.object(bigquery, "Client", return_value=client):
    expect_stopped(lambda: read_prediction_inputs(ROOT, "approved-project", "analysis"), "US dataset")
client.query.assert_not_called()
client = Mock(); client.get_dataset.side_effect = api_errors.NotFound("PRIVATE_REQUEST_MARKER")
with patch.object(bigquery, "Client", return_value=client):
    expect_stopped(lambda: read_prediction_inputs(ROOT, "approved-project", "analysis"), "60 days")
client.query.assert_not_called()
client = Mock(); client.get_dataset.return_value.location = "US"
dry, failed_job = Mock(total_bytes_processed=1), Mock()
failed_job.result.side_effect = api_errors.Forbidden("PRIVATE_REQUEST_MARKER")
client.query.side_effect = [dry, failed_job]
with patch.object(bigquery, "Client", return_value=client):
    expect_stopped(lambda: read_prediction_inputs(ROOT, "approved-project", "analysis"), "denied access")
assert client.query.call_count == 2
assert client.query.call_args.kwargs["job_config"].maximum_bytes_billed == prediction.LIMIT
print("PASS: mocked loader retains US, dry-run/no-cache and 10 GiB rejection; missing datasets issue no query")

# Entry CLIs must report ADC failure before real requests. The explicit static
# feature-list check is separately executable without an authenticated client.
for name, args in [("rebuild_analysis_tables.py", []),
                   ("validation_checklist.py", ["--step", "row_counts"]),
                   ("prediction_time_chronology_sensitivity.py", [])]:
    target = ROOT / "scripts" / name
    auth = Mock(side_effect=auth_errors.DefaultCredentialsError("PRIVATE_REQUEST_MARKER"))
    client = Mock(side_effect=auth_errors.DefaultCredentialsError("PRIVATE_REQUEST_MARKER"))
    with patch.object(sys, "argv", [str(target)] + args), patch.object(google.auth, "default", auth), \
            patch.object(bigquery, "Client", client), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        expect_stopped(lambda: runpy.run_path(str(target), run_name="__main__"),
                       "gcloud auth application-default login")
target = ROOT / "scripts/validation_checklist.py"
client = Mock(side_effect=AssertionError("Offline check must not construct a BigQuery client"))
with patch.object(sys, "argv", [str(target), "--step", "forbidden"]), \
        patch.object(bigquery, "Client", client), redirect_stdout(StringIO()):
    runpy.run_path(str(target), run_name="__main__")
client.assert_not_called()
print("PASS: all 3 CLI entry points stop on mocked missing ADC; explicit forbidden-feature check stays offline")

# The safety/rebuild and numerical source remain directly inspectable.
rebuild = (ROOT / "scripts/rebuild_analysis_tables.py").read_text()
assert "if not args.execute:" in rebuild and "except NotFound:" in rebuild
assert "INTERVAL 60 DAY" in rebuild and "maximum_bytes_billed=LIMIT" in rebuild
tree = ast.parse((ROOT / "scripts/prediction_time_validation.py").read_text())
assert any(isinstance(n, ast.FunctionDef) and n.name == "read_inputs" for n in tree.body)
print("PASS: explicit construction gating, missing-only creation, expiration and processing caps are retained")
