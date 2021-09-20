from EpubCrawler.util import request_retry
import sys
import json

pr = {
    'http': 'localhost:1080',
    'https': 'localhost:1080',
}

def get_info(fname, un, fid, pg=1):
    ofile = open(fname, 'a')
    i = (pg - 1) * 24
    while True:
        print(f'page: {i // 24 + 1}')
        url = f'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?username={un}&offset={i}&limit=24&folderid={fid}'
        j = request_retry('GET', url, proxies=pr).json()
        for it in j['results']:
            durl = it['deviation']['url']
            print(durl)
            ofile.write(durl + '\n')
        if not j['hasMore']: break
        i = j['nextOffset']
        
def main():
    cmd = sys.argv[1]
    arg = sys.argv[2]
    if cmd == 'info':
        get_info(
            arg, sys.argv[3], sys.argv[4], 
            int(sys.argv[5]) if len(sys.argv) > 5 else 1
        )
        
if __name__ == '__main__': main()