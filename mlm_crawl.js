var request = require('sync-request')
var cheerio = require('cheerio')
var processImg = require('epub-crawler/src/img')
var fs = require('fs')
var req = require('epub-crawler/src/util').requestRetry

var selectors = {
    'title': 'h1.title',
    'content': 'section.entry',
    'remove': '.simplesocialbuttons, .widget_text, ins, script, .woo-sc-hr, center, .crp_related',
    'link': 'h2.title>a',
    'exiName': 'mlm_exist.json',
    'pageUrl': 'https://machinelearningmastery.com/{id}/',
    'tocUrl': 'https://machinelearningmastery.com/category/{cate}/page/{i}/',
    'block': '.urvanov-syntax-highlighter-syntax',
}

var artTemp = '<html><body>\n<h1>{title}</h1>\n{content}\n</body></html>'

function processCodeBlock($block, $) {
    var code = $block.find('textarea').eq(0).text()
    var $pre = $('<pre></pre>')
    $pre.text(code)
    $block.replaceWith($pre)
}

function getArticle(html, url) {
    var $ = cheerio.load(html)
    if (selectors.remove)
        $(selectors.remove).remove()
    
    var $blocks = $(selectors.block)
    for(var i = 0; i < $blocks.length; i++){
        processCodeBlock($blocks.eq(i), $)
    }
    
    var title = '<h1>' + 
        $(selectors.title).eq(0).text().trim() + '</h1>'
    var co = $(selectors.content).html()
    co = `<blockquote>原文：<a href='${url}'>${url}</a></blockquote>${co}`
    
    return {title: title, content: co}
}

function load_exist() {
    var fname = selectors.exiName
    if (!fs.existsSync(fname))
        return new Set()
    var li = JSON.parse(fs.readFileSync(fname, 'utf-8'))
    console.log(`load ${li.length} existed`)
    return new Set(li)
}

var exi = load_exist()

function download(id, dir='out') {
    console.log(id)
    if (fs.existsSync(`${dir}/${id}.html`))
        return
    if (exi.has(id)) return
    var url = selectors.pageUrl.replace('{id}', id)
    var html = req('GET', url).body.toString()
    var art = getArticle(html, url)
    var imgs = new Map()
    art.content = processImg(art.content, imgs, {
        'pageUrl': url,
        'imgPrefix': 'img/',
    })
    try {fs.mkdirSync(dir)} catch {}
    try {fs.mkdirSync(`${dir}/img`)} catch {}
    html = artTemp.replace('{title}', art.title)
               .replace('{content}', art.content)
    fs.writeFileSync(`${dir}/${id}.html`, html)
    for (var [name, img] of imgs.entries()) {
        fs.writeFileSync(`${dir}/img/${name}`, img)
    }

}

function batch(fname) {
    var dir = fname.replace(/\.\w+$/, '')
    var ids = fs.readFileSync(fname, 'utf-8')
                .split('\n')
                .map(x => x.trim())
                .filter(x => x)
    for (var id of ids) 
        download(id, dir)
}

function getIds(html) {
    var $ = cheerio.load(html)
    var $links = $(selectors.link)
    var res = []
    for (var i = 0; i < $links.length; i++) {
        var url = $links.eq(i).attr('href')
        if (!url) continue
        res.push(url.split('/').slice(-2)[0])
    }
    return res
}

function fetch(fname, cate, st, ed) {
    st = st || 1
    ed = ed || 1000000
    
    var ofile = fs.openSync(fname, 'a')
    for (var i = st; i <= ed; i++) {
        console.log(`page: ${i}`)
        var url = selectors.tocUrl
            .replace('{cate}', cate)
            .replace('{i}', i)
        var html = req('GET', url).body.toString()
        var ids = getIds(html)
        if (ids.length == 0) break
        fs.writeSync(ofile, `page: ${i}\n`)
        ids = ids.filter(x => !exi.has(x))
        for (var id of ids)
            fs.writeSync(ofile, id + '\n')
    }
    
}

function main() {
    
    var cmd = process.argv[2]
    if (cmd == 'download')
        download(process.argv[3])
    else if (cmd == 'batch')
        batch(process.argv[3])
    else if (cmd == 'fetch')
        fetch(...process.argv.slice(3, 7))
}

if (require.main === module) main()
