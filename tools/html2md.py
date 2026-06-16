#!/usr/bin/env python3
"""HTML → Jekyll Markdown 转换工具。

将自包含 HTML 文档（含 base64 图片、KaTeX 公式、表格、callout 提示框）
转换为 Jekyll 兼容的 Markdown 文件。

用法:
    python html2md.py <输入.html> <输出目录> [标题] [日期]

示例:
    python html2md.py report.html ./my-blog/ "我的报告" "2026-06-16"

输出:
    - _posts/YYYY-MM-DD-标题.md     Jekyll 文章
    - assets/images/html-report-fig*.png  提取的图片

关键教训（写在代码注释里）:
    ⚠️ 实体解码必须在标签清理之后执行！
       &lt; → < 会产生虚假 HTML 标签，吞噬后续内容。
"""

import sys
import re
import html as html_mod
import base64
from pathlib import Path
from datetime import date

# ── Windows GBK 终端兼容 ──
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════
# 配置区域 —— 按项目需求修改
# ═══════════════════════════════════════════════════════════════════════

CALLOUT_LABELS = {
    'info':   '[INFO]',
    'warn':   '[WARN]',
    'danger': '[DANGER]',
    'ok':     '[OK]',
    'tip':    '[TIP]',
}

# SVG 图片 / 侧边栏泄露到正文中的纯文本行，需从最终输出剔除
STRAY_OVERLAY_LINES = [
    'REVISION V4.0',
    'Balloon 1.5m', 'RCS -35 dBsm', 'Sonde', '10-60m',
    'D=600mm', 'RCS -5.5 dBsm', 'WEATHER RADAR',
    'Beam ~1deg', 'R1 (sphere)', 'R2 (sonde)', 'dR=R1-R2',
    'Closed cells > 95%', 'CNC Machined Surface',
    'Ra 3-5um | Cut-open cells', 'Conductive Coating',
    'Ag-based 25-75um | Rs', 'Skin depth ~20um @ S-band',
    'PMI Closed-Cell Foam + Conductive Coating (ROHACELL IG-F)',
]

STRAY_FIG_CAPTIONS = [
    'Deployment geometry', 'PMI closed-cell', 'All three targets',
]


# ═══════════════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════════════

def html_to_markdown(html_path, output_dir, post_title=None, post_date=None):
    """主转换函数。

    Args:
        html_path:  源 HTML 文件路径
        output_dir: Jekyll 项目根目录
        post_title: 博客文章标题 (默认从 <title> 提取)
        post_date:  发布日期 (默认取当天)

    Returns:
        str: 生成的 .md 文件路径
    """
    out = Path(output_dir)

    # ── 1. 读取源文件 ──────────────────────────────────────
    with open(html_path, 'r', encoding='utf-8') as f:
        html_src = f.read()
    print(f'Read: {html_path} ({len(html_src):,} chars)')

    # ── 2. 提取 base64 图片 ─────────────────────────────────
    img_re = re.compile(r'<img src="data:image/(\w+);base64,([^"]+)"[^>]*>')
    img_map = {}  # idx -> (ext, b64data)

    def _replace_img(m):
        idx = len(img_map) + 1
        ext = m.group(1)
        data = m.group(2)
        img_map[idx] = (ext, data)
        return (
            f'![Fig{idx}]'
            f'({{{{ "/assets/images/html-report-fig{idx}.{ext}"'
            f' | relative_url }}}})'
        )

    html_no_img = img_re.sub(_replace_img, html_src)

    img_dir = out / 'assets' / 'images'
    img_dir.mkdir(parents=True, exist_ok=True)
    for idx, (ext, data) in img_map.items():
        fpath = img_dir / f'html-report-fig{idx}.{ext}'
        with open(fpath, 'wb') as f:
            f.write(base64.b64decode(data))
        print(f'  Image [{idx}]: {fpath.name} ({fpath.stat().st_size/1024:.1f} KB)')

    # ── 3. 提取正文（深度计数器，严格匹配嵌套） ───────────
    main_start = html_no_img.find('<div class="main">')
    if main_start == -1:
        main_start = html_no_img.find('<body>')
        if main_start == -1:
            raise SystemExit('ERROR: cannot find <div class="main"> or <body>')
        main_start += len('<body>')
    else:
        main_start += len('<div class="main">')

    # 我们已经在 <div class="main"> 内部，所以初始深度 = 1
    depth = 1
    pos = main_start
    main_end = None

    while pos < len(html_no_img):
        next_open = html_no_img.find('<div', pos)
        next_close = html_no_img.find('</div>', pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                main_end = next_close
                break
            pos = next_close + 6

    if main_end is None:
        raise SystemExit('ERROR: cannot locate end of main content div')

    body = html_no_img[main_start:main_end]
    print(f'Body extracted: {len(body):,} chars')

    # ── 4. 移除脚本和导航 ──────────────────────────────────
    body = re.sub(r'<script[^>]*?>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<nav class="sidebar-toggle">.*?</nav>', '', body, flags=re.DOTALL)

    # ── 5. HTML 元素 → Markdown ────────────────────────────

    # 标题
    body = re.sub(r'<h2[^>]*?>(.*?)</h2>', r'\n\n## \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<h3[^>]*?>(.*?)</h3>', r'\n\n### \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<h4[^>]*?>(.*?)</h4>', r'\n\n#### \1\n', body, flags=re.DOTALL)

    # 段落
    body = re.sub(r'<p[^>]*?>(.*?)</p>', r'\n\n\1\n', body, flags=re.DOTALL)

    # 粗体 / 斜体 / 链接 / 换行
    body = re.sub(r'<strong>(.*?)</strong>', r'**\1**', body)
    body = re.sub(r'<em>(.*?)</em>', r'*\1*', body)
    body = re.sub(r'<a href="([^"]+)"[^>]*?>(.*?)</a>', r'[\2](\1)', body)
    body = re.sub(r'<br\s*/?>', '\n', body)

    # Callout 提示框 (★ 必须在清理 div 之前处理 ★)
    # 关键：先消除 callout 内部的嵌套 div（<div class="lbl">），
    # 否则非贪婪 .*? 会被内部 </div> 截断（与教训 #2 相同的问题）
    body = re.sub(
        r'<div class="lbl">(.*?)</div>',
        r'**\1：**', body, flags=re.DOTALL,
    )

    def _callout(m):
        cls = m.group(1)
        inner = m.group(2)
        label = CALLOUT_LABELS.get(cls, cls.upper())
        inner_text = inner
        inner_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', inner_text)
        inner_text = re.sub(r'<em>(.*?)</em>', r'*\1*', inner_text)
        inner_text = re.sub(r'<[^>]+>', '', inner_text)
        inner_text = re.sub(r'\s+', ' ', inner_text).strip()
        return f'\n> **{label}:** {inner_text}\n'

    body = re.sub(
        r'<div class="callout\s+(\w+)"[^>]*?>(.*?)</div>',
        _callout, body, flags=re.DOTALL,
    )

    # 版本标签
    body = re.sub(
        r'<span class="tag\s+tag-(\w+)"[^>]*?>(.*?)</span>',
        r'*[\2]*', body,
    )

    # 表格 → GFM
    def _table(m):
        rows = re.findall(r'<tr>(.*?)</tr>', m.group(0), re.DOTALL)
        md_rows = []
        for i, row in enumerate(rows):
            cells = re.findall(r'<t[hd][^>]*?>(.*?)</t[hd]>', row, re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if not cells:
                continue
            md_rows.append('| ' + ' | '.join(cells) + ' |')
            if i == 0:
                md_rows.append('|' + '|'.join(['------' for _ in cells]) + '|')
        return '\n' + '\n'.join(md_rows) + '\n'

    body = re.sub(r'<table[^>]*?>.*?</table>', _table, body, flags=re.DOTALL)

    # KaTeX annotation → MathJax
    body = re.sub(
        r'<annotation encoding="application/x-tex">(.*?)</annotation>',
        lambda m: f'${m.group(1)}$', body, flags=re.DOTALL,
    )

    # 列表 / 分割线 / 上标
    body = re.sub(r'<li>(.*?)</li>', r'- \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<ul[^>]*?>', '\n', body)
    body = re.sub(r'</ul>', '\n', body)
    body = re.sub(r'<ol[^>]*?>', '\n', body)
    body = re.sub(r'</ol>', '\n', body)
    body = re.sub(r'<hr[^>]*?>', '\n---\n', body)
    body = re.sub(r'<sup>(.*?)</sup>', r'^\1^', body)

    # ── 6. 剥离 div / span 外壳 ────────────────────────────
    body = re.sub(r'</?div[^>]*?>', '', body)
    body = re.sub(r'</?span[^>]*?>', '', body)

    # ── 7. 清理残留 table/tr/td ────────────────────────────
    body = re.sub(r'</?table[^>]*?>', '', body)
    body = re.sub(r'</?t[rhd][^>]*?>', '', body)

    # ── 8. ★★★ 关键步骤：标签清理 → 实体解码 ★★★ ─────────
    # 顺序不可颠倒！先清除所有 <...> 标签，再解码 &lt; → <
    body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
    body = re.sub(r'</?section[^>]*?>', '', body)
    body = re.sub(r'</?h1[^>]*?>', '', body)
    body = re.sub(r'<[^>]+>', '', body)

    body = html_mod.unescape(body)
    body = body.replace('​', '')  # zero-width space

    # ── 9. 移除 SVG 图注残留 ───────────────────────────────
    for line in STRAY_OVERLAY_LINES:
        body = re.sub(r'^' + re.escape(line) + r'$', '', body, flags=re.MULTILINE)
    for cap in STRAY_FIG_CAPTIONS:
        body = re.sub(r'^Fig\.\d+:\s*' + re.escape(cap) + r'.*$', '', body, flags=re.MULTILINE)

    # ── 10. 空白行收束 ─────────────────────────────────────
    lines = body.split('\n')
    result = []
    blank = 0
    for line in lines:
        s = line.rstrip()
        if s == '':
            blank += 1
            if blank <= 2:
                result.append('')
        else:
            blank = 0
            result.append(s)
    body = '\n'.join(result)
    body = re.sub(r'(#+\s+.*)\n\n\n+', r'\1\n\n', body)
    body = body.strip()

    # ── 10b. 分离 Figure 标题 ─────────────────────────────────
    # "![...](...)Figure X-Y: caption" → "![...](...)\n\n*Figure X-Y: caption*"
    body = re.sub(
        r'(!\[.*?\]\(\{\{.*?\}\}\))(Figure [\w\d\-]+:.*?)$',
        r'\1\n\n*\2*',
        body, flags=re.MULTILINE,
    )

    # ── 11. 组装 Jekyll 文章 ───────────────────────────────
    if post_title is None:
        m = re.search(r'<title>(.*?)</title>', html_src)
        post_title = m.group(1) if m else 'Untitled'
    if post_date is None:
        post_date = date.today().isoformat()

    slug = re.sub(r'[^\w一-鿿]+', '-', post_title).strip('-')[:60]
    filename = f'{post_date}-{slug}.md'

    post = (
        f'---\n'
        f'layout: default\n'
        f'title: {post_title}\n'
        f'date: {post_date}\n'
        f'---\n\n'
        f'*Converted from HTML. {len(img_map)} figure(s).*\n\n'
        f'{body}\n'
    )

    posts_dir = out / '_posts'
    posts_dir.mkdir(parents=True, exist_ok=True)
    post_path = posts_dir / filename
    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(post)

    print(f'Done: {post_path}  ({len(post):,} chars, {len(img_map)} images)')
    return str(post_path)


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    html_to_markdown(
        html_path=sys.argv[1],
        output_dir=sys.argv[2],
        post_title=sys.argv[3] if len(sys.argv) > 3 else None,
        post_date=sys.argv[4] if len(sys.argv) > 4 else None,
    )
