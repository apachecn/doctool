import sys
import requests
from pyquery import PyQuery as pq
import json
import subprocess as subp
from os import path

crawler_config = {
    "name": "",
    "url": "http://www.woshipm.com/",
    "link": "",
    "title": "h2.article--title",
    "content": ".article--content",
    "remove": ".article--actions, .article-bottomAd, .pm-adTitle, .support-author",
    "optiMode": "thres",
    "list": []
}

def get_info(html):
    root = pq(html)
    el_pgnums = root('.nav-links .page-numbers:not(.dots):not(.prev):not(.next)')
    if len(el_pgnums) == 0:
        total = 1
    else:
        total = int(
            el_pgnums.eq(len(el_pgnums) - 1)
                .text().strip()
                .replace(',', '')
        )
    cate = root('title').text().split(' | ')[0]
    return {'total': total, 'cate': cate}
    
def get_dt_range(html):
    root = pq(html)
    el_times = root('time')
    return {
        'ed': el_times.eq(0).text().replace('-', ''),
        'st': el_times.eq(len(el_times) - 1).text(). replace('-', ''),
    }
    
def get_toc(html):
    root = pq(html)
    el_links = root('h2.post-title>a')
    el_times = root('time')
    return [
        {
            'link': el_links.eq(i).attr('href'),
            'dt': el_times.eq(i).text().replace('-', ''),
        } for i in range(len(el_links))
    ]
    
def get_first_pg(cate, dt, total):
    st = 1
    ed = total
    while st <= ed:
        mid = (st + ed) // 2
        url = f'http://www.woshipm.com/category/{cate}/page/{mid}'
        html = requests.get(url).text
        dt_range = get_dt_range(html)
        print(mid, dt_range)
        if dt >= dt_range['st'] and \
           dt <= dt_range['ed']:
            return mid
        elif dt < dt_range['st']:
            st = mid + 1
        else:
            ed = mid - 1
    
    return -1
    
def download(cate, stdt, eddt):
    config = crawler_config.copy()
    
    url = f'http://www.woshipm.com/category/{cate}'
    html = requests.get(url).text
    info = get_info(html)    
    print(info)
    cateName = info['cate']
    config['name'] = f'人人都是产品经理社区：{cateName}分类 {stdt}-{eddt}'
    if path.exists(config['name'] + '.epub'):
        print('已存在')
        return
    
    st = get_first_pg(cate, eddt, info['total'])
    stop = False
    for i in range(st, info['total'] + 1):
        if stop: break
        print(f'page: {i}')
        url = f'http://www.woshipm.com/category/{cate}/page/{i}'
        html = requests.get(url).text
        pgtoc = get_toc(html)
        if len(pgtoc) == 0: break
        for art in pgtoc:
            if art['dt'] > eddt: continue
            if art['dt'] < stdt:
                stop = True
                break
            print(art)
            config['list'].append(art['link'])
    
    fname = f'config_woshipm_{cate}_{stdt}_{eddt}.json'
    open(fname, 'w').write(json.dumps(config))
    subp.Popen(f'crawl-epub {fname}', shell=True).communicate()

def download_year(cate, year):
    is_leap = lambda year: \
        year % 4 == 0 and year % 100 != 0 or year % 400 == 0
    yr_map = {
        1: 31,
        2: 28 if not is_leap(int(year)) else 29,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }
    for mon, nd in yr_map.items():
        download(cate,  f'{year}{mon:02d}01', f'{year}{mon:02d}{nd:02d}')
    
def main():
    cmd = sys.argv[1]
    if cmd == 'dl':
        download(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'dlyr':
        download_year(sys.argv[2], sys.argv[3])
    
if __name__ == '__main__': main()
