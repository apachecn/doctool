/*
apt update -y
apt install -y libgl1
npm install sync-request
npm install cheerio
npm install gen-epub -g
npm install epub-crawler -g
pip install imgyaso
wget https://raw.githubusercontent.com/apachecn/doctool/master/util.js
*/

var fs = require('fs')
var cheerio = require('cheerio')
var genEpub = require('gen-epub')
var os = require('os')
var path = require('path')
var processImg = require('epub-crawler/src/img')
var request = require('./util.js').requestRetry

function getBody(html) {
    return cheerio.load(html)('body').html()
}

function getToc(id, headers) {
    var res = []
	for (var i = 1; ; i++) {
		var url = 'https://www.kaggle.com/requests/KernelsService/ListKernels'
		var param = {"kernelFilterCriteria":{"search":"","listRequest":{"competitionId":id,"userId":null,"sortBy":"hotness","pageSize":100,"group":"everyone","outputType":null,"page":i,"datasetId":null,"datasourceType":null,"forkParentScriptId":null,"kernelType":null,"language":null,"tagIds":"","excludeResultsFilesOutputs":false,"wantOutputFiles":false,"after":null,"hasGpuRun":null,"privacy":null}},"detailFilterCriteria":{"deletedAccessBehavior":"returnNothing","unauthorizedAccessBehavior":"returnNothing","excludeResultsFilesOutputs":false,"wantOutputFiles":false,"gcsTimeoutMs":null,"kernelIds":[],"maxOutputFilesPerKernel":null,"outputFileTypes":[],"readMask":null}}
		var jstr = request('POST', url, {json: param, headers: headers})
			.body.toString()
		var j = JSON.parse(jstr)
		if (j['result']['kernels'].length == 0)
			break
		for (var it of j['result']['kernels']) {
			it.url = 'https://www.kaggle.com' + it.scriptUrl
			res.push(it)
		}
	}
	console.log(`Total: ${res.length}`)
    return res
}

function compToId(html) {
    var id = /kaggle\/(\d+)/.exec(html)[1]
    return id
}

function getCookiesAndId(name) {
	var url = `https://www.kaggle.com/c/${name}/code`
	var r = request('GET', url)
	var cookies = {}
	for(var kv of r.headers['set-cookie']) {
		kv = kv.split('; ')[0].split('=')
		if(kv.length < 2) continue
		cookies[kv[0]] = kv[1]
	}
	var id = compToId(r.body.toString())
	return [cookies, id]
}

function download(name) {
    console.log(`name: ${name}`)
	var [cookies, id] = getCookiesAndId(name)
	console.log('Cookies:', cookies)
	console.log(`id: ${id}`)
	var cookieStr = Object.entries(cookies)
		.map(x => x[0] + '=' + x[1]).join('; ')
	var headers = {
		'Cookie': cookieStr,
		'x-xsrf-token': cookies['XSRF-TOKEN'],
	}
	var toc = getToc(id, headers)
    var articles = [{title: `Kaggle Kernel - ${name}`, content: ''}]
    var imgs = new Map()
    for(var it of toc) {
		console.log(it.url)
        var html = request('GET', it.url).body.toString()
		var realUrl = /"renderedOutputUrl":"(.+?)"/.exec(html)[1]
		html = request('GET', realUrl).body.toString()
		var co = cheerio.load(html)('#notebook-container').toString()
		co = processImg(co, imgs, {
			pageUrl: realUrl,
			imgPrefix: '../Images/',
		})
        var from = `<p>From: <a href='${it.url}'>${it.url}</a></p>`
		var prefix = 'https://www.kaggle.com'
        var au = `<p>Author: <a href='${prefix + it.author.profileUrl}'>${it.author.displayName}</a></p>`
        co = `${from}\n${au}\n${co}`
        articles.push({title: it.title, content: co})
    }
    genEpub(articles, imgs)
}

function main() {
    var names = process.argv[2].split(':')
    for(var name of names)
        download(name)
}

if(module == require.main) main()
