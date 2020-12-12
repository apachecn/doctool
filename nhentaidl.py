import requests
from pyquery import PyQuery as pq
import os
import sys
from os import path
from imgyaso import grid
import shutil
import json
import subprocess as subp
import uuid
import tempfile
import numpy as np
import cv2
import re

# npm install -g gen-epub

RE_INFO = r'\[(.+?)\]\s*(.+?)\s*(?=\[|$)'

config = {
    'hdrs': {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    },
}

def load_existed():
    existed = []
    if path.exists('existed.json'):
        existed = json.loads(open('existed.json').read())
    return set([tuple(e) for e in existed])
    
existed = load_existed()

def check_exist(existed, name):
    rms = re.findall(RE_INFO, name)
    if len(rms) == 0: return False
    return tuple(rms[-1]) in existed

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

def safe_mkdir(dir):
    try:
        os.mkdir(dir)
    except:
        pass

def safe_rmdir(dir):
    try:
        shutil.rmtree(dir)
    except:
        pass
        
def get_info(html):
    root = pq(html)
    title = root('h2.title').eq(0).text().strip()
    tags = root('.tag>.name')
    tags = set((pq(t).text() for t in tags))
    imgs = root('.gallerythumb > img')
    imgs = [
        pq(i).attr('data-src')
            .replace('t.jpg', '.jpg')
            .replace('t.png', '.png')
            .replace('t.nhentai', 'i.nhentai')
        for i in imgs
    ]
    return {'title': fname_escape(title), 'imgs': imgs, 'tags': tags}

def process_img(img):
    img = np.frombuffer(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)
    
    h, w = img.shape
    if (w > h): img = img.T[::-1]
    
    h, w = img.shape
    if w > 1000:
        rate = 1000 / w
        nh = round(h * rate)
        img = cv2.resize(img, (1000, nh), interpolation=cv2.INTER_CUBIC)
    
    img = grid(img)
    img = cv2.imencode(
        '.png', img, 
        [cv2.IMWRITE_PNG_COMPRESSION, 9]
    )[1]
    return bytes(img)

def gen_epub(articles, imgs=None, name=None, out_path=None):   
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
    
    args = [
        'gen-epub',
        fname,
        '-i',
        img_dir,
    ]
    if name: args += ['-n', name]
    if out_path: args += ['-p', out_path]
    subp.Popen(
        args, shell=True, 
        stdout=subp.PIPE, 
        stderr=subp.PIPE
    ).communicate()
    safe_rmdir(dir)

def download(id):
    url = f'https://nhentai.net/g/{id}/'
    html = requests.get(url).text
    info = get_info(html)
    print(info['title'])
    
    if check_exist(existed, info['title']):
        print('已存在')
        return 
        
    ofname = f"out/{info['title']}.epub"
    if path.exists(ofname):
        print('已存在')
        return
    safe_mkdir('out')
    
    imgs = {}
    l = len(str(len(info['imgs'])))
    for i, img_url in enumerate(info['imgs']):
        fname = str(i).zfill(l) + '.png'
        print(f'{img_url} => {fname}')
        img = requests.get(img_url, headers=config['hdrs']).content
        img = process_img(img)
        imgs[fname] = img
            
    co = [
        f'<p><img src="../Images/{str(i).zfill(l)}.png" /></p>' 
        for i in range(len(info['imgs']))
    ]
    co = '\n'.join(co)
    articles = [{'title': info['title'], 'content': co}]
    gen_epub(articles, imgs, None, ofname)
    
def get_ids(html):
    root = pq(html)
    links = root('a.cover')
    ids = [
        pq(l).attr('href')[3:-1]
        for l in links
    ]
    return ids
    
def fetch(fname, cate="", st=None, ed=None):
    ofile = open(fname, 'w')
    st = st or 1
    ed = ed or 1_000_000
    
    for i in range(st, ed + 1):
        print(f'page: {i}')
        url = f'https://nhentai.net/{cate}/?page={i}'
        html = requests.get(url).text
        ids = get_ids(html)
        if len(ids) == 0: break
        for id in ids:
            ofile.write(id + '\n')
            
    ofile.close()
    
def batch(fname):
    ids = filter(None, open(fname).read().split('\n'))
    for id in ids:
        download(id)
        
def extract(fname):
    lines = open(fname, encoding='utf-8').read().split('\n')
    lines = filter(None, lines)
    res = []
    
    for l in lines:
        rms = re.findall(RE_LINE, l)
        if len(rms) == 0: continue
        res.append(rms[-1])
        
    open(fname + '.json', encoding='utf-8') \
        .write(json.dumps(res))
    
    
def main():
    op = sys.argv[1]
    if op in ['dl', 'download']:
        download(sys.argv[2])
    elif op == 'batch':
        batch(sys.argv[2])
    elif op == 'fetch':
        fetch(
            sys.argv[2], 
            sys.argv[3] if len(sys.argv) > 3 else "", 
            sys.argv[4] if len(sys.argv) > 4 else None,
            sys.argv[5] if len(sys.argv) > 5 else None,
        )
    elif op == 'extract':
        extract(sys.argv[2])

if __name__ == '__main__': main()
