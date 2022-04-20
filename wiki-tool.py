import argparse
import requests
from readability import Document
import tempfile
import uuid
import subprocess as subp
import re
import os
import json
from os import path
from pyquery import PyQuery as pq
from datetime import datetime
from EpubCrawler.img import process_img
from EpubCrawler.util import safe_mkdir
from EpubCrawler.config import config

DIR = path.dirname(path.abspath(__file__))

default_hdrs = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
}

RE_CODE_BLOCK = r'\[code\][\s\S]+?\[/code\]'
RE_CODE_PRE = r'\[code\]\r?\n\x20*\r?\n'
RE_CODE_SUF = r'\r?\n\x20*\r?\n(\x20*)\[/code\]'

def d(name):
    return path.join(DIR, name)

def tomd(html):
    js_fname = d('tomd.js')
    html_fname = path.join(tempfile.gettempdir(), uuid.uuid4().hex + '.html')
    open(html_fname, 'w', encoding='utf8').write(html)
    subp.Popen(
        ["node", js_fname, html_fname],
        shell=True,
    ).communicate()
    md_fname = re.sub(r'\.html$', '', html_fname) + '.md'
    md = open(md_fname, encoding='utf8').read()
    os.remove(html_fname)
    return md

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

def code_replace_func(m):
    s = m.group()
    ind = re.search(RE_CODE_SUF, s).group(1)
    code = re.sub(RE_CODE_PRE, '', s)
    code = re.sub(RE_CODE_SUF, '', code)
    code = re.sub(r'(?<=\n)\x20{4}', '', code)
    code = re.sub(r'\A\x20{4}', '', code)
    return f'```\n{code}\n{ind}```'

def download_handle(args):
    html = requests.get(
        args.url,
        headers=default_hdrs,
    ).content.decode(args.encoding, 'ignore')
    
    # 解析标题
    rt = pq(html)
    el_title = rt.find('title').eq(0)
    title = el_title.text().strip()
    el_title.remove()
    
    # 判断是否重复
    title_esc = re.sub(r'\s', '-', fname_escape(title))
    fname = f'docs/{title_esc}.md'
    if path.isfile(fname):
        print(f'{title} 已存在')
        return
    
    # 解析内容并下载图片
    co = Document(str(rt)).summary()
    co = pq(co).find('body').html()
    imgs = {}
    co = process_img(co, imgs, img_prefix='img/', page_url=args.url)
    html = f'''
    <html><body>
    <h1>{title}</h1>
    <blockquote>
    来源：<a href='{args.url}'>{args.url}</a>
    </blockquote>
    {co}</body></html>
    '''
    
    # 转换 md
    md = tomd(html)
    # md = re.sub(RE_CODE_BLOCK, code_replace_func, md)
    yaml_head = '\n'.join([
        '<!--yml',
        'category: ' + args.category,
        'date: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '-->',
    ])
    md = f'{yaml_head}\n\n{md}'
    
    # 写入硬盘
    safe_mkdir('docs')
    safe_mkdir('docs/img')
    open(fname, 'w', encoding='utf-8').write(md)
    for name, data in imgs.items():
        open(f'docs/img/{name}', 'wb').write(data)
        
    print('已完成')
    
    
def main():
    parser = argparse.ArgumentParser(prog="BookerWikiTool", description="iBooker WIKI tool", formatter_class=argparse.RawDescriptionHelpFormatter)
    # parser.add_argument("-v", "--version", action="version", version=f"BookerWikiTool version: {__version__}")
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers()
    
    login_parser = subparsers.add_parser("download", help="download a page")
    login_parser.add_argument("url", help="url")
    login_parser.add_argument("-e", "--encoding", default='utf-8', help="encoding")
    login_parser.add_argument("-c", "--category", default='未分类', help="category")
    login_parser.set_defaults(func=download_handle)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__": main()