---
layout: default
title: 项目工作小结——GitHub Pages 技术博客搭建
date: 2026-06-06
---

# 项目工作小结：GitHub Pages 技术博客搭建

## 一、项目概述

**目标**：从零开始搭建一个基于 GitHub Pages 的个人技术博客，支持 Markdown 写作、LaTeX 数学公式渲染和图片嵌入，并将一份约 2.8MB 的 HTML 技术论证报告转换为博客文章上线发布。

**仓库地址**：https://github.com/cjj197581/Test-Github-Blog  
**线上地址**：https://cjj197581.github.io/Test-Github-Blog/  
**完成日期**：2026-06-06

---

## 二、技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 托管平台 | GitHub Pages | 免费、推送即部署、无需 CI 配置 |
| 静态站点 | Jekyll | GitHub Pages 原生支持，Markdown 渲染零配置 |
| 数学公式 | MathJax 3 (CDN) | 支持 `$...$` 行内和 `$$...$$` 块级 LaTeX，配置简单 |
| 主题 | Minima (默认) | 开箱即用，可通过自定义布局覆盖 |
| 样式 | 手写 SCSS | 轻量级自定义，无需引入完整 CSS 框架 |

---

## 三、实施过程

### 3.1 第一阶段：博客基础搭建（commit `9260edd`）

创建了完整的 Jekyll 站点骨架，共 10 个文件：

```
├── _config.yml              # 站点配置
├── Gemfile                  # Ruby 依赖（github-pages gem）
├── _layouts/default.html    # 自定义布局（注入 MathJax 3 CDN）
├── index.md                 # 首页（自动列出所有文章）
├── about.md                 # 关于页
├── _posts/
│   └── 2026-06-06-welcome.md  # 示例文章（演示公式 + 图片 + 代码 + 表格）
├── assets/
│   ├── css/style.scss       # 自定义样式
│   └── images/sample.svg    # 示例图片
├── .gitignore
└── README.md
```

关键技术点：

- **MathJax 配置**：在 `_layouts/default.html` 的 `<head>` 中通过 `<script>` 配置 `inlineMath: [['$', '$'], ['\\(', '\\)']]` 和 `displayMath: [['$$', '$$'], ['\\[', '\\]']]`，使 Markdown 中可直接书写 `$E=mc^2$` 和 `$$\int f(x)dx$$`

- **样式系统**：采用 SCSS 嵌套语法，设计响应式单栏布局（max-width 800px），支持暗色侧边栏导航、卡片式内容区域、callout 提示框等

### 3.2 第二阶段：HTML 技术报告转换（commit `38e19eb`）

将《泡沫中空镀膜金属球标校气象雷达——开题论证报告 V4.0》从自包含 HTML 文件转换为 Jekyll Markdown 博客文章。

**源文件特征**：
- 大小：2.8 MB
- 结构：单文件 HTML，含内嵌 CSS、KaTeX 渲染器、5 张 base64 编码的 PNG 图片
- 内容：10 章正文 + 4 个附录 + 参考文献，包含大量表格、数学公式、callout 提示框

**转换过程中的关键挑战与解决方案**：

#### 挑战 1：Base64 图片提取
- 问题：5 张图片以 `data:image/png;base64,...` 形式嵌入 HTML，总大小约 827 KB
- 解决：正则匹配 → base64 解码 → 写入 `assets/images/` 目录 → 替换为 Jekyll 相对路径引用
- 图片文件名：`balloon-report-fig1.png` ~ `balloon-report-fig5.png`

#### 挑战 2：嵌套 DIV 的内容提取
- 问题：HTML 中 `<div class="main">` 内部包含大量嵌套 `<div>`，用正则 `.*?` 非贪婪匹配会过早截断
- 解决：改为逐字符扫描，维护嵌套深度计数器，精确找到匹配的 `</div>` 闭合标签

#### 3：HTML 实体解码与标签清理的顺序问题（最关键 bug）
- 问题：`html.unescape()` 将 `&lt;` 解码为 `<` 后，产生了大量虚假 HTML 标签，导致后续 `<[^>]+>` 清理时误删了 4 张图片的 Markdown 引用
- 解决：**先执行标签清理，再执行实体解码**——这是本次项目最重要的工程教训

#### 挑战 4：数学公式恢复
- 问题：HTML 中 KaTeX 已将 LaTeX 渲染为 HTML 元素树，原始 LaTeX 源码丢失
- 解决：利用 KaTeX 输出的 `<annotation encoding="application/x-tex">` 元素提取原始 LaTeX 源码，替换为 MathJax 兼容的 `$...$` / `$$...$$` 格式

#### 挑战 5：HTML 语义元素的 Markdown 映射
- Callout 提示框 → `> **ICON LABEL:** content` 引用块
- 表格 → GFM 管道表格
- 列表 → `- item` 无序列表
- 标签 → `*[text]*` 斜体强调

---

## 四、项目产出

| 类别 | 数量 | 说明 |
|------|------|------|
| 配置文件 | 3 个 | `_config.yml`, `Gemfile`, `.gitignore` |
| 布局模板 | 1 个 | `_layouts/default.html`（含 MathJax） |
| 页面 | 2 个 | `index.md`, `about.md` |
| 博客文章 | 2 篇 | 示例文章 + 技术报告（共 941 行） |
| 样式文件 | 1 个 | `assets/css/style.scss` |
| 图片资源 | 6 张 | 1 张 SVG 示例 + 5 张报告 PNG |
| 文档 | 1 个 | `README.md` |
| **合计** | **16 个文件** | 项目总大小约 899 KB |

---

## 五、经验总结

### 成功的做法

1. **从简单示例开始**：先搭建可工作的最小博客（welcome 文章），验证 Jekyll + MathJax 链路，再接入复杂内容
2. **分阶段提交**：基础搭建和报告转换分两次 commit，便于回滚和对比
3. **工具脚本化**：HTML 转换写成 Python 脚本，可重复执行、逐步调试
4. **GitHub 原生工具链**：完全依赖 GitHub Pages 内置的 Jekyll，无需额外 CI 或构建工具

### 教训

1. **HTML 实体解码必须放在标签清理之后**：`&lt;` → `<` 会产生虚假标签，破坏内容完整性。正确的处理顺序是：标签清理 → 实体解码
2. **不要用正则匹配嵌套结构**：`<div>.*?</div>` 对嵌套 div 无效，应使用深度计数器逐字符解析
3. **KaTeX 渲染输出不可逆**：HTML 中的 rendered math 无法还原为 LaTeX，必须依赖 `<annotation>` 元素或原始源码
4. **大文件分块读取**：2.8MB 的 HTML 文件无法一次性传给 Read 工具，需要先了解结构（grep 章节标题）再分块读取关键部分

---

## 六、后续扩展建议

1. **标签/分类系统**：在 `_config.yml` 中配置 `collections`，实现文章按主题分类
2. **RSS 订阅**：添加 `jekyll-feed` 插件，自动生成 RSS feed
3. **评论系统**：集成 Giscus（基于 GitHub Discussions）实现文章评论
4. **搜索功能**：使用 Lunr.js 实现客户端全文搜索
5. **自动化工作流**：编写 Makefile 或脚本，一键创建新文章模板

---

*报告生成日期：2026-06-06 · 作者：CJJ*
