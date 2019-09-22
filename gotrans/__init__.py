import execjs
import requests
import re
import os
import json
from urllib.parse import quote

fname = 'gotk.js'
js = None
proxy = None
tkk = None

def d(s):
    return os.path.join(os.path.dirname(__file__), s)

def load_js():    
    global js
    js = open(d(fname)).read()
    js = execjs.compile(js)

def get_tk(s, tkk=None):
    if not tkk: tkk = get_tkk()
    return js.call('tk', s, tkk)
    
def get_tkk():
    global tkk
    if not tkk: 
        res = requests.get('https://translate.google.cn/', proxies=proxy).text
        tkk = re.search(r"tkk:'(\d+\.\d+)", res).group(1)
    return tkk

def trans(s, dst='zh-CN', src='en'):
    tk = get_tk(s)
    url = 'https://translate.google.cn/translate_a/single?' + \
          f'client=webapp&sl={src}&tl={dst}&dt=t&tk={tk}' + \
          f'&q={quote(s)}'
    res = requests.get(url, proxies=proxy).text
    j = json.loads(res)
    trans = ' '.join([o[0] for o in j[0]])
    return trans


load_js()