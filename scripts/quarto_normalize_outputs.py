from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
REPORT_NAME = "nonicu_raas_mortality_report.html"


def remove_empty_parents(path: Path, stop: Path) -> None:
    while path != stop and path.exists():
        try:
            path.rmdir()
        except OSError:
            break
        path = path.parent


target = ROOT / "outputs" / "reports" / REPORT_NAME
project_nested = ROOT / "outputs" / "reports" / "reports" / REPORT_NAME
legacy_nested = ROOT / "reports" / "outputs" / "reports" / REPORT_NAME

target.parent.mkdir(parents=True, exist_ok=True)

if project_nested.exists():
    shutil.move(str(project_nested), str(target))
    remove_empty_parents(project_nested.parent, ROOT / "outputs" / "reports")

if legacy_nested.exists():
    legacy_nested.unlink()
    remove_empty_parents(legacy_nested.parent, ROOT / "reports")
