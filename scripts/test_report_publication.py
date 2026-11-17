from pathlib import Path
from tempfile import TemporaryDirectory
from quarto_normalize_outputs import publish_report

with TemporaryDirectory() as tmp:
    root=Path(tmp);(root/'docs/reports').mkdir(parents=True);(root/'assets').mkdir()
    (root/'assets/new.png').write_bytes(b'aggregate test image')
    report=root/'docs/reports/nonicu_raas_mortality_report.html'
    report.write_text('<h1 id="ok">Report</h1><img src="../assets/new.png"><a href="#ok">Top</a>')
    assert publish_report(root)['copied_images']==1
    assert (root/'docs/assets/new.png').read_bytes()==b'aggregate test image'
    assert publish_report(root)['copied_images']==0
    report.write_text('<img src="../assets/missing.png">')
    try:publish_report(root)
    except FileNotFoundError:pass
    else:raise AssertionError('Missing canonical image must block publication')
    report.write_text('<a href="../docs/FIRTH_SENSITIVITY_VALIDATION.md">broken</a>')
    try:publish_report(root)
    except FileNotFoundError:pass
    else:raise AssertionError('Broken relative validation link must block publication')
    report.write_text('<img src="../assets/../../../private.png">')
    try:publish_report(root)
    except ValueError:pass
    else:raise AssertionError('Asset traversal must be rejected')
print('PASS: canonical image synchronization is idempotent; missing images, broken links and path traversal block publication')
