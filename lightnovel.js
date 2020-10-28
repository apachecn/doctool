var request = require('sync-request')
var cheerio = require('cheerio')
var iconv = require('iconv-lite')
var genEpub = require('gen-epub')
var fs = require('fs')
var chp = require('child_process')
var {URL} = require('url')

var dtMap = loadDtMap()

var cookie = process.env['WK8_COOKIE'] || ''

function sleep(s) {
    chp.spawnSync('sleep', [s])
}

function loadDtMap() {
    
    if(!fs.existsSync('dt.txt'))
        return {}
    
    var lines = fs.readFileSync('dt.txt', 'utf-8')
                  .split('\n')
                  .map(x => x.trim())
                  .filter(x => x)
    
    var dtMap = {}
    lines.map(x => x.split(' '))
         .filter(x => x.length >= 2)
         .forEach(x => dtMap[x[0]] = x[1])
    
    return dtMap
}

function fnameEscape(name){
    
    return name.replace(/\\/g, '＼')
               .replace(/\//g, '／')
               .replace(/:/g, '：')
               .replace(/\*/g, '＊')
               .replace(/\?/g, '？')
               .replace(/"/g, '＂')
               .replace(/</g, '＜')
               .replace(/>/g, '＞')
               .replace(/\|/g, '｜')
               
}

function requestRetry(method, url, options={}) {
    
    var retry = options.retry || 5
    
    for(var i = 0; i < retry; i++) {
        try {
            return request(method, url, options)
        } catch(ex) { 
            if(i == retry - 1) throw ex;
        }
    }
}

function formatText(text) {
    
    return text.replace(/(\r\n)+/g, '\r\n')     // 多个换行变为一个
               .replace(/^.+?\r\n.+?\r\n/, '')  // 去掉前两行
               .replace(/\r\n.+?\r\n.+?$/, '')  // 去掉后两行
               .replace(/^(.+?)$/gm, s => {     // 划分标题和段落
                   if(s.startsWith('    '))
                       return '<p>' + s.slice(4) + '</p>'
                   else
                       return '<!--split--><h1>' + s + '</h1>'
               })
               .split('<!--split-->')           // 拆分章节
               .filter(x => x)                  // 过滤空白章节
               .map(x => {
                   // 将章节拆分为标题和内容
                   var title = /<h1>(.+?)<\/h1>/.exec(x)[1]
                   var co = x.replace(/<h1>.+?<\/h1>/, '')
                   return {title: title, content: co}
               })
    
}

function getInfo(html) {
    
    var $ = cheerio.load(html)
    var dt = $('#content > div:nth-child(1) > table:nth-child(1) tr:nth-child(2) > td:nth-child(4)').text().slice(5).replace(/-/g, '')
    var url = $('#content > div:nth-child(1) > div:nth-child(6) > div > span:nth-child(1) > fieldset > div > a').attr('href')
    var title = $('#content > div:nth-child(1) > table:nth-child(1) tr:nth-child(1) > td > table tr > td:nth-child(1) > span > b').text()
    var author = $('#content > div:nth-child(1) > table:nth-child(1) tr:nth-child(2) > td:nth-child(2)').text().slice(5)
    return {dt: dt, url: url, title: fnameEscape(title), author: fnameEscape(author)}
    
}

function download(id) {
    
    if(id == null) {
        console.log('invalid id')
        return
    }
    
    var url = `https://www.wenku8.net/book/${id}.htm`
    var html = iconv.decode(requestRetry('GET', url).body, 'gbk')
    var info = getInfo(html)
    var dt = info.dt || dtMap[id] || 'UNKNOWN';
    console.log(info.title, info.author, dt)
        
    try {fs.mkdirSync('out')} catch(ex) {}
    var path = `out/${info.title} - ${info.author} - ${dt}.epub`
    if(fs.existsSync(path)) {
        console.log(`文件已存在`)
        return
    }
    
    var articles = []
    articles.push({title: info.title, content: `<p>作者：${info.author}</p>`})
    
    url = `http://dl.wenku8.com/down.php?type=utf8&id=${id}`
    var text = requestRetry('GET', url).body.toString()
    var chs = formatText(text)
    articles = articles.concat(chs)
    genEpub(articles, new Map(), null, path)
}

function getToc(html) {
    
    var $ = cheerio.load(html)
    var $links = $('table.grid b a')
    var $dts = $('table.grid div > div:nth-child(2) > p:nth-child(3)')
    var res = []
    for(var j = 0; j < $links.length; j++) {
        var id = /\/(\d+)\.htm/.exec($links.eq(j).attr('href'))[1]
        var dt = $dts.eq(j).text().slice(5).replace(/-/g, '')
        res.push({id: id, dt: dt})
    }
    return res

}

function fetch(fname, st, ed, withDt=false) {
    
    var ofile = fs.openSync(fname, 'a')
    
    outer:
    for(var i = 1; ; i++) {
        console.log(i)
        var url = `https://www.wenku8.net/modules/article/index.php?page=${i}`
        var html = iconv.decode(requestRetry('GET', url, {headers: {Cookie: cookie}}).body, 'gbk')
        var toc = getToc(html)
        if(toc.length == 0) break;
        for(var bk of toc) {
            if(ed && bk.dt > ed)
                continue;
            if(st && bk.dt < st)
                break outer;

            console.log(bk.id, bk.dt)
            if(withDt)
                fs.writeSync(ofile, `${bk.id} ${bk.dt}`)
            else
                fs.writeSync(ofile, bk.id)
            fs.writeSync(ofile, '\r\n')
        }
    }
    
    fs.closeSync(ofile)
    
}

function batch(fname) {
    var li = fs.readFileSync(fname, 'utf-8')
        .split('\n').map(x => x.trim()).filter(x => x)
    for(var id of li) download(id.split(' ')[0])
}

function main() {
    var cmd = process.argv[2]
    var arg = process.argv[3]
    if(cmd == 'fetch') fetch(arg, process.argv[4], process.argv[5])
    else if(cmd == 'batch') batch(arg)
    else if(cmd == 'dl' || cmd == 'download') download(arg)
    else if(cmd == 'fetchdt') fetch(arg, process.argv[4], process.argv[5], true)
}

if(require.main == module) main()
