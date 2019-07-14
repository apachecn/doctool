## 安装依赖项

```
pip install -r requirements.txt
npm install
apt install imagemagick
apt install pngquant
```

## `epub-crawler.js`

抓取网页和图片并保存 EPUB，解压后可以得到图片和 HTML。

需要 ImageMagick 和 pngquant。包依赖见文件开头。

```
node epub-crawler
```

### 配置文件`config.json`：

+   `name`：保存的文件名称
+   `url`：目录页 URL
+   `link`：链接`<a>`的选择器
+   `base`：链接`<a>`的前缀
+   `title`：文章页的标题选择器
+   `content`：文章页的内容选择器
+   `remove`：文章页需要移除的元素的选择器
+   `credit`：是否显示原文链接
+   `processMath`：是否处理 TeX 公式
+   `processDecl`：是否处理 sphinx 类定义
+   `hdrs`：HTTP 请求的协议头
+   `list`：如果这个列表不为空，则抓取这个列表，忽略`url`

## `img-better.js`

自动压缩图片。需要 ImageMagick 和 pngquant。

```
node img-better <dir>
```

## `img.js`

保存 HTML 中的图片到同目录的`img`中，并更新 HTML 中的链接。

```
node img <file|dir>
```

## `trans.py`

调用谷歌翻译按段落翻译 HTML。

```
python trans.py <file|dir>
```

## `tomd.js`

将 HTML 转化为 MD

```
node tomd <file|dir>
```

### 规则定义`my-conventors.js`

```
RuleObj {

    filter: string|Array[string]|function(Element):boolean,
    replacement: function(string, Element):string
}

module.exports: Array[RuleObj]
```

## `sina-short.js`

将 MD 中的链接转换为新浪短网址。

```
node sina-short <file>
```

## `process_tex.js`

将 MD/HTML 中的 TeX 公式转换为图片。

```
node process_tex <dir>
```
