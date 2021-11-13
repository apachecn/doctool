import sys
import re
from pyquery import PyQuery as pq
from EpubCrawler.util import request_retry
from EpubCrawler.img import process_img
from GenEpub import gen_epub
from concurrent.futures import ThreadPoolExecutor

pool = ThreadPoolExecutor(5)

def get_toc(id, headers):
    res = []
    i = 1
    while True:
        url = 'https://www.kaggle.com/requests/KernelsService/ListKernels'
        param = {"kernelFilterCriteria":{"search":"","listRequest":{"competitionId":id,"userId":None,"sortBy":"hotness","pageSize":100,"group":"everyone","outputType":None,"page":i,"datasetId":None,"datasourceType":None,"forkParentScriptId":None,"kernelType":None,"language":None,"tagIds":"","excludeResultsFilesOutputs":False,"wantOutputFiles":False,"after":None,"hasGpuRun":None,"privacy":None}},"detailFilterCriteria":{"deletedAccessBehavior":"returnNothing","unauthorizedAccessBehavior":"returnNothing","excludeResultsFilesOutputs":False,"wantOutputFiles":False,"gcsTimeoutMs":None,"kernelIds":[],"maxOutputFilesPerKernel":None,"outputFileTypes":[],"readMask":None}}
        j = request_retry('POST', url, json=param, headers=headers).json()
        if len(j['result']['kernels']) == 0:
            break
        for it in j['result']['kernels']:
            it['url'] = 'https://www.kaggle.com' + it['scriptUrl']
            res.append(it)
        i += 1
    print(f'Total: {len(res)}')
    return res
    
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
    
def download_one(it, art, imgs):
    try:
        html = request_retry('GET', it['url']).text
        real_url = re.search(r'"renderedOutputUrl":"(.+?)"', html).group(1)
        html = request_retry('GET', real_url).text
        co = pq(html).find('#notebook-container').html()
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
    toc = get_toc(id, headers)
    articles = [{'title': f'Kaggle Kernel - {name}', 'content': ''}]
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

def main():
    names = sys.argv[1].split(':')
    for n in names: download(n)
    
if __name__ == '__main__': main()