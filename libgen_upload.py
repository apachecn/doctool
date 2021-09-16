import requests
import hashlib
import os
import sys
from os import path
from pyquery import PyQuery as pq
import re
from concurrent.futures import ThreadPoolExecutor
from EpubCrawler.util import request_retry

RE_INFO = r'\[(.+?)\]([^\[]+)'

urls = {
    'info': 'https://library.bz/{cate}/uploads/{md5}',
    'upload': 'https://library.bz/{cate}/upload/',
    'submit': 'https://library.bz/{cate}/uploads/new/{md5}',
}

    
default_hdrs = {
    'Authorization': 'Basic Z2VuZXNpczp1cGxvYWQ=',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
}

series = None

def calc_md5(bts):
    hash = hashlib.md5()
    hash.update(bts)
    return hash.hexdigest()

def proc_info(fname, info):
    hdlrs = {
        'lightnovel': proc_ln_info,
        'it-ebooks': proc_itebooks_info,
        'dmzj': proc_dmzj_info,
        'nhentai': proc_nh_info,
        'ixinzhi': proc_ixinzhi_info,
    }
    if series in hdlrs:
        hdlrs[series](fname, info)

def proc_itebooks_info(fname, info):
    title = path.basename(fname) \
        .replace('.epub', '') \
        .replace('.pdf', '')
    info['title'] = title
    m = re.search(r'\d{4}', fname)
    if m:
        year = m.group()
        info['year'] = year
        info['series'] = f'it-ebooks-{year}'
    else:
        info['series'] = 'it-ebooks-extra'
    info['authors'] = 'it-ebooks'
    info['publisher'] = 'iBooker it-ebooks'
    

def proc_ln_info(fname, info):
    ori_info = path.basename(fname) \
        .replace('.epub', '').split(' - ')
    info['authors'] = ori_info[1]
    info['edition'] = ori_info[2]
    info['year'] = ori_info[2][:-4]
    info['publisher'] = 'Wenku8.Net'
    
def proc_dmzj_info(fname, info):
    ori_info = path.basename(fname) \
        .replace('.epub', '').split(' - ')
    info['title'] = ori_info[0] + ' - ' + ori_info[1]
    info['authors'] = ori_info[2]
    info['publisher'] = 'DMZJ'
    
def proc_ixinzhi_info(fname, info):
    info['authors'] = 'ixinzhi'
    info['publisher'] = 'iBooker xinzhi'
    
def proc_nh_info(fname, info):
    rm = re.findall(RE_INFO, \
        path.basename(fname).replace('.epub', ''))
    if len(rm) == 0:
        info['authors'] = '未知'
    else:
        info['authors'] = rm[0][0]
    info['publisher'] = 'NHentai'
    

def get_info(html):
    root = pq(html)
    props = [
        'title',
        'authors',
        'language',
        'year',
        'publisher',
        'isbn',
        'cover',
        'edition',
        'series',
        'pages',
        'gb_id',
        'asin',
        'description',
    ]
    info = {p: root(f'input[name={p}]').val() for p in props}
    if not info.get('language'):
        info['language'] = 'Chinese'
    return info

def process_file(fname):
    print(fname)
    if not fname.endswith('.pdf') and \
       not fname.endswith('.epub'):
        print('请提供 EPUB 或 PDF')
        return
    md5 = calc_md5(open(fname, 'rb').read()).upper()
    print(f'md5: {md5}')
    
    url = urls['info'].replace('{md5}', md5)
    r = request_retry('GET', url, headers=default_hdrs, allow_redirects=False)
    if r.status_code != 404:
        print('已存在')
        return
        
    url = urls['upload']
    mimetype = 'application/pdf' if fname.endswith('.pdf') else 'application/epub+zip'
    files = {
        'file': (path.basename(fname), open(fname, 'rb'), mimetype)
    }
    r = request_retry('POST', url, files=files, headers=default_hdrs)
    if r.status_code != 200 and r.status_code != 301:
        print(f'上传失败：{r.status_code}')
        return
    
    url = urls['submit'].replace('{md5}', md5)
    r = request_retry('GET', url, headers=default_hdrs)
    if r.status_code != 200:
        print(f'获取信息失败：{r.status_code}')
        return
    info = get_info(r.text)
    proc_info(fname, info)
    print(info)
    r = request_retry('POST', url, data=info, headers=default_hdrs)
    if r.status_code != 200 and r.status_code != 301:
        print(f'编辑信息失败：{r.status_code}')
        return
    print('上传成功！')
    
def process_file_safe(fname):
    try:
        process_file(fname)
    except Exception as ex:
        print(ex)
    
def process_dir(dir):
    pool = ThreadPoolExecutor(1)
    hdlrs = []
    files = os.listdir(dir)
    for f in files:
        f = path.join(dir, f)
        hdlrs.append(pool.submit(process_file_safe, f))
    for h in hdlrs:
        h.result()
    
def main():
    global series
    series = sys.argv[1]
    fname = sys.argv[2]
    cate = series
    if series in ['lightnovel', 'dmzj', 'nhentai']:
        cate = 'fiction'
    elif series in ['it-ebooks', 'ixinzhi']:
        cate = 'main'
    for k, v in urls.items():
        urls[k] = v.replace('{cate}', cate)
    if path.isdir(fname):
        process_dir(fname)
    else:
        process_file(fname)
    
if __name__ == '__main__': main()
