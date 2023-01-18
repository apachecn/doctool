from pyquery import PyQuery as pq
import re
import os
from os import path
import json
import sys
import shutil
import argparse
import subprocess as subp
import copy
import traceback
from concurrent.futures import ThreadPoolExecutor
import tempfile
import uuid
import hashlib
from imgyaso import pngquant_bts
from EpubCrawler.util import request_retry
from GenEpub import gen_epub
from EpubCrawler.img import process_img
from EpubCrawler.config import config
 
__version__ = '0.0.0.0'
config['colors'] = 256
config['imgSrc'] = ['zoomfile', 'src']
 
 
default_hdrs = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
}
 
pr = None
host = 'giantessnight.cf'
 
selectors = {
    'title': '#thread_subject',
    'content': 'td[id^=postmessage], .pattl',
    'author': 'a.xw1',
    'pages': 'div.pgt label span',
    'time': 'em[id^=authorposton]',
    'remove': '.jammer, [style="display:none"]',
    'uid': 'dd a.xi2',
    'link': '[id^=normalthread] a.xst',
}

ch_split = False
 
load_cookie = lambda: os.environ.get('GN_COOKIE', '')
 
def load_existed(fname):
    existed = []
    if path.exists(fname):
        existed = json.loads(open(fname).read())
    return set(existed)

def fname_escape(name):
     
    return name.replace('\\', '＼') \
               .replace('/', '／') \
               .replace(':', '：') \
               .replace('*', '＊') \
               .replace('?', '？') \
               .replace('"', '＂') \
               .replace('<', '＜') \
               .replace('>', '＞') \
               .replace('|', '｜')
                
 
def get_info(html):
    root = pq(html)
    title = root(selectors['title']).eq(0).text().strip()
    author = root(selectors['author']).eq(0).text().strip()
    el_page = root(selectors['pages'])
    if len(el_page) == 0:
        pages = 1
    else:
        pages = el_page.attr('title')
        pages = int(pages.split(' ')[1])
    return {
        'title': fname_escape(title),
        'pages': pages,
        'author': author,
    }
     
def get_uid(html):
    root = pq(html)
    uid = root(selectors['uid']).eq(0).text().strip()
    return uid
 
def get_last_time(html):
    root = pq(html)
    time_str = root(selectors['time']).eq(-1).html()
    time_str = re.search(r'\d+\-\d+\-\d+', time_str).group()
    time_str = ''.join([
        s.zfill(2)
        for s in time_str.split('-')
    ])
    return time_str
 
def get_contents(html):
    root = pq(html)
    root(selectors['remove']).remove()
    el_contents = root(selectors['content'])
    contents = [
        '<div>' + pq(c).html() + '</div>'
        for c in el_contents
    ]
    return contents

def md5(s):
    return hashlib \
        .md5(s.encode('utf-8')) \
        .hexdigest()
     
def download_art(url, articles, imgs, cookie):
    hdrs = default_hdrs.copy()
    hdrs['Cookie'] = cookie
    html = request_retry('GET', url, headers=hdrs, proxies=pr).text
    contents = get_contents(html)
    for c in contents:
        c = process_img(
            c, imgs, 
            img_prefix='../Images/',
            page_url=url,
        )
        articles.append({
            'title': str(len(articles)),
            'content': c
        })
     
def get_info_by_tid(tid, cookie):
    hdrs = default_hdrs.copy()
    hdrs['Cookie'] = cookie
    url = f'https://{host}/gnforum2012/forum.php?mod=viewthread&tid={tid}'
    html = request_retry('GET', url, headers=hdrs, proxies=pr).text
    uid = get_uid(html)
    if not uid: return
    url = f'https://{host}/gnforum2012/forum.php?mod=viewthread&tid={tid}&page=1000000&authorid={uid}'
    html = request_retry('GET', url, headers=hdrs, proxies=pr).text
    info = get_info(html)
    info['uid'] = uid
    info['time'] = get_last_time(html)
    return info
     
def download_split(args):
    tid, cookie = args.tid, args.cookie
    try: os.mkdir('out')
    except: pass
     
    info = get_info_by_tid(tid, cookie)
    if not info:
        print(f'{tid} 不存在')
        return
    uid = info['uid']
    tm = info['time']
    if args.start and tm < args.start:
        print(f'日期 {tm} 小于起始日期 {args.start}')
        return
    if args.end and tm > args.end:
        print(f'日期 {tm} 大于终止日期 {args.end}')
        return
    print(f"tid: {tid}, title: {info['title']}, time: {info['time']}")
    
    for i in range(1, info['pages'] + 1):
        print(f'page: {i}')
        name = ' - '.join([
            info['title'],
            info['author'],
            info['time'],
            f'pt{i}'
        ])
        if name in existed:
            print('已存在')
            return
        p = f"out/{name}.epub"
        if path.exists(p):
            print('已存在')
            continue
        articles = [{
            'title': info['title'] + f' - pt{i}',
            'content': f'<p>作者：{info["author"]}</p><p>TID：{tid}</p>'
        }]
        imgs = {}
        url = f'https://{host}/gnforum2012/forum.php?mod=viewthread&tid={tid}&page={i}&authorid={uid}'
        download_art(url, articles, imgs, cookie)
        gen_epub(articles, imgs, None, p)
     
def download_safe(args):
    try: download(args)
    except: traceback.print_exc()
     
def download(args):
    tid, ch_split, cookie = args.tid, args.split, args.cookie
    if ch_split: 
        download_split(args)
        return

    try: os.mkdir('out')
    except: pass
 
    info = get_info_by_tid(tid, cookie)
    if not info:
        print(f'{tid} 不存在')
        return
    uid = info['uid']
    tm = info['time']
    if args.start and tm < args.start:
        print(f'日期 {tm} 小于起始日期 {args.start}')
        return
    if args.end and tm > args.end:
        print(f'日期 {tm} 大于终止日期 {args.end}')
        return
    print(f"tid: {tid}, title: {info['title']}, time: {info['time']}")
     
    name = ' - '.join([
        info['title'],
        info['author'],
        info['time'],
    ])
    existed = load_existed(args.existed_list) 
    if name in existed:
        print('已存在')
        return
    p = f"out/{name}.epub"
    if path.exists(p):
        print('已存在')
        return
     
    articles = [{
        'title': info['title'],
        'content': f'<p>作者：{info["author"]}</p><p>TID：{tid}</p>'
    }]
    imgs ={}
    for i in range(1, info['pages'] + 1):
        print(f'page: {i}')
        url = f'https://{host}/gnforum2012/forum.php?mod=viewthread&tid={tid}&page={i}&authorid={uid}'
        download_art(url, articles, imgs, cookie)
     
    gen_epub(articles, imgs, None, p)
 
def get_tids(html):
    root = pq(html)
    el_links = root(selectors['link'])
    links = [pq(l).attr('href') for l in el_links]
    links = [re.search(r'tid=(\d+)', l).group(1) for l in links]
    return links
     
def batch(args):
    fname = args.fname
    with open(fname, encoding='utf-8') as f:
        tids = f.read().split('\n')
    tids = filter(None, [t.strip() for t in tids])
    pool = ThreadPoolExecutor(args.threads)
    hdls = []
    for t in tids: 
        args = copy.deepcopy(args)
        args.tid = t
        h = pool.submit(download_safe, args)
        hdls.append(h)
    for h in hdls: h.result()
    
     
def fetch(args):
    fname, fid, st, ed = args.fname, args.fid, args.start, args.end
    f = open(fname, 'a', encoding='utf-8')
    hdrs = default_hdrs.copy()
    hdrs['Cookie'] = args.cookie
    for i in range(st, ed + 1):
        print(f'page: {i}')
        url = f'https://{host}/gnforum2012/forum.php?mod=forumdisplay&fid={fid}&page={i}'
        html = request_retry('GET', url, headers=hdrs, proxies=pr).text
        tids = get_tids(html)
        if len(tids) == 0: break
        for t in tids:
            print(t)
            f.write(t + '\n')
            f.flush()
         
    f.close()
    
def extract(args):
    dir = args.dir
    res = [
        f.replace('.epub', '')
        for f in os.listdir(dir)
        if f.endswith('.epub')
    ]
    ofname = path.abspath(dir) + '.json'
    open(ofname, 'w', encoding='utf-8') \
        .write(json.dumps(res))
     
def main():
    parser = argparse.ArgumentParser(prog="GnCralwer", description="GnCralwer", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"BookerWikiTool version: {__version__}")
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers()
    
    dl_parser = subparsers.add_parser("dl", help="download a page")
    dl_parser.add_argument("tid", help="tid")
    dl_parser.add_argument("-S", "--split", action='store_true', help="whether to split ch")
    dl_parser.add_argument("-s", "--start", help="staring date")
    dl_parser.add_argument("-e", "--end", help="ending date")
    dl_parser.add_argument("-c", "--cookie", default=load_cookie(), help="gn cookie")
    dl_parser.add_argument("-l", "--existed-list", default='gn_existed.json', help="existed fnames JSON")
    dl_parser.set_defaults(func=download)

    fetch_parser = subparsers.add_parser("fetch", help="fetch tids")
    fetch_parser.add_argument("fname", help="fname")
    fetch_parser.add_argument("fid", help="fid")
    fetch_parser.add_argument("-s", "--start", type=int, default=1, help="staring page num")
    fetch_parser.add_argument("-e", "--end", type=int, default=10000000, help="ending page num")
    fetch_parser.add_argument("-c", "--cookie", default=load_cookie(), help="gn cookie")
    fetch_parser.set_defaults(func=fetch)

    batch_parser = subparsers.add_parser("batch", help="batch download")
    batch_parser.add_argument("fname", help="fname")
    batch_parser.add_argument("-S", "--split", action='store_true', help="whether to split ch")
    batch_parser.add_argument("-s", "--start", help="staring date")
    batch_parser.add_argument("-e", "--end", help="ending date")
    batch_parser.add_argument("-c", "--cookie", default=load_cookie(), help="gn cookie")
    batch_parser.add_argument("-t", "--threads", type=int, default=8, help="num of threads")
    batch_parser.add_argument("-l", "--existed-list", default='gn_existed.json', help="existed fnames JSON")
    batch_parser.set_defaults(func=batch)

    ext_parser = subparsers.add_parser("ext", help="ext fnames into JSON")
    ext_parser.add_argument("dir", help="dir name")
    ext_parser.set_defaults(func=extract)
    
    search_parser = subparsers.add_parser("search", help="search file in existed")
    search_parser.add_argument("kw", help="key word")
    search_parser.set_defaults(func=lambda args: print(args.kw in existed))
    
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__': main()