"""Verify the deployed report bytes and every same-site linked resource (stdlib only)."""
from hashlib import sha256
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from quarto_normalize_outputs import ReportResources

URL='https://makotoy56.github.io/mimic-iv-nonicu-medication/reports/nonicu_raas_mortality_report.html'
ROOT=Path(__file__).resolve().parents[1]


def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'portfolio-publication-check/1.0'}),timeout=30) as response:
        if response.status!=200:raise RuntimeError(f'HTTP {response.status}: {url}')
        return response.read()


def check_live():
    content=fetch(URL)
    local=ROOT/'docs/reports/nonicu_raas_mortality_report.html'
    if sha256(content).digest()!=sha256(local.read_bytes()).digest():
        raise ValueError('Live HTML differs from the local rendered report; wait for deployment')
    parser=ReportResources();parser.feed(content.decode())
    urls=set()
    for _,url in parser.resources:
        if not urlsplit(url).path:continue
        target=urljoin(URL,url)
        if urlsplit(target).netloc==urlsplit(URL).netloc:urls.add(target.split('#')[0])
    for url in sorted(urls):fetch(url)
    print(f'PASS: live HTML matches local report; {len(urls)} linked same-site resources return HTTP 200')
    return len(urls)


if __name__=='__main__':check_live()
