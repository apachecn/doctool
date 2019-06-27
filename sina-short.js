var fs = require('fs')
var request = require('sync-request')

var fname = process.argv[2]
var co = fs.readFileSync(fname, 'utf-8')
var re = /\[.*?\]\((.*?)\)/g
var re2 = /\[.*?\]\((.*?)\)/
var urls = {}

co = co.replace(re, s => {
    try {
        var rm = re2.exec(s)
        var url = rm[1]
        if(!url || url.indexOf('//t.cn/') != -1) return s
        console.log(url)
        
        if(!urls.hasOwnProperty(url)) {
            var resStr = request('GET', `http://api.t.sina.com.cn/short_url/shorten.json?source=3271760578&url_long=${encodeURIComponent(url)}`).getBody().toString()
            var j = JSON.parse(resStr)
            var sh = j[0].url_short
            urls[url] = sh
        }
        
        var sh = urls[url]
        console.log(sh)
        return s.split(url).join(sh)
        
    } catch(ex) {
        console.log(ex)
        return s
    }
    
})

co = co.replace(/\[(.+?)\]\(http:\/\/(t\.cn.+?)\)/g, '$1（$2）')

fs.writeFileSync(fname, co)
