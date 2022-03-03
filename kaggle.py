import sys
import re
from pyquery import PyQuery as pq
from EpubCrawler.util import request_retry
from EpubCrawler.img import process_img
from GenEpub import gen_epub
from concurrent.futures import ThreadPoolExecutor

pool = ThreadPoolExecutor(5)

def get_toc(id, pg, headers):
    url = 'https://www.kaggle.com/api/i/kernels.KernelsService/ListKernels'
    param = {"kernelFilterCriteria":{"search":"","listRequest":{"competitionId":id,"sortBy":"HOTNESS","pageSize":20,"group":"EVERYONE","page":pg,"tagIds":"","excludeResultsFilesOutputs":False,"wantOutputFiles":False}},"detailFilterCriteria":{"deletedAccessBehavior":"RETURN_NOTHING","unauthorizedAccessBehavior":"RETURN_NOTHING","excludeResultsFilesOutputs":False,"wantOutputFiles":False,"kernelIds":[],"outputFileTypes":[]}}
    r = request_retry('POST', url, json=param, headers=headers)
    j = r.json()
    if 'kernels' not in j: return []
    for it in j['kernels']:
        it['url'] = 'https://www.kaggle.com' + it['scriptUrl']
    return j['kernels']
    
def comp_to_id(html):
    return re.search(r'kaggle/(\d+)', html).group(1)
    
def get_cookie_and_id(name):
    url = f'https://www.kaggle.com/c/{name}/code'
    r = request_retry('GET', url)
    cookies = {}
    for kv in r.headers['Set-Cookie'].split(', '):
        kv = kv.split('; ')[0].split('=')
        if len(kv) < 2: continue
        cookies[kv[0]] = kv[1]
    id = comp_to_id(r.text)
    return [cookies, id]
    
def get_real_url(url):
    html = request_retry('GET', url).text
    return re.search(r'"renderedOutputUrl":"(.+?)"', html).group(1)
    
def download_one(it, art, imgs):
    try:
        real_url = get_real_url(it['url'])
        html = request_retry('GET', real_url).text
        root = pq(html)
        root.find('script').remove()
        co = root.find('#notebook-container').html()
        co = process_img(co, imgs, 
            page_url=real_url, img_prefix='../Images/')
        origin = f"<p>From: <a href='{it['url']}'>{it['url']}</a></p>"
        prefix = 'https://www.kaggle.com'
        au = f"<p>Author: <a href='{prefix + it['author']['profileUrl']}'>{it['author']['displayName']}</a></p>"
        co = f'{origin}\n{au}\n{co}'
        art.update({'title': it['title'], 'content': co})
    except Exception as ex:
        print(ex)
    
def download(name):
    print(f'name: {name}')
    cookies, id = get_cookie_and_id(name)
    print(f'cookies: {cookies}\nid: {id}')
    cookie_str = '; '.join([
        k + '=' + v for k, v in cookies.items()
    ])
    headers = {
        'Cookie': cookie_str,
        'x-xsrf-token': cookies.get('XSRF-TOKEN', ''),
    }
    i = 1
    while True:
        print(f'Page: {i}')
        toc = get_toc(id, i, headers)
        if len(toc) == 0: break
        articles = [{'title': f'Kaggle Kernel - {name} - Page{i}', 'content': ''}]
        imgs = {}
        hdls = []
        for it in toc:
            print(it['url'])
            art = {}
            articles.append(art)
            hdl = pool.submit(download_one, it, art, imgs)
            hdls.append(hdl)
        for h in hdls: h.result()
        articles = list(filter(None, articles))
        gen_epub(articles, imgs)
        i += 1

def main():
    names = sys.argv[1].split(':')
    for n in names: 
        try: download(n)
        except: pass
    
if __name__ == '__main__': main()
