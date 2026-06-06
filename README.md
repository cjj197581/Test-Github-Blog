# Tech Blog

Daily technical articles — math, code, and engineering. Built with Jekyll + MathJax on GitHub Pages.

## Writing a new post

Create a `.md` file in `_posts/` named like `YYYY-MM-DD-title.md`:

```
---
layout: default
title: Your Title
---

## Section

Inline math: $x^2 + y^2 = 1$

Block math:

$$
\int_a^b f(x)\,dx
$$
```

## Local preview

```
bundle exec jekyll serve
```
