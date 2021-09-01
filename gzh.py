import requests
import json
import os
import sys
import time
import re
from datetime import datetime
import subprocess as subp
import uuid

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
}

def parse_kv(text):
    res = {}
    for kv in text.split('&'):
        pos = kv.find('=')
        if pos == -1: continue
        res[kv[:pos]] = kv[pos+1:]
    return res

def main():
    param = parse_kv(sys.argv[1])
    start = sys.argv[2] if len(sys.argv) > 2 else None
    end = sys.argv[3] if len(sys.argv) > 3 else None
    biz = param.get('__biz', '')
    uin = param.get('uin', '')
    key = param.get('key', '')
    pass_ticket = param.get('pass_ticket', '')
    appmsg_token = param.get('appmsg_token', '')
    
    url = f'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={biz}&uin={uin}&key={key}&devicetype=Windows+Server+2016+x64&version=63030532&lang=zh_CN&a8scene=7&pass_ticket={pass_ticket}&fontgear=2'
    html = requests.get(url, headers=headers).text
    m = re.search(r'nickname = "(.+?)"', html)
    if not m:
        print('名称获取失败')
        return
    name = m.group(1)
    print(name)
    
    urls = []
    wait = 10
    i = 0
    stop = False
    while not stop:
        print(f'page: {i // 10 + 1}')
        url = f'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz={biz}&f=json&offset={i}&count=10&is_ok=1&scene=&uin={uin}&key={key}&pass_ticket={pass_ticket}&wxtoken=&appmsg_token={appmsg_token}&x5=0&f=json'
        j = requests.get(url, headers=headers).json()
        if j['ret'] != 0:
            print(j['errmsg'])
            time.sleep(wait)
            wait += 10
            continue
        if not j['can_msg_continue']:
            break
        li = json.loads(j['general_msg_list'])
        for it in li['list']:
            dt = datetime \
                .utcfromtimestamp(it['comm_msg_info']['datetime']) \
                .strftime('%Y%m%d')
            if start and dt < start:
                stop = True
                break
            if end and dt > end:
                continue
            url = it['app_msg_ext_info']['content_url']
            if not url: continue
            print(url)
            urls.append(url)
        wait = 10
        i += 10
    
    config = {
        "name": f"{name} {start}-{end}",
        "url": "https://mp.weixin.qq.com",
        "title": "#activity-name",
        "content": "#js_content",
        "optiMode": "thres",
        "list": urls,
    }
    config_fname = f'config_{uuid.uuid4().hex}.json'
    open(config_fname, 'w', encoding='utf-8').write(json.dumps(config))
    subp.Popen(f'crawl-epub {config_fname}', shell=True).communicate()
    os.remove(config_fname)
    print('done...')
    
if __name__ == '__main__': main()
