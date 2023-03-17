from EpubCrawler.util import request_retry
import sys
import re
from datetime import datetime, timedelta
from pyquery import PyQuery as pq

def get_links(html, dt):
    dt_str = dt.strftime('%Y-%m-%d')
    rt = pq(html)
    links = [pq(el).attr('href') for el in rt('.postArticle-readMore>a')]
    tms = [pq(el).attr('datetime')[:10] for el in rt('time')]
    links = [
        l + '#' + t
        for l, t in zip(links, tms)
        if t == dt_str
    ]
    return links

def main():
    now = datetime.now()
    host, st, ed = (
        sys.argv[1], 
        sys.argv[2] if len(sys.argv) > 2 else f'{now.year}0101', 
        sys.argv[3] if len(sys.argv) > 3 else f'{now.year}{now.month:02d}{now.day:02d}'
    )
    ofname = re.sub(r'\W', '_', host) + '_' + st + '_' + ed
    stdt = datetime(int(st[:4]), int(st[4:6]), int(st[6:8]))
    eddt = datetime(int(ed[:4]), int(ed[4:6]), int(ed[6:8]))
    ofile = open(ofname, 'w', encoding='utf8')
    dt = stdt
    while dt <= eddt:
        url = f'https://{host}/archive/{dt.year}/{dt.month:02d}/{dt.day:02d}/'
        print(url)
        html = request_retry('GET', url).text
        links = get_links(html, dt)
        print('\n'.join(links))
        ofile.write('\n'.join(links) + '\n')
        dt = dt + timedelta(days=1)
    ofile.close()
    
if __name__ == '__main__': main()