## `crawler.js`

抓取网页并保存到 HTML

```
node crawler
```

### 配置文件`config.json`：

+   `fname`：保存的文件名称
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

> 注意
> 
> 图片的相对链接需要手动处理

## `split.js`

将抓取的 HTML 的章节分割成单独的文件

```
node split <file>
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