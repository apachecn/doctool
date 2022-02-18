from pyquery import PyQuery as pq
import sys
import os
from os import path
import re
from pyquery import PyQuery as pq

def process_pre(el_pre, root):
    el_lines = el_pre.find('.FixedLine')
    lines = []
    for i in range(len(el_lines)):
        el_line = el_lines.eq(i)
        lines.append(el_line.html())
    el_new_pre = root('<pre></pre>')
    code = re.sub(r'<[^>]*>', '', '\n'.join(lines))
    code = re.sub(r'^\x20+', '', code, flags= re.M)
    el_new_pre.html(code)
    el_pre.replace_with(el_new_pre)

def process_para(el_para, root):
    el_new_para = root('<p></p>')
    el_new_para.html(el_para.html())
    el_para.replace_with(el_new_para)

def process_file(fname):
    print(fname)
    if not fname.endswith('.html'):
        return
    html = open(fname, encoding='utf-8').read()
    html = html.replace('<?xml version="1.0" encoding="utf-8"?>', '')
    html = re.sub(r'xmlns=".+?"', '', html)
    html = re.sub(r'xmlns:epub=".+?"', '', html)
    root = pq(html)
    
    el_pres = root('.ProgramCode')
    for i in range(len(el_pres)):
        el_pre = el_pres.eq(i)
        el_new_pre = root('<pre></pre>')
        code = re.sub(r'<[^>]*>', '', el_pre.html())
        code = re.sub(r'^\x20+', '', code, flags=re.M)
        code = code.replace('\xa0', '\x20')
        el_new_pre.html(code)
        el_pre.replace_with(el_new_pre)
    
    el_codes = root('.EmphasisFontCategoryNonProportional, .FontName2')
    for i in range(len(el_codes)):
        el_code = el_codes.eq(i)
        el_new_code = root('<code></code>')
        el_new_code.text(el_code.text())
        el_code.replace_with(el_new_code)
        
    el_paras = root('div.Para')
    print(len(el_paras))
    for i in range(len(el_paras)):
        process_para(el_paras.eq(i), root)
        
    el_lis = root('.UnorderedList, .OrderedList, pre, .Figure, .Table')
    print(len(el_lis))
    for i in range(len(el_lis)):
        el_li = el_lis.eq(i)
        el_li_parent = el_li.parent()
        if not el_li_parent.is_('p, div.Para'):
            continue
        el_li.remove()
        el_li_parent.after(el_li)
        
    el_paras = root('.CaptionNumber, .MediaObject')
    print(len(el_paras))
    for i in range(len(el_paras)):
        process_para(el_paras.eq(i), root)
    
    root('.ChapterContextInformation, .AuthorGroup, .ItemNumber').remove()
    
    html = str(root)
    html = re.sub(r'</?(div|span|article|header|section|figure|figcaption)[^>]*>', '', html)
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