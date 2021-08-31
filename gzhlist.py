import requests
import json
from urllib.parse import quote_plus
import os
import sys
import time

token = os.environ.get('WX_TOKEN', '')
cookie = os.environ.get('WX_COOKIE', '')

headers = {'Cookie': cookie}

def main():
    name = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    url = f'https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&begin=0&count=1&query={quote_plus(name)}&token={token}&lang=zh_CN&f=json&ajax=1'
    j = requests.get(url, headers=headers).json()
    fake_id = j['list'][0]['fakeid']
    
    ofile = open(f'wx_{name}.txt', 'a')
    wait = 10
    i = (start - 1) * 5
    while True:
        print(f'page: {i // 5 + 1}')
        url = f'https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&begin={i}&count=5&fakeid={fake_id}&type=9&query=&token={token}&lang=zh_CN&f=json&ajax=1'
        j = requests.get(url, headers=headers).json()
        print(j)
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
    
if __name__ == '__main__': main()
