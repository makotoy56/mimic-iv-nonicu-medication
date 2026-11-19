"""Fail-closed access guidance for real-data notebook and CLI entry points.

This module supplies no data and performs no authentication or queries on import.
It never substitutes synthetic data, cached results or another source after an
access failure. Numerical/data-quality exceptions continue to propagate.
"""
from contextlib import contextmanager
from functools import wraps
import re

from google.api_core import exceptions as api_errors
from google.auth import exceptions as auth_errors


class RealDataAccessError(RuntimeError):
    """A safe, actionable access error without request/credential contents."""


def _stop(operation, reason, next_step):
    return RealDataAccessError(
        f"Real-data execution stopped ({operation}). {reason}\n"
        f"Next: {next_step}\n"
        "No synthetic/demo data or saved results were substituted. "
        "See docs/SETUP.md and REPRODUCIBILITY.md."
    )


def require_settings(project, dataset):
    """Reject missing/example placeholders before ADC or any client operation."""
    placeholders = {"your_project", "your_dataset", "your-project", "your-dataset",
                    "project_id", "dataset_id", "replace_me", "changeme"}
    valid_project = (isinstance(project, str) and project.strip() == project
                     and project.lower() not in placeholders
                     and re.fullmatch(r"[a-z0-9][a-z0-9:.-]*", project))
    valid_dataset = (isinstance(dataset, str) and dataset.lower() not in placeholders
                     and re.fullmatch(r"[A-Za-z0-9_]{1,1024}", dataset))
    if not valid_project or not valid_dataset:
        raise _stop("configuration", "PROJECT_ID or dataset is missing or invalid.",
                    "Set PROJECT_ID and DATASET/DATASET_ID to your authorized destination; "
                    "update the matching SQL destination prefixes. Keep source prefixes unchanged.")


def require_destination(destination):
    """Validate the rebuild helper's existing PROJECT.DATASET setting."""
    if not isinstance(destination, str) or destination.count(".") != 1:
        raise _stop("configuration", "The destination must be PROJECT.DATASET.",
                    "Configure the rebuild helper and SQL prefixes as documented before running.")
    require_settings(*destination.split(".", 1))


def _guidance(error):
    if isinstance(error, (auth_errors.DefaultCredentialsError, auth_errors.RefreshError,
                          api_errors.Unauthenticated, api_errors.Unauthorized)):
        return ("Application Default Credentials are missing, expired or rejected.",
                "Outside the notebook, run gcloud auth application-default login with your "
                "approved account, then restart the kernel and retry the input step.")
    if isinstance(error, api_errors.Forbidden):
        return ("BigQuery denied access.",
                "Confirm PhysioNet/MIMIC approval for the ADC account, source-table read access, "
                "BigQuery job permissions and the destination permissions needed by this step. "
                "Ask the project administrator if access is still denied.")
    if isinstance(error, api_errors.NotFound):
        return ("A required BigQuery project, dataset or table was not found.",
                "Check project/dataset settings and US location. Derived sandbox tables may "
                "expire after 60 days; follow the documented construction/rebuild steps explicitly. "
                "This error does not create or replace any table.")
    if isinstance(error, api_errors.BadRequest):
        return ("BigQuery rejected the request (for example SQL, location or scan limit).",
                "Check the configured SQL prefixes, US source/destination location and the "
                "existing scan budget. Correct the request; do not disable or raise safety limits.")
    if isinstance(error, (api_errors.DeadlineExceeded, TimeoutError)):
        return ("The real-data operation timed out.",
                "Check the job status and authorized query scope before explicitly retrying; "
                "retain the existing timeout and processing limits.")
    if isinstance(error, api_errors.GoogleAPICallError):
        return ("The BigQuery service or connection was unavailable.",
                "Check connectivity and service status, then explicitly retry the real-data step. "
                "No model or result export should follow a failed input step.")
    if isinstance(error, auth_errors.GoogleAuthError):
        return ("Google authentication failed.",
                "Repair ADC for your approved account outside the notebook, then restart its kernel.")
    if isinstance(error, FileNotFoundError):
        return ("A required local SQL or aggregate-reference file is missing.",
                "Run from the documented repository location and check the required upstream "
                "files. Do not replace a missing clinical input with demonstration data.")
    # These are existing fail-closed checks in the unchanged input/rebuild code.
    if isinstance(error, RuntimeError) and str(error) in {
            "Source scan exceeds the 10 GiB safety limit",
            "Prediction input source scan exceeds 10 GiB"}:
        return ("The source scan exceeds the existing 10 GiB safety limit.",
                "Review the configured source and query scope; keep the processing cap unchanged.")
    if isinstance(error, ValueError) and str(error) == "Expected US source/destination location":
        return ("The source/destination location is not US.",
                "Select the documented US dataset and source location before retrying.")
    return None


@contextmanager
def real_data_errors(operation="BigQuery access"):
    """Explain known access failures; never swallow unrelated analysis errors."""
    try:
        yield
    except RealDataAccessError:
        raise
    except Exception as error:
        cause = error
        seen = set()
        while cause is not None and id(cause) not in seen:
            seen.add(id(cause))
            guidance = _guidance(cause)
            if guidance:
                # SDK exceptions can include requests or SQL. Do not echo them.
                raise _stop(operation, *guidance) from None
            cause = cause.__cause__
        raise


@contextmanager
def real_data_access(project, dataset, operation="initialize BigQuery access"):
    require_settings(project, dataset)
    with real_data_errors(operation):
        yield


def real_data_io(function):
    """Wrap an I/O helper/CLI without changing its arguments or return value."""
    @wraps(function)
    def guarded(*args, **kwargs):
        with real_data_errors(function.__name__):
            return function(*args, **kwargs)
    return guarded


def read_prediction_inputs(root=None, project=None, dataset=None):
    """Actionable entry adapter for the unchanged, verified prediction loader."""
    with real_data_access(project, dataset, "load real prediction-time inputs"):
        from prediction_time_validation import read_inputs
        kwargs = {"project": project, "dataset": dataset}
        if root is not None:
            kwargs["root"] = root
        return read_inputs(**kwargs)
