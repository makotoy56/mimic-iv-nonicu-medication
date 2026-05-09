# SAS Workflow Directory

This folder contains SAS-side files for the non-ICU RAAS medication analysis and cross-platform validation workflow.

## Directory Layout

- `inputs/`: Uploaded CSV analytic datasets used as SAS import sources.
- `data/`: SAS datasets created after importing input CSV files.
- `programs/`: SAS programs for import, baseline summaries, unadjusted analysis, and multivariable logistic regression reproduction.
- `outputs/`: SAS-generated PDFs and CSV validation outputs.
- `logs/`: SAS logs, if exported from SAS Studio or another SAS environment.
- `docs/`: SAS-specific documentation, notes, or validation references.

Keep this structure flat and simple so SAS outputs can be compared transparently with the Python validation artifacts.
