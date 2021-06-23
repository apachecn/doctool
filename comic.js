var request = require('sync-request')
var fs = require('fs')
var cheerio = require('cheerio')
var path = require('path')
var chp = require('child_process')
var genEpub = require('gen-epub')
var os = require('os')

var headers = {
    'Referer': 'http://manhua.dmzj.com/',
}

var d = fname => path.join(__dirname, fname)

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

function loadExisted() {
	var existed = []
	var fname = 'dmzj_existed.json'
	if (fs.existsSync(fname)) {
		existed = JSON.parse(fs.readFileSync(fname, 'utf-8'))
	}
	return new Set(existed)
}

var existed = loadExisted()

function getInfo(html) {
    
    var $ = cheerio.load(html)
    var title = $('.anim_title_text h1').text()
    var author = $('div.anim-main_list tr:nth-child(3) a').text().trim()
    
    var $links = $('.cartoon_online_border li a')
    var toc = []
    for(var i = 0; i < $links.length; i++) {
        var $link = $links.eq(i)
        toc.push('http://manhua.dmzj.com' + $link.attr('href'))
    }

    return {title: fnameEscape(title), author: author, toc: toc}
}


function getArticle(html) {
    var $ = cheerio.load(html)
    var title = $('.hotrmtexth1 a').text().trim()
    var ch = $('.display_middle span').text().trim()
    var sc = $('script:not([src])').eq(0).html()
    if(sc) {
        var pics = eval(sc + 'arr_pages')
            .map(s => 'http://images.dmzj.com/' + s)
    } else { var pics = null }
    return {
        title: fnameEscape(title),
        ch: fnameEscape(ch),
        pics: pics
    }
}

function safeMkdir(dir) {
    try { fs.mkdirSync(dir)}
    catch(ex) {}
}

function safeRmdir(dir) {
    try { fs.rmdirSync(dir)}
    catch(ex) {}
}

function procImg(img) {
    
    var fname = new Date().getTime().toString() + '.png';
    fname = path.join(os.tmpdir(), fname)
    fs.writeFileSync(fname, img)
    chp.spawnSync('python', [d('procimg4comic.py'), fname])
    img = fs.readFileSync(fname)
    fs.unlinkSync(fname)
    return img
}

function download(id) {
    
    if(!id) {
        console.log('请输入 ID')
        return
    }
    
    safeMkdir('out')
    
    var url = `http://manhua.dmzj.com/${id}/`
    var html = request('GET', url).body.toString()
    var info = getInfo(html)
    console.log(info.title, info.author)

    if(info.toc.length == 0) {
        console.log('已下架')
        return
    }
    
    for(var url of info.toc) {
        
        console.log(`ch: ${url}`)
        var html = request('GET', url).body.toString()
        var art = getArticle(html)
        if(!art.pics) {
            console.log('找不到页面')
            continue
        }
        
        var name = `${art.title} - ${info.author} - ${art.ch}`
        if (existed.has(name)) {
            console.log('文件已存在')
            continue
        }
        var p = `out/${name}.epub`
        if(fs.existsSync(p)) {
            console.log('文件已存在')
            continue
        }
        
        var imgs = new Map()

        for(var [i, picUrl] of art.pics.entries()) {
            console.log(`pic: ${picUrl}`)
            var img = request('GET', picUrl, {headers: headers}).body
            img = procImg(img)
            imgs.set(`${i}.png`, img)
        }
        
        co = Array.from(Array(art.pics.length).keys())
            .map(i => `<p><img src='../Images/${i}.png' width='100%' /></p>`)
            .join('\r\n')
        var articles = [{title: `${art.title} - ${art.ch}`, content: co}]
        genEpub(articles, imgs, null, p)
    }
    
}

function fetch(fname, st, ed) {
    
    var f = fs.openSync(fname, 'a')
    
    outer:
    for(var i = 1; ; i++) {
        
        console.log(i)
        var url = `http://sacg.dmzj.com/mh/index.php?c=category&m=doSearch&status=0&reader_group=0&zone=2304&initial=all&type=0&_order=t&p=${i}&callback=c`
        var res = request('GET', url).body.toString()
        var j = JSON.parse(res.slice(2, -2))
        if(!j.result) break
        for(var bk of j.result) {
            var id = bk.comic_url.slice(1, -1)
            var dt = bk.last_update_date.replace(/-/g, '')
            
            if(ed && dt > ed)
                continue
            if(st && dt < st)
                break outer
            
            console.log(id, dt)
            fs.writeSync(f, `${id}\r\n`)
        }
    }
    
    fs.closeSync(f)
}

function batch(fname) {
    var li = fs.readFileSync(fname, 'utf-8')
        .split('\n').map(x => x.trim()).filter(x => x)
    for(var id of li) download(id)
}

function pack(dir) {
    
    if(!fs.statSync(dir).isDirectory()) {
        console.log('请输入目录名')
        return
    }
    
    var dirInfo = path.parse(dir)
    var p = path.join(dirInfo.dir, dirInfo.base + '.epub')
    console.log(p)
    if(fs.existsSync(p)) {
        console.log('文件已存在')
        return
    }
    
    var files = fs.readdirSync(dir).filter(
        s => s.endsWith('.jpg') ||
             s.endsWith('.png') ||
             s.endsWith('.gif')
    )
    
    var imgs = new Map()
    
    for(var [i, f] of files.entries()) {
        console.log(f)
        f = path.join(dir, f)
        var img = fs.readFileSync(f)
        img = procImg(img)
        imgs.set(`${i}.png`, img)
    }
    
    co = Array.from(Array(files.length).keys())
        .map(i => `<p><img src='../Images/${i}.png' width='100%' /></p>`)
        .join('\r\n')
    var articles = [{title: dirInfo.base, content: co}]
    genEpub(articles, imgs, null, p)
}

function main() {
    
    var op = process.argv[2]
    var arg = process.argv[3]
    
    if(op == 'dl' || op == 'download')
        download(arg)
    else if(op == 'batch')
        batch(arg)
    else if(op == 'fetch')
        fetch(arg, process.argv[4], process.argv[5])
    else if(op == 'pack')
        pack(arg)
}

if(require.main == module) main()
