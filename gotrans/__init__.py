import requests
import re
import os
import json
from urllib.parse import quote
import sys

proxy = None
tkk = None

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
}

def _shr32(x, bits):
    if bits <= 0:
        return x

    if bits >= 32:
        return 0

    x_bin = bin(x)[2:]
    x_bin_length = len(x_bin)

    if x_bin_length > 32:
        x_bin = x_bin[x_bin_length - 32: x_bin_length]

    if x_bin_length < 32:
        x_bin = x_bin.zfill(32)

    return int(x_bin[:32 - bits].zfill(32), 2)

def _rl(a, b):
    for c in range(0, len(b) - 2, 3):
        d = b[c + 2]

        if d >= 'a':
            d = ord(d[0]) - 87
        else:
            d = int(d)

        if b[c + 1] == '+':
            d = _shr32(a, d)
        else:
            d = a << d

        if b[c] == '+':
            a = a + d & (2 ** 32 - 1)
        else:
            a = a ^ d

    return a

def get_tk(a, tkk=None):
    if not tkk: tkk = get_tkk()
    tkk = tkk.split('.')
    
    b = int(tkk[0])
    d = []

    for f in range(0, len(a)):
        g = ord(a[f])

        if g < 128:
            d.append(g)
        else:
            if g < 2048:
                d.append(g >> 6 | 192)
            else:
                if ((g & 0xfc00) == 0xd800 and
                        f + 1 < len(a) and
                        (ord(a[f + 1]) & 0xfc00) == 0xdc00):

                    f += 1
                    g = 0x10000 + ((g & 0x3ff) << 10) + (ord(a[f]) & 0x3ff)

                    d.append(g >> 18 | 240)
                    d.append(g >> 12 & 63 | 128)
                else:
                    d.append(g >> 12 | 224)
                    d.append(g >> 6 & 63 | 128)

            d.append(g & 63 | 128)

    a = b

    for e in range(0, len(d)):
        a += d[e]
        a = _rl(a, "+-a^+6")

    a = _rl(a, "+-3^+b+-f")

    a = a ^ int(tkk[1])

    if a < 0:
        a = (a & (2 ** 31 - 1)) + 2 ** 31

    a %= 10 ** 6

    return f"{a}.{a ^ b}"
    
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
    res = requests.get(url, headers=headers, proxies=proxy).text
    j = json.loads(res)
    trans = ' '.join([o[0] for o in j[0]])
    return trans

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <word>")
        return 
    text = sys.argv[1]
    print(f"{text}: {get_tk(text)}")

if __name__ == '__main__': main()
