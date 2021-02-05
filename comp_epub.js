var fs = require('fs')
var jszip = require('jszip')
var {optiImg, isPic} = require('epub-crawler/src/util')
// 需要安装 imgyaso

function main() {
    
    var epubName = process.argv[2]
    if (!epubName.endsWith('.epub')) {
        console.log('请提供 EPUB')
        return
    }
    
    var zip = jszip()
    if (!zip.load) {
        console.log('请安装 JSZIP 2.x')
        return
    }
    
    var data = fs.readFileSync(epubName)
    zip.load(data)
    
    for (var info of Object.values(zip.files)) {
        if (!isPic(info.name))
            continue
        
        console.log(info.name)
        var img = optiImg(info.asNodeBuffer())
        zip.file(info.name, img)
    }
    
    data = zip.generate({
        type: "nodebuffer",
        compression: "DEFLATE",
    })
    fs.renameSync(epubName, epubName + '.bak')
    fs.writeFileSync(epubName, data)
    console.log('done')
    
}

if (require.main === module) main()
