from EpubCrawler.util import request_retry
import json
from urllib.parse import quote_plus
import os
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor
from pyquery import PyQuery as pq

cookie = os.environ.get('WX_COOKIE', '')

headers = {
    'Cookie': cookie,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
}

def gzh_list(name, start=1):
    url = f'https://mp.weixin.qq.com'
    r = request_retry('GET', url, headers=headers, allow_redirects=False)
    loc = r.headers.get('Location', '')
    m = re.search(r'token=(\d+)', loc)
    if not m:
        print('token 获取失败')
        return
    token = m.group(1)
    
    url = f'https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&begin=0&count=1&query={quote_plus(name)}&token={token}&lang=zh_CN&f=json&ajax=1'
    j = request_retry('GET', url, headers=headers).json()
    fake_id = j['list'][0]['fakeid']
    
    ofile = open(f'wx_{name}.txt', 'a')
    wait = 10
    i = (start - 1) * 5
    while True:
        print(f'page: {i // 5 + 1}')
        url = f'https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&begin={i}&count=5&fakeid={fake_id}&type=9&query=&token={token}&lang=zh_CN&f=json&ajax=1'
        j = request_retry('GET', url, headers=headers).json()
        if j['base_resp']['ret'] == 200013:
            time.sleep(wait)
            wait += 10
            continue
        if len(j['app_msg_list']) == 0:
            break
        for it in j['app_msg_list']:
            print(it['link'])
            ofile.write(it['link'] + '\n')
        wait = 10
        i += 5
    ofile.close()
    print('done...')
    
def parse_kv(text):
    res = {}
    for kv in text.split('&'):
        pos = kv.find('=')
        if pos == -1: continue
        res[kv[:pos]] = kv[pos+1:]
    return res

def gzh_list2(param, start=1):
    param = parse_kv(param)
    biz = param.get('__biz', '')
    uin = param.get('uin', '')
    key = param.get('key', '')
    pass_ticket = param.get('pass_ticket', '')
    appmsg_token = param.get('appmsg_token', '')
    
    url = f'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={biz}&uin={uin}&key={key}&devicetype=Windows+Server+2016+x64&version=63030532&lang=zh_CN&a8scene=7&pass_ticket={pass_ticket}&fontgear=2'
    html = request_retry('GET', url, headers=headers).text
    m = re.search(r'nickname = "(.+?)"', html)
    if not m:
        print('名称获取失败')
        return
    name = m.group(1)
    print(name)
    
    ofile = open(f'wx_{name}.txt', 'a')
    wait = 10
    i = (start - 1) * 10
    while True:
        print(f'page: {i // 10 + 1}')
        url = f'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz={biz}&f=json&offset={i}&count=10&is_ok=1&scene=&uin={uin}&key={key}&pass_ticket={pass_ticket}&wxtoken=&appmsg_token={appmsg_token}&x5=0&f=json'
        j = request_retry('GET', url, headers=headers).json()
        if j['ret'] != 0:
            print(j['errmsg'])
            time.sleep(wait)
            wait += 10
            continue
        if not j['can_msg_continue']:
            break
        li = json.loads(j['general_msg_list'])
        for it in li['list']:
            if 'app_msg_ext_info' not in it:
                continue
            url = it['app_msg_ext_info']['content_url']
            if not url: continue
            print(url)
            ofile.write(url + '\n')
        wait = 10
        i += 10
    
    ofile.close()
    print('done...')

def tr_get_title(url, d):
    try:
        html = request_retry('GET', url).text
        title = pq(html).find('#activity-name').text().strip()
        d[url] = title 
        print(f'url: {url}, title: {title}')
    except Exception as ex: print(ex)
    

def uniq(fname):
    line = open(fname, encoding='utf-8').read().split('\n')
    line = filter(None, map(lambda l: l.strip(), line))
    
    url_title_map = {}
    pool = ThreadPoolExecutor(5)
    hdls = []
    for url in line:
        print(url)
        hdl = pool.submit(tr_get_title, url, url_title_map)
        hdls.append(hdl)
    for h in hdls: h.result()    
    
    ofname = re.sub('\.\w+$', '', fname) + '-uniq.txt'
    ofile = open(ofname, 'w', encoding='utf-8')
    vis = set()
    for url in line:
        title = url_title_map.get(url, '')
        if not title or title in vis:
            continue
        ofile.write(url + '\n')
        vis.add(title)
    ofile.close()    
    print('done...')
    

def main():
    cmd = sys.argv[1]
    arg = sys.argv[2]
    if cmd == 'list':
        gzh_list(arg, int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    elif cmd == 'list2':
        gzh_list2(arg, int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    elif cmd == 'uniq':
        uniq(arg)
    
if __name__ == '__main__': main()
