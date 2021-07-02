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
		var url = 'https://www.kaggle.com/requests/ListKernelsRequest'
		var param = {"kernelFilterCriteria":{"competitionId":id,"userId":null,"sortBy":"hotness","pageSize":100,"group":"everyone","outputType":null,"startRow":0,"page":i,"datasetId":null,"datasourceType":null,"forkParentScriptId":null,"kernelType":null,"language":null,"tagIds":"","excludeResultsFilesOutputs":false,"wantOutputFiles":true,"search":"","after":null,"hasGpuRun":null,"privacy":null},"detailFilterCriteria":{"deletedAccessBehavior":"returnNothing","unauthorizedAccessBehavior":"returnNothing","excludeResultsFilesOutputs":false,"wantOutputFiles":true,"kernelIds":[],"maxOutputFilesPerKernel":null,"outputFileTypes":[],"selection":{}}}
		var jstr = request('POST', url, {json: param, headers: headers})
			.body.toString()
		var j = JSON.parse(jstr)
		if (j['result']['kernels'].length == 0)
			break
		for (var it of j['result']['kernels'])
			res.push(it)
	}
    return res
}

function compToId(html) {
    var id = /kaggle\/(\d+)/.exec(html)[1]
    return id
}

function download(name) {
    console.log(`name: ${name}`)
	var url = `https://www.kaggle.com/c/${name}/code`
	var r = request('GET', url)
	var cookies = {}
	for(var kv of r.headers['set-cookie']) {
		kv = kv.split('; ')[0].split('=')
		if(kv.length < 2) continue
		cookies[kv[0]] = kv[1]
	}
	var cookieStr = Object.entries(cookies)
		.map(x => x[0] + '=' + x[1]).join('; ')
	// console.log(cookieStr)
	
	var id = compToId(r.body.toString())
	console.log(`id: ${id}`)
	var headers = {
		'Cookie': cookieStr,
		'x-xsrf-token': cookies['XSRF-TOKEN'],
	}
	var toc = getToc(id, headers)
    var articles = [{title: `Kaggle Kernel - ${name}`, content: ''}]
    var imgs = new Map()
    for(var it of toc) {
        var notebooks = it.outputFiles.filter(
			x => x.name == '__results__.html' ||
			     x.name == '__resultx__.html'
		)
		if (notebooks.length == 0)
			continue
		var realUrl = notebooks[0].downloadUrl
		console.log(`url: ${realUrl}`)
        var co = request('GET', realUrl).body.toString()
		co = processImg(getBody(co), imgs, {
			pageUrl: realUrl,
			imgPrefix: '../Images/',
		})
        var from = `<p>From: <a href='${url}'>${url}</a></p>`
        var score = ''
        if(it.bestPublicScore)
            score = `<p>Score: ${it.bestPublicScore}</p>`
		var prefix = 'https://www.kaggle.com'
        var au = `<p>Author: <a href='${prefix + it.author.profileUrl}'>${it.author.displayName}</a></p>`
        co = `${from}\n${au}\n${score}\n${co}`
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
