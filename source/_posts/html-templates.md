---
title: HTML 模板
date: 2023-12-30 00:10:47
tags: [HTML, 渲染]
categories: web
thumbnail: images/html-templates/00-25-24.png
disqusId: html-templates
---

前端三剑客 HTML/CSS/JavaScript。JavaScript 已经飞黄腾达，甚至都不认浏览器这个祖宗了；CSS 痴迷与自己的布局样式、动画和色彩、Houdini 扩展等等，进入了修仙的通道。看来看去只剩 HTML 这个老顽固还在自己的一亩三分地里爬坑，几十年来一点长进都没有。

虽然 web components 让人们看到了重拾 HTML 组件的希望，但随着 Safari 等厂商的不配合，以及深入探究后的继承兼容性问题，最终也没有达成一致。HTML 还是归于一滩死水。但这样的的好处也很明显，像其他领域还在挣破头皮要开发新功能时，HTML 只要能渲染 `if/else`, `for loop`,`import/include`, `pipe/filter` 就谢天谢地足够日常使用了。

正因如此，其实各家 MVVM 与其说是为了渲染 HTML 而写了个框架，不如说是挂羊头卖狗肉专职搞数据流，只是把随手写的 HTML 模板滥竽充数地塞到了用户面前。而这也造成了各家的模板语言五花八门，根本无法有效互通。

![React](/blog/images/html-templates/00-46-00.png)
![Svelte](/blog/images/html-templates/00-46-34.png)
![Vue](/blog/images/html-templates/00-47-46.png)
![Angular](/blog/images/html-templates/00-49-08.png)

更可恶的是，小程序还有一套模板语言……

这些模板可谓是争奇斗艳，群魔乱舞。但最大的一个问题是，很多模板都在破坏 HTML 自身的[图灵完备](https://tcya.xyz/2015/06/07/pure-html-Turing-machine-program.html)。几十年后，不要说读懂这段代码，就是运行版本都找不到。

有悲观的博主甚至直接[切换到了 web components](https://jakelazaroff.com/words/web-components-will-outlive-your-javascript-framework/) 来对抗这种不确定性，但这只适合于自娱自乐的自嗨项目，公司级项目肯定不合适。咋办呢？先调研调研用过的模板吧。

# 模板大赏

## 非 JavaScript 模板

Django 模板

这大概是我用过最早的模板了，甚至还记得当时第一次联动 MySQL 输出动态内容时的喜悦，语法接近于 ejs，大括号加 % 包裹一切。用起来平平无奇，只记得 Python 传数据用 dictionary 很麻烦，每次都要加 `['*']` 来获取对应的键值。但这种模板的好处是跟后端彻底分离，只作为模板单独存在，也容易替换。

[Plim](https://plim.readthedocs.io/en/latest/)

平心而论这可以说是我见过地表最强的模板了，像瑞士军刀一样百搭。基于 Mako 的设计，使其支持了很多你想要的功能，很多你想都想不到的功能它也支持。甚至直接在模板层编译 Sass 和 Stylus，还有 markdown。但它最最令人满意的是，和 Jade（现在叫 Pug 了）还有 Python 一样，是**基于缩进来区分嵌套层级**的。

![Plim](/blog/images/html-templates/01-16-52.png)

![less is more](/blog/images/html-templates/01-20-31.png)

当你写了一整天代码，突然说要改个模板中的链接，你就会发现没有闭合尖括号的代码是多么的赏心悦目。

## JavaScript 模板

### 静态模板

Handlebars

ejs

nunjunks

### 动态模板

JSX

all-in-one (Vue, Svelte)

# 解决方案

## 目标

- 同时支持 SSR 和 SPA 动态渲染
- 对数据和现有框架侵入低

## Next.js 介绍
