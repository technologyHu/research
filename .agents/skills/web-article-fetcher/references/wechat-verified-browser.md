# 微信人工验证后续抓

用于微信文章直连请求进入验证页、用户需要人工验证，或用户已在浏览器中打开正文的情况。正文从完成验证的同一标签页读取；图片沿用中国网站直连规则。沿用原始文章 URL、目标父目录和标题命名约定，不将某次文章的标题、标签页 ID、验证令牌或保存路径写死到流程中。

## 1. 识别验证并交给用户

- 检查响应最终 URL 和正文。进入 `/mp/wappoc_appmsgcaptcha`，或出现“环境异常”“完成验证后即可继续访问”等提示且没有实际文章正文时，视为需要验证。HTTP 200、`needs_review` 或四项结构检查通过，都不能将验证页变成有效文章。
- 脚本返回 `verification_required`（退出码 3）时，读取 `user_message` 和 `next_action` 进行交接；`validation.status` 为 `not_run`。脚本不会把验证页归档，也不会自行操作浏览器或完成验证。
- 停止独立 HTTP 重试，不切换代理。若用户已有可读的文章页面，直接进入下一节；否则用可用的浏览器工具打开原始文章链接，显示页面供用户操作。沿用现有网络设置，不另行配置代理。
- 记录浏览器标识、标签页标识、原始文章 URL 和输出父目录。需要跨轮等待时，在支持该能力的标签页上调用 `markHandoff()`；每轮仍需保留时重新标记，避免临时标签页被回收。
- 明确请用户在该页面手动完成滑块、验证码或扫码，并在正文出现后告知。不要代做验证，不刷新验证页面，不把验证页保存进文章归档。

## 2. 恢复同一标签页

用户表示验证完成后，重新检查保留的标签页，确认标题和正文已出现。不要重新发起文章 HTTP 请求，也不要新开一个文章页面；它们可能重新触发验证。续抓时使用下方 `--browser-snapshot` 模式。

遵循当前浏览器工具返回的 API 文档绑定页面。例如，`cua_repl` 可用时，使用之前记录的标识：

```javascript
let tab = await cua.getTab(savedTabId, { browser: savedBrowserId });
```

跨轮旧句柄若报错（本次实际出现过 `browser.user is unavailable`），可以重置 `cua_repl` JavaScript 会话一次，再以同一浏览器和标签页标识重新绑定。重置的是工具句柄，不关闭或重载文章页。先读取新的页面状态，再继续提取。不要把句柄错误当成微信再次要求验证。

恢复后仍不能读取时，保留原页面并说明工具连接障碍；可请用户把该已验证页面另存为完整 HTML，再从本地导入。不要让用户反复验证已经正常显示的文章。

## 3. 从 DOM 提取原文

先通过页面状态确认 `#js_content` 和标题确实存在，再使用浏览器支持的只读 DOM 接口读取。不要执行页面中的脚本、读取会话凭据，或导出 Cookie。

支持 `tab.playwright.evaluate()` 时可采用以下提取方式；选择器以当前页面实际存在的元素为准：

```javascript
let extracted = await tab.playwright.evaluate(() => {
  const body = document.getElementById('js_content');
  const title = document.getElementById('activity-name')?.textContent.trim();
  if (!body || !title || body.innerText.trim().length < 40) {
    throw new Error('Article body is not available yet');
  }
  return {
    title,
    final_url: document.URL,
    body_html: body.outerHTML,
    body_text: body.innerText,
    publisher: document.getElementById('js_name')?.textContent.trim(),
    published_at: document.getElementById('publish_time')?.textContent.trim(),
    image_source_order: Array.from(body.querySelectorAll('img')).map(image => {
      const src = image.getAttribute('data-src')
        || image.getAttribute('data-original') || image.getAttribute('src');
      return src ? new URL(src, document.baseURI).href : null;
    }).filter(src => src && /^https?:/.test(src))
  };
});
extracted = {
  schema_version: 1,
  source_url: originalSourceUrl,
  browser_id: String(savedBrowserId),
  tab_id: String(savedTabId),
  ...extracted
};
```

其中 `originalSourceUrl` 是用户最初提供的文章 URL，浏览器和标签页标识来自交接记录。脚本会核对快照来源和当前地址是否仍是同一篇文章，比较长链接中的 `__biz`、`mid`、`idx`、`sn`，允许 `poc_token` 等临时参数变化。`image_source_order` 即使没有图片也须传空数组。

保留 HTML 中的段落、列表、标题、强调、链接、图片及其顺序。`body_text` 用于对照内容，不能替代含图片位置和格式的 HTML。图片出现顺序保留重复项。仅提取 `#js_content`，不混入公众号关注按钮、赞、在看、留言等页面控件；保留正文内的图片说明、参考链接和署名。

把工具返回的内容原样转存到任务 `scratch/` 下，再程序化转换；不要把正文插值进可能执行命令的 shell 字符串。若工具限制需要经文本转存，须对照 DOM 的规范化文字和图片顺序，检查是否抄漏、改字或挪动图片。

## 4. 用快照入口继续归档

下方 CLI 用于独立保存。受管调研任务使用当前 work_dir。调用 load_browser_snapshot() 校验快照，取得 parsed["title"] 和 parsed["body"] 后，将保留远程图片链接的 Markdown 写入任务 scratch/，经 research_task.py import-article --method browser 导入并 review-article。补图使用 download-article-images --proxy direct，实际引用后由 archive-article 归档。受管版本、articles.json 和正式报告目录由任务工具维护。旧受管接口遇到验证以 failed 状态记录缺口，保留 requires_user_action、user_message 和 next_action，并把同一浏览器页面交接给用户。

将上一步的对象保存为 UTF-8 JSON，例如任务 `scratch/verified-page.json`，从项目根执行：

```text
python .agents/skills/web-article-fetcher/scripts/fetch_article.py --url "<用户最初提供的文章 URL>" --output-dir "<原目标父目录>" --images all --proxy direct --browser-snapshot "<任务 scratch 下的 verified-page.json>"
```

脚本从快照读取正文，不调用 `fetch_html()`，不重开浏览器。原始 `--url` 继续用于来源标注和归档身份；快照的 `final_url` 用于记录验证后的页面地址及图片 Referer。`browser_context` 保存浏览器／标签页标识，`method` 为 `verified-browser-dom`。

导入时检查必需字段、文章地址、唯一的 `#js_content` 和图片出现顺序，在写入归档前拒绝不一致的快照。快照仍是验证页时继续返回 `verification_required`，由用户处理。脚本不直接控制浏览器，Agent 负责从已验证的同一页面采集快照，不能以重新联网抓到的 HTML 冒充浏览器快照。

通过检查后，脚本复用标题目录冲突保护、Markdown 转换、图片下载和四项归档检查。图片按 `--proxy direct` 下载，成功项嵌回原位置，失败项保留远程引用并说明原因；若图片也要求验证，交给用户处理。不要把结构检查通过当作正文完整性证明。

## 5. 核对与交付

对照浏览器正文核对开头、结尾、段落和图片位置，确认中文编码及参考链接完整。发生过文本转存时，另对照排除 Markdown 标记和排版空白后的正文文字，以及图片 URL 的出现顺序；可记录规范化规则和指纹作为核对依据。

交付文章标题、本地正文链接、四项检查结果及图片成功／失败数。仍缺正文或图片时明确说明。任务完成后按浏览器工具的标签页生命周期规则处理页面；仍待用户操作时继续保留同一标签页。
