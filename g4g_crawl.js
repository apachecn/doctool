var request = require('sync-request')
var cheerio = require('cheerio')
var processImg = require('epub-crawler/src/img')
var fs = require('fs')
var req = require('epub-crawler/src/util').requestRetry

var selectors = {
    'title': 'article>h1',
    'content': 'article>.text',
    'remove': 'script, ins, iframe, p:empty, pre:empty, #personalNoteDiv, #practiceLinkDiv, div[id^=AP], .code-output-container, .textBasedMannualAds, ._ap_apex_ad, div>br',
    'tab': '.code-block',
    'code': 'td.code',
    'line': '.line',
    'link': '.articles-list .content .head a',
}

var artTemp = '<html><body>\n<h1>{title}</h1>\n{content}\n</body></html>'

function processTab($, $tab) {
	var $code = $tab.find(selectors.code).eq(0)
	var $newCode = $('<pre></pre>')
	var $lines = $code.find(selectors.line)
	var lines = []
	for (var i = 0; i < $lines.length; i++) {
		lines.push($lines.eq(i).text())
	}
	$newCode.text(lines.join('\n'))
	$tab.replaceWith($newCode)
}

function getArticle(html, url) {
    var $ = cheerio.load(html)
    if (selectors.remove)
        $(selectors.remove).remove()
    
    var $tabs = $(selectors.tab)
    for(var i = 0; i < $tabs.length; i++) {
        var $tab = $tabs.eq(i)
        processTab($, $tab)
    }
    
    var title = '<h1>' + 
        $(selectors.title).eq(0).text().trim() + '</h1>'
    var co = $(selectors.content).html()
    co = `<blockquote>原文：<a href='${url}'>${url}</a></blockquote>${co}`
    
    return {title: title, content: co}
}

function load_exist() {
	var fname = 'g4g_exist.json'
	if (!fs.existsSync(fname))
		return new Set()
	var li = JSON.parse(fs.readFileSync(fname, 'utf-8'))
	console.log(`load ${li.length} existed`)
	return new Set(li)
}

function download(id, dir='out') {
    console.log(id)
    if (fs.existsSync(`${dir}/${id}.html`))
        return
	var exi = load_exist()
	if (exi.has(id)) return
    var url = `https://www.geeksforgeeks.org/${id}/`
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
    var exi = load_exist()
    
    var ofile = fs.openSync(fname, 'a')
    for (var i = st; i <= ed; i++) {
        console.log(`page: ${i}`)
        var url = `https://www.geeksforgeeks.org/category/${cate}/page/${i}/`
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
