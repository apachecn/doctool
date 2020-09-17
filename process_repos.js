const fs = require('fs')
const chp = require('child_process')
const path = require('path')
const moment = require('moment')
const req = require('sync-request')

// 需要将 Token 添加进环境变量
const GH_TOKEN = process.env['GH_TOKEN']
const defaultHdrs = {'User-Agent': 'ApacheCN'}

function requestRetry(method, url, ops) {
    for (var i = 1; ; i++) {
        try {
            return req(method, url, ops)
        } catch(ex) {
            console.log(`$method $url: retry $i`)
        }
    }
}

const request = requestRetry

function getRootFile(un, repo) {
    var hdrs = Object.assign({}, defaultHdrs)
    hdrs['Authorization'] = 'Token ' + GH_TOKEN
    var url = `https://api.github.com/repos/${un}/${repo}/contents`
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

function main() {
    var dir = process.argv[2]
    var docs = getGhRepos('apachecn')
    console.log(docs)
    
    for(var doc of docs) {
        console.log(doc)
        var rootFiles = getRootFile('apachecn', doc)
        // 在这里填写过滤条件
        var isDocRepo = rootFiles.includes('doc') ||
                        rootFiles.includes('docs') ||
                        rootFiles.includes('SUMMARY.md')
        if(!isDocRepo || rootFiles.includes('LICENSE'))
           continue
        // -----------------------
        var docDir = path.join(dir, doc)
        if(!fs.existsSync(docDir)) {
            process.chdir(dir)
            chp.spawnSync('git', ['clone', `https://github.com.cnpmjs.org/apachecn/${doc}`], {stdio: 'inherit'})
            if(!fs.existsSync(docDir)) continue
            process.chdir(doc)
            chp.spawnSync('git', ['remote', 'set-url', 'origin', `https://github.com/apachecn/${doc}`], {stdio: 'inherit'})
            process.chdir('..')
        }
        process.chdir(docDir)
        chp.spawnSync('git', ['pull'], {stdio: 'inherit'})
        // 在这里填写操作
        fs.copyFileSync(path.join(__dirname, 'LICENSE'), path.join(docDir, 'LICENSE'))
        // -----------------------
        chp.spawnSync('git', ['add', '-A'], {stdio: 'inherit'})
        chp.spawnSync('git', 
            ['commit', '-am', moment().format('YYYY-MM-DD HH:mm:ss')], 
            {stdio: 'inherit'})
        chp.spawnSync('git', ['push'], {stdio: 'inherit'})
    }
}

if(require.main === module) main()
