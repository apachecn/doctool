# coding: utf-8

import re
from googletrans import Translator
import time
import sys
import os
from bs4 import BeautifulSoup as bs
import requests
import hashlib
import json
from urllib.parse import quote
from argparse import ArgumentParser

RE_CODE = r'<(pre|code)[^>]*?>[\s\S]*?</\1>'
RE_TAG = r'<[^>]*?>'
RE_ENTITY = r'&(\w+|#x?\d+);'

parser = ArgumentParser()
parser.add_argument('--proxy')
parser.add_argument('--wait-sec', type=float, default=0.5)
args = parser.parse_args(sys.argv[2:])
if args.proxy:
    p = args.proxy
    args.proxy = {'http': p, 'https': p}

trans = Translator(['translate.google.cn'], proxies=args.proxy)

def set_inner_html(elem, html):
    body = bs('<body>' + html + '</body>', 'lxml').body
    elem.clear()
    for ch in list(body.children):
        elem.append(ch)

def tags_preprocess(html):

    '''
    # 去头去尾
    html = html.replace("<?xml version='1.0' encoding='utf-8'?>", '')
    html = re.sub(r'<html[^>]*?>.*?<body[^>]*?>', '', html, flags=re.RegexFlag.DOTALL)
    html = re.sub(r'</body>.*?</html>', '', html, flags=re.RegexFlag.DOTALL)
    '''
    
    tags = []
    idx = 0
    
    def replace_func(m):
        nonlocal idx
        s = m.group()
        tags.append(s)
        tk = f' [HTG{idx}] '
        idx += 1
        return tk
        
    # 移除 <pre|code>
    html = re.sub(RE_CODE, replace_func, html)
    # 移除其它标签
    html = re.sub(RE_TAG, replace_func, html)
    # 移除实体
    html = re.sub(RE_ENTITY, replace_func, html)
    
    # 去掉 Unix 和 Windows 换行
    html = html.replace('\n', ' ')
    html = html.replace('\r', '')
    return html, tags

def tags_recover(html, tags):

    # 还原标签
    for i, t in enumerate(tags):
        html = html.replace(f'[HTG{i}]', t)
        
    return html

def trans_real(html):

    translated = False

    while not translated:
        try:
            print(html)
            html = trans.translate(html, dest='zh-cn', src='en').text
            # html = baidu_trans(html)
            translated = True
            time.sleep(args.wait_sec)
        except Exception as ex:
            print(ex)
            time.sleep(args.wait_sec)
    
    # 修复占位符
    html = re.sub(r'\[\s*(?:htg|HTG)\s*(\d+)\s*\]', r'[HTG\1]', html)
    return html

def trans_one(html):
    if html.strip() == '':
        return ''
    
    # 标签预处理
    html, tokens = tags_preprocess(html)
    
    # 按句子翻译
    html = trans_real(html)
    
    # 标签还原
    html = tags_recover(html, tokens)
    return html

def trans_html(html):
    root = bs(html, 'lxml')
    
    # 处理 <p> <h?>
    elems = root.select('p, h1, h2, h3, h4, h5, h6')
    for elem in elems:
        to_trans = elem.decode_contents()
        trans = trans_one(to_trans)
        set_inner_html(elem, trans)
        
    # 处理 <blockquote> <td> <th>
    elems = root.select('blockquote, td, th')
    for elem in elems:
        if elem.p: continue
        to_trans = elem.decode_contents()
        trans = trans_one(to_trans)
        set_inner_html(elem, trans)
    
    # 处理 <li>
    elems = root.select('li')
    for elem in elems:
        if elem.p: continue
        
        # 如果有子列表，就取下来
        sub_list = None
        if elem.ul: sub_list = elem.ul
        if elem.ol: sub_list = elem.ol
        if sub_list: sub_list.extract()
        
        to_trans = elem.decode_contents()
        trans = trans_one(to_trans)
        set_inner_html(elem, trans)
        
        # 将子列表还原
        if sub_list: elem.append(sub_list)
    
    return root.decode()

def process_code(html):
    root = bs(html, 'lxml')
    
    pres = root.select('div.code, div.Code')
    for p in pres:
        newp = bs('<pre></pre>', 'lxml').pre
        newp.append(p.text)
        p.replace_with(newp)
        
    codes = root.select('span.inline-code, span.CodeInline')
    for c in codes:
        newc = bs('<code></code>', 'lxml').code
        newc.append(c.text)
        c.replace_with(newc)
        
    return str(root)

is_html = lambda f: f.endswith('.html') or f.endswith('.htm')

def process_file(fname):
    if not is_html(fname):
        print(f'{fname} 不是 HTML 文件')
        return
    
    print(fname)
    html = open(fname, encoding='utf-8').read()
    html = process_code(html)
    html = trans_html(html)
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(html)

def process_dir(dir):
    files = [f for f in os.listdir(dir) if is_html(f)]
    for f in files:
        f = os.path.join(dir, f)
        process_file(f)

def main():
    # python trans.py <dir|file>
    
    fname = sys.argv[1]
    if os.path.isdir(fname):
        process_dir(fname)
    else:
        process_file(fname)
        
if __name__ == '__main__': main()
