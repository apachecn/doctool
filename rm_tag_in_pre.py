from pyquery import PyQuery as pq
import sys
import os
from os import path
import re

def rep_func(m):
    code = m.group(1)
    code = re.sub(r'<[^>]*?>', '', code)
    code = re.sub(r'(\r?\n)+', r'\1', code)
    return f'<pre>{code}</pre>'

def process_file(fname):
    print(fname)
    if not fname.endswith('.html'):
        return
    html = open(fname, encoding='utf-8').read()
    html = html.replace('<?xml version="1.0" encoding="utf-8"?>', '')
    html = re.sub(r'<pre[^>]*>([\s\S]+?)</pre>', rep_func, html)
    open(fname, 'w', encoding='utf-8').write(html)
    
def process_dir(dname):
    fnames = os.listdir(dname)
    for f in fnames:
        f = path.join(dname, f)
        process_file(f)

def main():
    fname = sys.argv[1]
    if path.isfile(fname):
        process_file(fname)
    else:
        process_dir(fname)
        
if __name__ == '__main__': main()