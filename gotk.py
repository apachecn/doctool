import execjs
import requests
import re
import os

fname = 'gotk.js'

def d(s):
    return os.path.join(os.path.dirname(__file__), s)

js = open(d(fname)).read()
js = execjs.compile(js)

def tk(s, tkk=None):
    if not tkk: tkk = get_tkk()
    return js.call('tk', s, tkk)
    
def get_tkk():
    res = requests.get('https://translate.google.cn/').text
    return re.search(r"tkk:'(\d+\.\d+)", res).group(1)
