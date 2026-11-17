"""Publish canonical report images and fail on broken local report resources."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
import shutil

ROOT=Path(__file__).resolve().parents[1]
REPORT=Path('docs/reports/nonicu_raas_mortality_report.html')
IMAGE_SUFFIXES={'.png','.svg','.jpg','.jpeg','.webp','.gif'}


class ReportResources(HTMLParser):
    def __init__(self):
        super().__init__();self.resources=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.add(attrs['id'])
        key='src' if tag in {'img','script'} else 'href' if tag in {'a','link'} else None
        if key and attrs.get(key):self.resources.append((tag,attrs[key]))


def publish_report(root=ROOT):
    root=Path(root).resolve();report=root/REPORT
    if not report.exists():
        return {'copied_images':0,'checked_resources':0}
    parser=ReportResources();parser.feed(report.read_text())
    canonical=(root/'assets').resolve();public=(root/'docs/assets').resolve()
    copied=0
    for tag,url in parser.resources:
        parsed=urlsplit(url)
        if parsed.scheme or parsed.netloc:continue
        path=unquote(parsed.path)
        if not path.startswith('../assets/'):continue
        rel=Path(path.removeprefix('../assets/'))
        source=(canonical/rel).resolve();target=(public/rel).resolve()
        if not source.is_relative_to(canonical) or not target.is_relative_to(public):
            raise ValueError(f'Asset path escapes publication directories: {url}')
        if source.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError(f'Unexpected report asset type: {url}')
        if not source.is_file():raise FileNotFoundError(f'Missing canonical report asset: {url}')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or target.read_bytes()!=source.read_bytes():
            shutil.copy2(source,target);copied+=1
    checked=0
    for tag,url in parser.resources:
        parsed=urlsplit(url)
        if parsed.scheme or parsed.netloc:continue
        path=unquote(parsed.path)
        if not path:
            if parsed.fragment and unquote(parsed.fragment) not in parser.ids:
                raise ValueError(f'Broken report anchor: {url}')
            continue
        if path.startswith('/'):continue
        target=(report.parent/path).resolve()
        if not target.is_relative_to(root/'docs'):
            raise ValueError(f'Relative report resource leaves public docs root: {url}')
        if not target.is_file():raise FileNotFoundError(f'Broken local report resource: {url}')
        checked+=1
    return {'copied_images':copied,'checked_resources':checked}


if __name__=='__main__':
    print('Report publication checks:',publish_report())
