var request = require('sync-request');


function requestRetry(method, url, options={}) {
    
    options.retry = options.retry || 5
    
    for(var i = 0; i < options.retry; i++) {
        try {
            return request(method, url, options)
        } catch(ex) {
            if(i == options.retry - 1) throw ex;
        }
    }
}

exports.requestRetry = requestRetry
