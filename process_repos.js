const fs = require('fs')
const chp = require('child_process')
const path = require('path')
const moment = require('moment')
const req = require('sync-request')
const {btoa, atob} = require('abab')
var nbp = require('npm-book-publisher')

// 需要将 Token 添加进环境变量
const GH_TOKEN = process.env['GH_TOKEN']
const KAN_COOKIE = process.env['KAN_COOKIE']
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

function formUrlEncode(data) {
    return Object.entries(data)
        .map(x => encodeURIComponent(x[0]) + '=' + 
                  encodeURIComponent(x[1]))
        .join('&')
}

function kanExist(un, repo) {
    
    var url = `https://www.kancloud.cn/${un}/${repo}`
    return request('GET', url, {headers: defaultHdrs})
        .statusCode != 404
}

function kanRelease(un, repo) {
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Cookie'] = KAN_COOKIE
    hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
    
    var url = `https://www.kancloud.cn/book/${un}/{repo}/release`
    var r = request('post', url, {body: '', headers: hdrs})
    if(r.statusCode == 200 || r.statusCode == 422)
        return {code: 0, message: ''}
    else
        return {code: 1, message: r.statusCode.toString()}
}

function kanToggle(un, repo, field, on=true) {
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Cookie'] = KAN_COOKIE
    hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
    
    var data = {
        field: field,
        toggle: on? 'on': 'off',
    }
    var url = `https://www.kancloud.cn/book/${un}/${repo}/setting/toggle`
    var r = request('post', url, 
        {body: formUrlEncode(data), headers: hdrs})
    if(r.statusCode == 200)
        return {code: 0, message: ''}
    else
        return {code: 1, message: r.statusCode.toString()}
}

function kanCreateRepo(
    un, repo, title=null, desc=null, 
    type='normal', visible=true, extra={}
) {
    title = title || repo
    desc = desc || repo
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Cookie'] = KAN_COOKIE
    hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
    
    var data =  {
        type: type,
        title: title,
        name: repo,
        description: desc,
        visibility_level: visible? '20': '0',
        namespace: un,
    }
    for(var [k, v] of Object.entries(extra)) {
        data['extra[' + k + ']'] = v
    }
    var url = 'https://www.kancloud.cn/new'
    r = request('POST', url, 
        {body: formUrlEncode(data), headers: hdrs})
    if(r.statusCode == 200)
        return {code: 0, message: ''}
    else
        return {code: 1, message: r.statusCode.toString() + ' ' + r.body.toString()}
}

function getDesc(md) {
    var rm = /^#+ (.+?)$/m.exec(md)
    return rm? rm[1]: ''
}

function dockerHubExist(name, repo) {
    var url = `https://hub.docker.com/v2/repositories/${name}/${repo}/`
    var r = request('GET', url, {headers: defaultHdrs})
    return r.statusCode != 404
}

function filterDockerRepoName(name) {
    return name.toLowerCase()
        .replace(/[^\w\-]/g, '-')
        .split('-')
        .filter(x => x)
        .join('-')
}

const extras = [
    ['apachecn', 'hands-on-ml-2e-zh'],
    ['apachecn', 'principles-zh'],
    ['it-ebooks-0', 'data8-textbook-zh'],
    ['it-ebooks-0', 'prob140-textbook-zh'],
]

function main() {
    var dir = process.argv[2]
    var cacheName = 'gh_repos.json'
    var docs = getGhRepos('apachecn')
        .map(x => ['apachecn', x])
        .concat(extras)
        .sort((a, b) => a[1].localeCompare(b[1]))
    console.log(`仓库读取完毕`)
    
    for(var [un, repo] of docs) {
        console.log(un + '/' + repo)
        // 在这里填写过滤条件
        var rootFiles = listGhFiles(un, repo)
        var isDoc = rootFiles.includes('SUMMARY.md') || 
                    rootFiles.includes('doc') || 
                    rootFiles.includes('docs')
        if(!rootFiles.includes('index.html') || 
           !rootFiles.includes('README.md') || !isDoc)
            continue
        // -----------------------
        var docDir = path.join(dir, repo)
        if(!fs.existsSync(docDir)) {
            process.chdir(dir)
            chp.spawnSync('git', 
                ['clone', `https://gitclone.com/github.com/${un}/${repo}`, '-b', 'master'], 
                {stdio: 'inherit'})
            if(!fs.existsSync(docDir)) continue
            process.chdir(repo)
            chp.spawnSync('git', 
                ['remote', 'set-url', 'origin', `https://github.com/${un}/${repo}`], 
                {stdio: 'inherit'})
        }
        process.chdir(docDir)
        chp.spawnSync('git', 
            ['pull', 'origin', 'master'], 
            {stdio: 'inherit'})
        // 在这里填写操作
        
        // -----------------------
        chp.spawnSync('git', ['add', '-A'], {stdio: 'inherit'})
        chp.spawnSync('git', 
            ['commit', '-am', moment().format('YYYY-MM-DD HH:mm:ss')], 
            {stdio: 'inherit'})
        chp.spawnSync('git', ['push'], {stdio: 'inherit'})
    }
}

if(require.main === module) main()
