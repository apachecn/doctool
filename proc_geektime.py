import os
from os import path
import sys
import re
from pyquery import PyQuery as pq
from concurrent.futures import ThreadPoolExecutor
from GenEpub import gen_epub
from EpubCrawler.img import process_img

def repl_pre(m):
    s = m.group(0)
    rt = pq(s)
    rt('.richcontent-pre-copy, .hljs-ln-numbers').remove()
    s = rt.__str__().replace(' ', '&nbsp;')
    s = re.sub(r'</?(table|thead|tbody|tr|th|td)[^>]*>', '', s)
    return s
    
def repl_div_pre(m):
    s = m.group(0)
    s = re.sub(r'</?(div|span)[^>]*>', '', s)
    s = re.sub(r'^\s*<br/>', '', s)
    return f'<pre>{s}</pre>'
    

def get_article(html):
    html = proc_html(html)
    rt = pq(html)
    '''
    for el in pq('img'):
        el = pq(el)
        el.attr('src', el.attr('data-savepage-src'))
    '''
    title = rt('h1').eq(0).text().strip()
    style = '\n'.join([
        pq(el).html()
        for el in rt('style')
    ])
    rt('style').remove()
    cont = rt('[data-slate-editor="true"], ._29HP61GA_0').eq(0).html()
    return {
        'title': title,
        # 'content': f'<style>{style}</style>\n{cont}',
        'content': cont,
    }
    
    

def main():
    dir = sys.argv[1]
    fnames = [f for f in os.listdir(dir) if f.endswith('.html')]
    
    group = {}
    for f in fnames:
        m = re.search(r'^(\d+)', f)
        if not m: continue
        no = int(m.group(1))
        group.setdefault(no, [])
        group[no].append(f)
        
    pool = ThreadPoolExecutor(16)
    hdls = []
    for no, fnames in group.items():
        h = pool.submit(tr_proc_book, dir, fnames)
        hdls.append(h)
    for h in hdls: h.result()


def tr_proc_book(dir, fnames):
    title = fnames[0].split('：')[0]
    print(title)
    articles = [{
        'title': title,
        'content': '',
    }]
    imgs = {}
    for f in fnames:
        print(f)
        ff = path.join(dir, f)
        html = open(ff, encoding='utf8').read()
        art = get_article(html)
        articles.append(art)
        art['content'] = process_img(art['content'], imgs, img_prefix='../Images/')
    gen_epub(articles, imgs)


def proc_html(html):
    html = re.sub(r'<pre[^>]*>[\s\S]+?</pre>', repl_pre, html)
    html = re.sub(r'(?=<div[^>]*data-slate-type="code-line"[^>]*>)', '<br/>', html)
    html = re.sub(r'<div[^>]*data-slate-type="pre"[^>]*>[\s\S]+?</div>(?=<div[^>]*data-slate-type="[\w\-]+"[^>]*>)(?!<div[^>]*data-slate-type="code-line"[^>]*>)', repl_div_pre, html)

    rt = pq(html)
    
    el_paras = rt.find('[data-slate-type="paragraph"], [data-slate-type="image"]')
    for  el in el_paras:
        el = pq(el)
        elp = pq('<p></p>')
        elp.html(el.html())
        el.replace_with(elp)
    el_quotes = rt.find('[data-slate-type="block-quote"]')
    for  el in el_quotes:
        el = pq(el)
        elq = pq('<blockquote></blockquote>')
        elq.html(el.html())
        el.replace_with(elq)
    el_bolds = rt.find('[data-slate-type="bold"]')
    for  el in el_bolds:
        el = pq(el)
        elb = pq('<b></b>')
        elb.html(el.html())
        el.replace_with(elb)
    el_lists = rt.find('[data-slate-type="list"]')
    for  el in el_lists:
        el = pq(el)
        elol = pq('<ol></ol>')
        elol.html(el.html())
        el.replace_with(elol)
    el_llines = rt.find('[data-slate-type="list-line"]')
    for  el in el_llines:
        el = pq(el)
        elli = pq('<li></li>')
        elli.html(el.html())
        el.replace_with(elli)
    el_icodes = rt.find('[data-slate-type="code"]')
    for  el in el_icodes:
        el = pq(el)
        elcode = pq('<code></code>')
        elcode.text(el.text())
        el.replace_with(elcode)
    el_codes = rt.find('[data-slate-type="pre"]')
    for el in el_codes:
        el = pq(el)
        el_inner = el.find('[data-origin="pm_code_preview"]')
        if not el_inner: continue
        elpre = pq('<pre></pre>')
        elpre.html(el_inner.html().replace(' ', '&nbsp;'))
        el.replace_with(elpre)
    
    return str(rt)
    
if __name__ == '__main__': main()