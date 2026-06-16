---
layout: default
title: Home
---

# {{ site.title }}

{{ site.description }}

<br>

<ul class="post-list">
{% for post in site.posts %}
  <li class="post-card">
    <div class="post-date">{{ post.date | date: "%Y-%m-%d" }}</div>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
  </li>
{% endfor %}
</ul>
