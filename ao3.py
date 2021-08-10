import requests
from pyquery import PyQuery as pq
from datetime import datetime, timedelta
import sys, re, os, json
import subprocess as subp
from os import path
import tempfile
import uuid
import time
import calendar

host = 'archiveofourown.org'

pr = {
    # 'http': 'https://localhost:1080',
    # 'https': 'https://localhost:1080',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
}

def request_retry(method, url, retry=10, **kw):
    kw.setdefault('timeout', 10)
    for i in range(retry):
        try:
            return requests.request(method, url, **kw)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print(f'{url} retry {i}')
            if i == retry - 1: raise e

get_retry = lambda *args, **kwargs: \
    request_retry('GET', *args, **kwargs)


def get_article(html):
    root = pq(html)
    title = root('h2.title').text().strip()
    root('h2.title').remove()
    co = root('div.preface').html() + '\n' + \
         str(root('dl.meta')) + '\n' + \
         root('div.userstuff').html()
    return {
        'title': title,
        'content': co,
    }
    
def safe_mkdir(dir):
    try:
        os.mkdir(dir)
    except:
        pass
        
def safe_rmdir(dir):
    try:
        os.rmdir(dir)
    except:
        pass

def get_ids(html):
    root = pq(html)
    el_links = root.find('h4 a:first-of-type')
    return [
        pq(l).attr('href').split('/')[-1]
        for l in el_links
    ]
    
def dl_ids(ids, articles):
    i = 1
    while i < len(ids):
        id = ids[i]
        print(f'id: {id}')
        url = f'https://{host}/works/{id}?view_adult=true'
        r = get_retry(
            url, 
            headers=headers, 
            proxies=pr,
            timeout=8,
        )
        if r.status_code == 429:
            print('HTTP 429')
            time.sleep(10)
            continue
        html = r.text
        art = get_article(html)
        articles.append(art)
        i += 1

def download(ori_st=None, ori_ed=None, pg=1):
    now = datetime.now()
    ori_st = ori_st or now.strftime('%Y%m%d')
    ori_ed = ori_ed or now.strftime('%Y%m%d')
    
    fname = f'out/ao3_{ori_st}_{ori_ed}.epub'
    if path.exists(fname):
        print('已存在')
        return
    articles = [{
        'title': f'ao3_{ori_st}_{ori_ed}',
        'content': '',
    }]
    
    st = datetime.strptime(ori_st, '%Y%m%d')
    ed = datetime.strptime(ori_ed,'%Y%m%d')
    ed += timedelta(1)
    days_st = (now - ed).days
    days_ed = (now - st).days
    print(f'days start: {days_st}, days end: {days_ed}')
    
    i = pg
    while True:
        print(f'page: {i}')
        url = f'https://{host}/works/search?utf8=%E2%9C%93&commit=Search&page={i}&work_search%5Brevised_at%5D={days_st}-{days_ed}+days&work_search%5Blanguage_id%5D=zh&work_search%5Bsort_direction%5D=desc&work_search%5Bsort_column%5D=revised_at'
        
        r = get_retry(
            url, 
            headers=headers, 
            proxies=pr,
            timeout=8,
        )
        if r.status_code == 429:
            print('HTTP 429')
            time.sleep(10)
            continue
        html = r.text
        ids = get_ids(html)
        if len(ids) == 0: break
        for id in ids:
            dl_ids(ids, articles)
        
        i += 1
        
    gen_epub(articles, None, fname)

def gen_epub(articles, imgs, p):   
    imgs = imgs or {}

    dir = path.join(tempfile.gettempdir(), uuid.uuid4().hex) 
    safe_mkdir(dir)
    img_dir = path.join(dir, 'img')
    safe_mkdir(img_dir)
    
    for fname, img in imgs.items():
        fname = path.join(img_dir, fname)
        with open(fname, 'wb') as f:
            f.write(img)
    
    fname = path.join(dir, 'articles.json')
    with open(fname, 'w') as f:
        f.write(json.dumps(articles))
    
    args = f'gen-epub "{fname}" -i "{img_dir}" -p "{p}"'
    subp.Popen(args, shell=True).communicate()
    safe_rmdir(dir)

def main():
    op = sys.argv[1]
    if op in ['dl', 'download']:
        download(
            sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else None,
            int(sys.argv[4]) if len(sys.argv) > 4 else 1,
        )
        
if __name__ == '__main__': main()
