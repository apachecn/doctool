var cheerio = require('cheerio');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
var req = require('sync-request');
var fs = require('fs');

var config = JSON.parse(fs.readFileSync('config.json', 'utf-8'))

function main() {
    
    var ofile = fs.openSync(config.fname, 'a');
    var toc = getTocFromCfg()

    var start = 0;
    if(fs.existsSync('out.idx')) {
        start = fs.readFileSync('out.idx')
        start = Number.parseInt(start) + 1
    }

    for(var i = start; i< toc.length; i++) {
        try {
            var url = toc[i];
            console.log('page: ' + url);
            
            
            if(url.startsWith('http')) {
                html = request(url);
                var content = getContent(html, url);
                fs.writeSync(ofile, '\n<!--split-->\n');
                fs.writeSync(ofile, content);
            }
            else 
                fs.writeSync(ofile, `\n<!--split-->\n<h1>${url}</h1>`);
            
            fs.writeFileSync('out.idx', i.toString())
        } catch(ex) {
            console.log(ex);
            i--;
        }
    }

    fs.closeSync(ofile);
    console.log('Done..');
}

function getTocFromCfg() {
    
    if(config.list && config.list.length > 0)
        return config.list;
    
    if (!config.url) {
        console.log('请指定 URL')
        process.exit()
    }
    
    var html = request(config.url);
    var toc = getToc(html);
    return toc;
    
}

function getToc(html)  {
        
    var $ = cheerio.load(html);
    
    if(config.remove)
        $(config.remove).remove()
    
    var $list = $(config.link);

    var res = [];
    for(var i = 0; i < $list.length; i++)
    {
        var $link = $list.eq(i)
        var url = $link.attr('href');
        if(!url) {
            var text = $link.text()
            res.push(text)
            continue
        }
        if(!url.includes('#'))
            res.push(config.base + url)

    }
    return res;
}

function getContent(html, url) {
    if(config.processMath)
        html = processMath(html)
    if(config.processDecl)
        html = processDecl(html)
    
    var $ = cheerio.load(html);
    
    if(config.remove)
        $(config.remove).remove()
    
    var title = ''
    if(config.title)
        title = '<h1>' + $(config.title).text() + '</h1>'
        
    var co = $(config.content).html()
    var credit = `<blockquote>原文：<a href='${url}'>${url}</a></blockquote>`
    
    if(config.credit)
        return title + credit + co;
    else
        return title + co;
}

function request(url) {

    return req('GET', url, {headers: config.hdrs}).getBody().toString();

}

////////////////////////////////////////////////////

// for sphinx docs
function processDecl(html) {
    
    var $ = cheerio.load(html)
    $('colgroup').remove()
    
    var $dts = $('dt')
    
    for(var i = 0; i < $dts.length; i++) {
        var $dt = $dts.eq(i)
        $dt.find('a.reference').remove()
        var t = $dt.text()
        var $pre = $('<pre></pre>')
        $pre.text(t)
        $dt.replaceWith($pre)
    }
    
    return $.html()
}

function processMath(html){
    
    var $ = cheerio.load(html)
    
    var $maths = $('span.math, div.math');
    for(var i = 0; i < $maths.length; i++) {
        var $m = $maths.eq(i)
        var tex = $m.text().replace(/\\\[|\\\]|\\\(|\\\)/g, '')
        var url = 'http://latex.codecogs.com/gif.latex?' + encodeURIComponent(tex)
        var $img = $('<img />')
        $img.attr('src', url)
        if($m.is('div')) {
            var $p = $('<p></p>')
            $p.append($img)
            $img = $p
        }
        $m.replaceWith($img)
    }
    
    return $.html()
}

if(module == require.main) main()