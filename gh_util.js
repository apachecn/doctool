const fs = require('fs')
const chp = require('child_process')
const path = require('path')
const moment = require('moment')
const req = require('sync-request')
const {btoa, atob} = require('abab')

// 需要将 Token 添加进环境变量
const GH_TOKEN = process.env['GH_TOKEN']
const defaultHdrs = {'User-Agent': 'ApacheCN'}

function requestRetry(method, url, ops) {
    for (var i = 1; ; i++) {
        try {
            return req(method, url, ops)
        } catch(ex) {
            var msg = ex.toString().slice(0, 100)
            console.log(`${method} ${url}: retry ${i}: ${msg}`)
        }
    }
}

const request = requestRetry

function getGhFile(un, repo, path) {
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Authorization'] = 'Token ' + GH_TOKEN
    var url = `https://api.github.com/repos/${un}/${repo}/contents/${path}`
    var res = request('GET', url, {headers: hdrs}).body.toString()
    var j = JSON.parse(res)
    if(j.message) return ''
    return atob(j.content)
}

function listGhFiles(un, repo, path='') {
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Authorization'] = 'Token ' + GH_TOKEN
    var url = `https://api.github.com/repos/${un}/${repo}/contents/${path}`
    var res = request('GET', url, {headers: hdrs}).body.toString()
    var j = JSON.parse(res)
    if(j.message) return []
    return j.map(x => x.name)
}

function getGhRepos(un) {
    
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Authorization'] = 'Token ' + GH_TOKEN
    
    var repos = []
    
    for(var i = 1; ; i++) {
    
        var res = request(
            'GET', 
            `https://api.github.com/users/${un}/repos?type=public&page=${i}&per_page=100`, 
            {headers: hdrs}
        ).body.toString()
        var j = JSON.parse(res)
        if(j.message) break;
        if(j.length == 0) break;
        for(var o of j) {
            if(!o.fork)
                repos.push(o.name)
        }
    }
    
    return repos;
}

module.exports = {
	defaultHdrs:  defaultHdrs,
	requestRetry: requestRetry,
	getGhFile:    getGhFile,
	listGhFiles:  listGhFiles,
	getGhRepos:   getGhRepos,
}
