# 查作者：各站点的可靠办法

目标是拿到**创作者/UP 主/专栏作者**的名字，而不是编辑、转载号。

## B 站（最稳，走官方 API）

```
https://api.bilibili.com/x/web-interface/view?bvid=<BV号>
```
需要带两个头，否则会被拦：
```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36
Referer: https://www.bilibili.com/
```
返回 `data.owner.name` 就是 UP 主，`data.owner.mid` 是 UID（可以用来确认多个视频是否同一人）。
免登录，不需要 cookie。

## 知乎（常被反爬，按顺序试）

1. **API**：`https://www.zhihu.com/api/v4/articles/<id>?include=author` —— 经常直接返回 `{"error": ...}`。
2. **网页直连**：`curl https://zhuanlan.zhihu.com/p/<id>` —— 常被拦，只返回几百字节的跳转页。
3. **可以的话用能渲染页面的抓取工具**（WebFetch 之类）读正文，从署名、文末介绍里找。
4. **兜底（很有效）**：很多作者会写「文章目录」类的汇总文，里面自引用链接是 `作者名：文章标题` 的格式。
   拿到一次作者名，就能覆盖他名下的其它文章。

注意区分：知乎页面上的「编辑于」是编辑时间，不是作者。

## 其它常见站点

- **YouTube**：网页里 `<link itemprop="name">` 或 `ownerChannelName`；也可用 `https://www.youtube.com/oembed?url=...&format=json` 拿 `author_name`。
- **微信公众号 / 少数派 / 博客**：抓 `<meta name="author">` 或 `og:article:author`；少数派是 `sspai.com`，作者常在标题下方署名。
- **X / Twitter**：`https://x.com/<user>/status/<id>` 的 user 段就是作者。
- **小红书**：`xsec_token` 是必需参数，别从 URL 里删；作者看 `og:` 或页面署名。

## 通用建议

- 拿不到就**留空或写「未确认」**，不要猜。作者错了比没有更糟。
- 同一个作者在多个条目里出现时，用 UID / 主页链接确认是同一人再合并。
- 如果库里已有该作者的页面（如 `小林说.md`），用双链；没有就先写纯文本，问用户要不要建页
  （别凭空造一堆空页面）。
- 名字有拉丁/中文两种写法时（如「小Lin说」vs「小林说」），给已有页面加 `aliases`，让两种写法都能解析。
