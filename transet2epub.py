import requests
import json
import subprocess as subp
from pyquery import PyQuery as pq
import sys
from urllib.parse import urljoin
from EpubCrawler.util import request_retry

MARKDOWN_PANEL = '.markdown-body'

tmpl = {
    "link": f"{MARKDOWN_PANEL} li a",
    "title": f"{MARKDOWN_PANEL}>h1",
    "content": f"{MARKDOWN_PANEL}",
    "remove": "a.anchor",
    "optiMode": "none",
    "proxy": "http://localhost:1080",
}

def process_book(el_top, base):
    url = urljoin(el_top.attr('href'), base)
    print(url)
    config = tmpl.copy()
    config['name'] = el_top.text().strip()
    config['url'] = url.replace('README.md', 'SUMMARY.md')
    open('config.json', 'w', encoding='utf8') \
        .write(json.dumps(config))
    subp.Popen('crawl-epub', shell=True).communicate()

def main():
    url = sys.argv[1]
    html = request_retry('GET', url).text
    root = pq(html)
    el_links = root(f'{MARKDOWN_PANEL} li a')
    for el in el_links:
        el = pq(el)
        if 'README.md' in el.attr('href'):
            process_book(el, url)
            
if __name__ == '__main__': main()