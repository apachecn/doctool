import os
from os import path
import shutil
import requests
from pyquery import PyQuery as pq
import execjs
import sys
import cv2
import numpy as np
import re
from imgyaso import grid
import tempfile
import json
import uuid
import subprocess as subp

headers = {
    'Referer': 'http://manhua.dmzj.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
}

d = lambda name: path.join(path.dirname(__file__, name))

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
            
def load_existed():
    exi = []
    fname = 'dmzj_existed.json'
    if path.exists(fname):
        exi = json.loads(open(fname, encoding='utf-8').read())
    return set(exi)
    
existed = load_existed()

def get_info(html):
    root = pq(html)
    title = root('.anim_title_text h1').text()
    author = root('div.anim-main_list tr:nth-child(3) a').text().strip()
    el_links = root('.cartoon_online_border li a')
    toc = []
    for i in range(len(el_links)):
        toc.append('http://manhua.dmzj.com' + el_links.eq(i).attr('href'))
    return {'title': fname_escape(title), 'author': fname_escape(author), 'toc': toc}
    
def get_article(html):
    root = pq(html)
    title = root('.hotrmtexth1 a').text().strip()
    ch = root('.display_middle span').text().strip()
    sc = root('script:not([src])').eq(0).html()
    if sc:
        pics = execjs.compile(sc).eval('arr_pages') 
        pics = list(map(lambda s: 'http://images.dmzj.com/' + s, pics))
    else: pics = None
    return {'title': fname_escape(title), 'ch': fname_escape(ch), 'pics': pics}
    
def safe_mkdir(dir):
    try: os.mkdir(dir)
    except: pass
    
def safe_rmdir(dir):
    try: shutil.rmtree(dir)
    except: pass
    
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
    
def process_img(img, l=4):
    img = np.frombuffer(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)
    
    h, w = img.shape
    if w > h: img = img.T[::-1]
    
    h, w = img.shape
    if w > 1000:
        rate = 1000 / w
        nh = round(h * rate)
        img = cv2.resize(img, (1000, nh), interpolation=cv2.INTER_CUBIC)
    
    
    img = grid(img)
    img = cv2.imencode('.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 9])[1]
    return bytes(img)
    
def download_ch(url, info):
    print(f'ch: {url}')
    html = request_retry('GET', url, headers=headers).text
    art = get_article(html)
    if not art['pics']:
        print('找不到页面')
        return
        
    name = f"{art['title']} - {info['author']} - {art['ch']}"
    ofname = f'out/{name}.epub'
    if name in existed or path.exists(ofname):
        print('文件已存在')
        return
    safe_mkdir('out')
    
    imgs = {}
    for i, img_url in enumerate(art['pics']):
        print(f'pic: {img_url}')
        img = request_retry('GET', img_url, headers=headers).content
        img = process_img(img)
        imgs[f'{i}.png'] = img
        
    co = '\r\n'.join([
        f"<p><img src='../Images/{i}.png' width='100%' /></p>"
        for i in range(len(imgs))
    ])
    articles = [{'title': f"{art['title']} - {art['ch']}", 'content': co}]
    gen_epub(articles, imgs, ofname)
    
    
def download(id):
    url = f'http://manhua.dmzj.com/{id}/'
    html = request_retry('GET', url, headers=headers).text
    info = get_info(html)
    print(info['title'], info['author'])
    
    if len(info['toc']) == 0:
        print('已下架')
        return
        
    for url in info['toc']:
        download_ch(url, info)
        
def main():
    cmd = sys.argv[1]
    arg = sys.argv[2]
    
    if cmd == 'download' or cmd == 'dl': download(arg)
    
if __name__ == '__main__': main()
