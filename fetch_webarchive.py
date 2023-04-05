import argparse
import re
from EpubCrawler.util import request_retry
from urllib.parse import urlparse

PAGE_SIZE = 10000
__version__ = '0.0.0.0'

def get_url_key(url, args):
    info = urlparse(url)
    k = info.path
    if args.query: k += '?' + info.query
    if args.fragment: k += '#' + info.fragment
    return k

def url_dedup(li, args):
    res = []
    for url in li:
        k = get_url_key(url, args)
        if not re.search(args.regex, k): continue
        if k in args.vis: continue
        res.append(url)
        args.vis.add(k)
    return res


def main():
    parser = argparse.ArgumentParser(prog="fetch-webarchive", description="iBooker WIKI tool", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"BookerWikiTool version: {__version__}")
    parser.set_defaults(vis=set())
    
    parser.add_argument("host", help="host")
    parser.add_argument("-s", "--start", type=int, default=1, help="starting page")
    parser.add_argument("-e", "--end", type=int, default=1_000_000_000, help="ending page")
    parser.add_argument("-r", "--regex", default='.', help="regex to match urls")
    parser.add_argument("-q", "--query", action='store_true', help="whether to deduplicate with query")
    parser.add_argument("-f", "--fragment", action='store_true', help="whether to deduplicate with fragment")
    args = parser.parse_args()
    
    ofname = re.sub('\W', '_', args.host) + '_' + str(args.start) + '_' + str(args.end) + '.txt'
    ofile = open(ofname, 'w', encoding='utf8')
    
    for i in range(args.start, args.end):
        print(f'page: {i}')
        offset = (i - 1) * PAGE_SIZE
        url = (
            'https://web.archive.org/cdx/search/cdx' +
            f'?url={args.host}/*&output=json' +
            '&filter=statuscode:200&filter=mimetype:text/html' +
            f'&limit={PAGE_SIZE}&offset={offset}' +
            '&collapse=urlkey&fl=original'
        )
        j = request_retry('GET', url).json()
        if not j: break
        li = [l[0] for l in j[1:]]
        li = url_dedup(li, args)
        for url in li:
            ofile.write(f'https://web.archive.org/web/{url}\n')
        
    ofile.close()
        
        
if __name__ == '__main__': main()