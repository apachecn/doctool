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
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
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
    
    ofile = open(f'wx_{name}.txt', 'a')
    wait = 10
    i = (start - 1) * 10
    while True:
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
    
if __name__ == '__main__': main()
