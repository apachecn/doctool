import os
import sys
import shutil
import subprocess as subp
from os import path
import re
import tempfile
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
import requests
from pyquery import PyQuery as pq
from GenEpub import gen_epub

cookie = os.environ.get('WK8_COOKIE', '')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Cookie': cookie,
}

def load_dt_map():
    if not path.exists('dt.txt'):
        return {}
    dt_map = {}
    lines = open('dt.txt', encoding='utf-8') \
        .read().split('\n')
    lines = filter(None, map(lambda x: x.strip()))
    lines = filter(lambda x: len(x) >= 2, 
        map(lambda x: x.split(' ')))
    for l in lines: dt_map[l[0]] = l[1]
    return dt_map
    
dt_map = load_dt_map()
    
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
            
def format_text(text):
    # 多个换行变为一个
    text = re.sub(r'(\r\n)+', '\r\n', text)
    # 去掉前两行
    text = re.sub(r'^.+?\r\n.+?\r\n', '', text)
    # 去掉后两行
    text = re.sub(r'\r\n.+?\r\n.+?$', '', text)
    # 划分标题和段落
    def rep_func(m):
        s = m.group(1)
        return '<p>' + s[4:] + '</p>' \
            if s.startswith('    ') else \
            '<!--split--><h1>' + s + '</h1>'
    text = re.sub(r'^(.+?)$', rep_func, text, flags=re.M)
    # 拆分章节，过滤空白章节
    chs = filter(None, text.split('<!--split-->'))
    # 将章节拆分为标题和内容
    map_func = lambda x: {
        'title': re.search(r'<h1>(.+?)</h1>', x).group(1),
        'content': re.sub(r'<h1>.+?<\/h1>', '', x),
    }
    return list(map(map_func, chs))
    
def get_info(html):
    root = pq(html)
    dt = root('#content > div:nth-child(1) > table:nth-child(1) tr:nth-child(2) > td:nth-child(4)').text()[5:].replace('-', '')
    url = root('#content > div:nth-child(1) > div:nth-child(6) > div > span:nth-child(1) > fieldset > div > a').attr('href')
    title = root('#content > div:nth-child(1) > table:nth-child(1) tr:nth-child(1) > td > table tr > td:nth-child(1) > span > b').text()
    author = root('#content > div:nth-child(1) > table:nth-child(1) tr:nth-child(2) > td:nth-child(2)').text()[5:]
    return {'dt': dt, 'url': url, 'title': fname_escape(title), 'author': fname_escape(author)}
    
def safe_mkdir(dir):
    try: os.mkdir(dir)
    except: pass
    
def download(id):
    url = f'https://www.wenku8.net/book/{id}.htm'
    html = request_retry('GET', url, headers=headers).content.decode('gbk')
    info = get_info(html)
    info['dt'] = info['dt'] or dt_map.get(id, 'UNKNOWN')
    print(info['title'], info['author'], info['dt'])
    
    ofname = f"out/{info['title']} - {info['author']} - {info['dt']}.epub"
    if path.exists(ofname):
        print('已存在')
        return
    safe_mkdir('out')
    
    articles = [{
        'title': info['title'], 
        'content': f"<p>作者：{info['author']}</p>",
    }]
    url = f'http://dl.wenku8.com/down.php?type=utf8&id={id}'
    text = request_retry('GET', url, headers=headers).content.decode('utf-8')
    chs = format_text(text)
    articles += chs
    gen_epub(articles, {}, None, ofname)
    
def safe_rmdir(dir):
    try: shutil.rmtree(dir)
    except: pass
    
def download_safe(id):
    try: download(id)
    except Exception as ex: print(ex)
    
def batch(fname):
    lines = open(fname, encoding='utf-8').read().split('\n')
    lines = filter(None, map(lambda x: x.strip(), lines))
    pool = ThreadPoolExecutor(5)
    hdls = []
    for id in lines:
        hdl = pool.submit(download_safe, id.split(' ')[0])
        hdls.append(hdl)
    for h in hdls: h.result()
    
def get_toc(html):
    root = pq(html)
    el_links = root('table.grid b a')
    el_dts = root('table.grid div > div:nth-child(2) > p:nth-child(3)')
    res = []
    for i in range(len(el_links)):
        id = re.search(r'/(\d+)\.htm', el_links.eq(i).attr('href')).group(1)
        dt = el_dts.eq(i).text().split('/')[0][3:].replace('-', '')
        if dt != '':
            res.append({'id': id, 'dt': dt})
    return res
        
    
def fetch(fname, st, ed, with_dt=False):
    ofile = open(fname, 'a', encoding='utf-8')
    
    stop = False
    i = 1
    while True:
        if stop: break
        print(f'page: {i}')
        url = f'https://www.wenku8.net/modules/article/index.php?page={i}'
        html = request_retry('GET', url, headers=headers).content.decode('gbk')
        toc = get_toc(html)
        if len(toc) == 0: break
        for bk in toc:
            if ed and bk['dt'] > ed:
                continue
            if st and bk['dt'] < st:
                stop = True
                break
            print(bk['id'], bk['dt'])
            if with_dt:
                ofile.write(bk['id'] + ' ' + bk['dt'] + '\n')
            else:
                ofile.write(bk['id'] + '\n')
        i += 1
        
    ofile.close()
    
def main():
    cmd = sys.argv[1]
    arg = sys.argv[2]
    if cmd == 'dl' or cmd == 'download': download(arg)
    elif cmd == 'batch': batch(arg)
    elif cmd == 'fetch': fetch(arg, sys.argv[3], sys.argv[4])
    elif cmd == 'fetchdt': fetch(arg, sys.argv[3], sys.argv[4], True)
    
    
if __name__ == '__main__': main()  
