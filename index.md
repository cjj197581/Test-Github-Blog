---
layout: default
title: Home
---

# {{ site.title }}

{{ site.description }}

## Posts

{% for post in site.posts %}
- **{{ post.date | date: "%Y-%m-%d" }}** — [{{ post.title }}]({{ post.url | relative_url }})
{% endfor %}
