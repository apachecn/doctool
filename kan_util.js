const fs = require('fs')
const chp = require('child_process')
const path = require('path')
const moment = require('moment')
const req = require('sync-request')
const {btoa, atob} = require('abab')

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

module.exports = {
	defaultHdrs:   defaultHdrs,
	formUrlEncode: formUrlEncode,
	requestRetry:  requestRetry,
	kanExist:      kanExist,
	kanRelease:    kanRelease,
	kanToggle:     kanToggle,
	kanCreateRepo: kanCreateRepo,
}
