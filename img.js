var fs = require('fs');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
var request = require('sync-request');
var crypto = require('crypto');
var cheerio = require('cheerio');
var path = require('path')

//var headers = {'Referer': 'https://blog.csdn.net/red_stone1/article/details/77278707'}
var headers = {}
var imgs = new Set();

var isDir = s => fs.statSync(s).isDirectory()

function mkdirSyncSafe(dir) {
    try {fs.mkdirSync(dir)} catch(ex) {}
}

function main() {
    
    var fname = process.argv[2];
    if(!fname)
    {
        console.log('请指定文件或目录。');
        process.exit(0);
    }
    
    if(isDir(fname)) {
        mkdirSyncSafe(path.join(fname, 'img'))
        processDir(fname)
    } else {
        var dir = path.dirname(fname)
        mkdirSyncSafe(path.join(dir, 'img'))
        processFile(fname)
    }
}

function processDir(dir) {
    var files = fs.readdirSync(dir);
    for(var fname of files) {
        fname = path.join(dir, fname)
        processFile(fname)
    }
}

function processFile(fname) {
    if(!fname.endsWith('.html'))
        return;
    console.log('file: ' + fname);
    var dir = path.dirname(fname)
    var content = fs.readFileSync(fname, 'utf-8');
    content = processHtml(content, dir);
    fs.writeFileSync(fname, content);
}

function processHtml(html, dir) {
    
    var $ = cheerio.load(html);
    
    var $imgs = $('img');
    
    for(var i = 0; i < $imgs.length; i++) {
        
        try {
            var $img = $imgs.eq(i);
            var url = $img.attr('src');
            if(!url.startsWith('http'))
                continue;
            
            var picname = crypto.createHash('md5').update(url).digest('hex') + ".jpg";
            console.log(picname)
            
            if(!imgs.has(picname)) {
                var data = request('GET', url, {headers: headers}).getBody();
                fs.writeFileSync(path.join(dir, 'img', picname), data);
                imgs.add(picname);
            }
            
            $img.attr('src', 'img/' + picname);
        } catch(ex) {console.log(ex.toString())}
    }
    
    return $.html();
}

if(module == require.main) main();