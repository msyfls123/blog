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

**Django 模板**

这大概是我用过最早的模板了，甚至还记得当时第一次联动 MySQL 输出动态内容时的喜悦，语法接近于 ejs，大括号加 % 包裹一切。用起来平平无奇，只记得 Python 传数据用 dictionary 很麻烦，每次都要加 `['*']` 来获取对应的键值。但这种模板的好处是跟后端彻底分离，只作为模板单独存在，也容易替换。

**[Plim](https://plim.readthedocs.io/en/latest/)**

平心而论这可以说是我见过地表最强的模板了，像瑞士军刀一样百搭。基于 Mako 的设计，使其支持了很多你想要的功能，很多你想都想不到的功能它也支持。甚至直接在模板层编译 Sass 和 Stylus，还有 markdown。但它最最令人满意的是，和 Jade（现在叫 Pug 了）还有 Python 一样，是**基于缩进来区分嵌套层级**的。

![Plim](/blog/images/html-templates/01-16-52.png)

![less is more](/blog/images/html-templates/01-20-31.png)

当你写了一整天代码，突然说要改个模板中的链接，你就会发现没有闭合尖括号的代码是多么的赏心悦目。

## JavaScript 模板

### 静态模板

**Handlebars / Mustache**

这两个框架都以他们的 logo 而闻名，大胡子形象深入人心。要说还有啥特别之处，倒不如说是他们都有别的语言的实现，可以方便地迁移。哦，对了，还都定位于可以渲染不只是 HTML 的内容，比如 RTF 或者配置文件 config.ini 之类，但还有哪个别的框架不能这么做吗？微笑脸😊

**ejs**

一个标榜自己是纯 JS 语法的模版，广义上来说它也算是 JSX 的一种了。相比其他模板遮遮掩掩去写 loop 和 if/else 标签，它做到了原生 JS 的控制流。

```ejs
<% if (user) { %>
  <h2><%= user.name %></h2>
<% } %>
```

```ejs
<ul>
  <% users.forEach(function(user){ %>
    <%- include('user/show', {user: user}); %>
  <% }); %>
</ul>
```

怎么说呢，看起来虽然有些怪，但还是比较符合直觉的哈。

**nunjunks**
又一个舶来品，从 Python 的 Jinja2 改装而来，总体平平无奇，有个 asyncAll 的功能可以在模板里用 Promise，但我何必呢 …… 直接在外面拼好不就行了。

### 动态模板

**JSX**

JSX 可谓是大道至简。语法上除了直接渲染 Array 展开表示 for loop 和 `&&` 表示 if 之外，再无别的特殊语法。哦，还有个 `dangerouslySetInnerHTML` 可以表示 raw 输出 js 内容到 HTML。

可以说是跟 React 的理念一样，消除了绝大部分需要记忆的内容。

**all-in-one (Vue, Svelte)**

这种模板，又可以说是框架的一部分，早已为了框架整体的性能或者架构设计而做了很多特殊适配。比如 Angular 的 Ivy Rendering Engine 就思考了这样一个问题，到底是现有组件还是现有模板？很明显从数据的流向来说，先有组件里的 data 再有 template，这样就出现了问题，在加载组件时要先加载组件的 class 部分再去 compile template，那不就存在 template 不对应但却运行下去了？所以 Ivy 就把 template 里的类型定义反转暴露给组件侧进行 AOT 检查。

详见 https://www.angularminds.com/blog/what-is-angular-ivy

> The Ivy Compilation Model
> 
> In the Ivy model, Angular decorators (@Injectable, etc) are compiled to static properties on the classes (ngInjectableDef). This process takes place without a complete analysis of code, and in most cases with a decorator only. Here, the only exception is @Component, which requires knowledge of the meta-data from the @NgModule which declares the component in order to properly generate the ngComponentDef. The selectors which are applicable during the compilation of a component template are determined by the module that declares that component.
> 
> The information needed by Reference Inversion and type-checking is included in the type declaration of the ngComponentDef in the .d.ts. Here, Reference Inversion is the process of determining the list of the components, directives, and pipes on which the decorator(which is getting compiled ) depends, allowing the module to be ignored altogether. 

# 解决方案

## 目标

- 同时支持 SSR 和 SPA 动态渲染
- 对数据和现有框架侵入低

## Next.js 介绍
