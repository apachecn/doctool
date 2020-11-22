var req = require('sync-request')
var moment = require('moment')
var fs = require('fs')
var genEpub = require('gen-epub')
var processImg = require('epub-crawler/src/img')

function getContent(art) {
    
    var auName = art.author.name
    var auUrl = 'https://www.zhihu.com/people/' + art.author.url_token
    var vote = art.voteup_count
    var url = art.url.replace('api/v4/answers', 'answer')
    var updTime = moment(art.updated_time * 1000).format('YYYY-MM-DD')
    var co = art.content.replace(/<noscript>.+?<\/noscript>/g, '')
        .replace(/ src=".+?"/g, '').replace(/data-actualsrc/g, 'src')
    
    var co = `
        <blockquote>
            <p>作者：<a href='${auUrl}'>${auName}</a></p>
            <p>赞同数：${vote}</p>
            <p>编辑于：<a href='${url}'>${updTime}</a></p>
        </blockquote>
        ${co}
    `
    return {title: auName, content: co}
}

function main() {
    
    var qid = process.argv[2]
    if(!qid) {
        console.log('请输入问题 ID')
        process.exit()
    }

    var url = `https://www.zhihu.com/api/v4/questions/${qid}/answers?limit=20&include=content,voteup_count`
    var res = req('GET', url).getBody().toString()
    var j = JSON.parse(res)
    var title = '知乎问答：' + j.data[0].question.title
    var co = `
        <blockquote>来源：<a href='https://www.zhihu.com/question/${qid}'>https://www.zhihu.com/question/${qid}</a></blockquote>
    `
    var articles = [{title: title, content: co}]
    var imgs = new Map()

    while(true) {
        
        console.log(url)
        var res = req('GET', url).getBody().toString()
        var j = JSON.parse(res)
        j.data.forEach(art => {
            art = getContent(art)
            art.content = processImg(art.content, imgs, {
                imgPrefix: '../Images/'
            })
            articles.push(art)
        })
        if(j.paging.is_end)
            break;
        url = j.paging.next
    }

    genEpub(articles, imgs)
}

if(module == require.main) main()
