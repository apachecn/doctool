# coding: utf-8

import re
from googletrans import Translator
import time
import sys
import os
from bs4 import BeautifulSoup as bs
import urllib
import requests
import json
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--proxy')
parser.add_argument('--wait-sec', type=int, default=1)
args = parser.parse_args(sys.argv[2:])
if args.proxy:
    p = args.proxy
    args.proxy = {'http': p, 'https': p}

trans = Translator(['translate.google.cn'], proxies=args.proxy)

def google_trans_api_alter(src):
    url = 'http://translate.google.cn/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl=en&tl=zh-cn&q=' + urllib.parse.quote(src)
    res = requests.get(url, proxies=args.proxy).text
    j = json.loads(res)
    t = [s["trans"] for s in j["sentences"]]
    t = ''.join(t)
    return t


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
    
    # 移除 <pre>
    pres = []
    i = 0
    
    def replace_pre(m):
        nonlocal i
        s = m.group()
        pres.append(s)
        tag = f' [PRE{i}] '
        i += 1
        return tag
        
    html = re.sub(r'<pre[^>]*?>[\s\S]*?</pre>', replace_pre, html)
    
    # 移除 <code>
    codes = []
    i = 0
    
    def replace_code(m):
        nonlocal i
        s = m.group()
        codes.append(s)
        tag = f' [COD{i}] '
        i += 1
        return tag
        
    html = re.sub(r'<code[^>]*?>[^<]*?</code>', replace_code, html)
    
    # 移除其它标签
    tags = []
    i = 0
    
    def replace_tag(m):
        nonlocal i
        s = m.group()
        tags.append(s)
        tag = f' [HTG{i}] '
        i += 1
        return tag
        
    html = re.sub(r'<[^>]*?>', replace_tag, html)
    
    # 去掉 Unix 和 Windows 换行
    html = html.replace('\n', ' ')
    html = html.replace('\r', '')
    return html, codes, pres, tags

def tags_recover(html, codes, pres, tags):
    
    # 还原 <pre>
    for i, p in enumerate(pres):
        html = html.replace(f'[PRE{i}]', p)
    
    # 还原 <code>
    for i, c in enumerate(codes):
        html = html.replace(f'[COD{i}]', c)
        
    # 还原其余标签
    for i, t in enumerate(tags):
        html = html.replace(f'[HTG{i}]', t)
        
    return html

def trans_real(html):

    translated = False

    while not translated:
        try:
            print(html)
            html = trans.translate(html, dest='zh-cn', src='en').text
            # html = google_trans_api_alter(html)
            translated = True
            time.sleep(args.wait_sec)
        except Exception as ex:
            print(ex)
            time.sleep(args.wait_sec)
    
    # 修复占位符
    html = re.sub(r'\[\s*COD\s*(\d+)\s*\]', r'[COD\1]', html)
    html = re.sub(r'\[\s*HTG\s*(\d+)\s*\]', r'[HTG\1]', html)
    html = re.sub(r'\[\s*PRE\s*(\d+)\s*\]', r'[PRE\1]', html)
    return html

def trans_one(html):
    
    # 标签预处理
    html, codes, pres, tags = tags_preprocess(html)
    
    # 按句子翻译
    html = trans_real(html)
    
    # 标签还原
    html = tags_recover(html, codes, pres, tags)
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
