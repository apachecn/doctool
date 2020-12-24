const fs = require('fs')
const chp = require('child_process')
const path = require('path')
const moment = require('moment')
const nbp = require('npm-book-publisher')
const {
	defaultHdrs,
	requestRetry,
	getGhFile,
	listGhFiles,
	getGhRepos,	
} = require('./gh_util.js')

const request = requestRetry

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
    var docs = getGhRepos('apachecn')
        .map(x => ['apachecn', x])
        .concat(extras)
        .sort((a, b) => a[1].localeCompare(b[1]))
    console.log(`仓库读取完毕`)
    
    for(var [un, repo] of docs) {
        console.log(un + '/' + repo)
        // 在这里填写过滤条件
        var rootFiles = listGhFiles(un, repo)
        if(!rootFiles.includes('index.html') || 
           !rootFiles.includes('README.md') ||
		   !rootFiles.includes('SUMMARY.md'))
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
