---
title: 使用 RxJS 处理前端数据流
date: 2021-04-11 18:54:41
tags:
  - rxjs
  - data-flow
categories:
  - web
thumbnail: images/use-rxjs-to-handle-data-flows/19-54-25.png
disqusId: use-rxjs-to-handle-data-flows
---
在前端开发中，虽然大部分时间都是在”接受用户操作数据将它们发送给服务器，再从服务器拉取数据展示成 UI 给用户“，但偶尔还是会有一些操作和显示不同步的情形，例如用户不停地在搜索框输入文字，那么在用户输入的时候其实是不希望一直去网络请求“建议搜索项”的，一方面会闪烁很厉害，一方面也会发出不必要的请求，可以用防抖（debounce）和节流（throttle）函数优化输入体验。

![](/blog/images/use-rxjs-to-handle-data-flows/20-41-12.gif)

单个组件也许只需要加个 `lodash` 的纯函数即可，但遇到**更复杂**的输入情形会是如何呢？

# 实际问题

## 问题 1：简单识别 URL

![](/blog/images/use-rxjs-to-handle-data-flows/21-42-51.png)

如上图所示，左侧是一个 window，从其他地方将一个带有超链接的文本复制到剪贴板之后切换到这个 window，我们希望在 window 的 focus 事件发出时能够识别到这个链接并打开。

第一版代码可能非常简单，只需要用正则表达式判断一下即可。

```js
// window.js
const URL_REG = /(?:(?:https|http):\/\/)?docs\.qq\.com\/\w+/;

function handleClipboardText(text) {
  const matched = text.match(URL_REG);
  if (matched) {
    openUrl(matched[0])
  }
}

thisWindow.on('focus', () => {
  const text = clipboard.getText();
  handleClipboardText(text);
})
```

## 问题 2：记忆已识别的文本

![](/blog/images/use-rxjs-to-handle-data-flows/22-06-27.png)

如果有多个窗口呢？希望能只在一个窗口触发一次，那就需要一个中心化的缓存值，缓存之前处理过的文本。

```js
// main.js
let memorizedText = null;

export function checkIsMemorizedText(text) {
  if (text !== memorizedText) {
    memorizedText = text;
    return false;
  }
  return true;
}
```

而相应的处理单个 window 的地方需要改成这样
```diff
// window.js
+ import { checkIsMemorizedText } from 'main';
const URL_REG = /(?:(?:https|http):\/\/)?docs\.qq\.com\/\w+/;

function handleClipboardText(text) {
+ const checked = checkIsMemorizedText(text);
+ if (checked) return;
  const matched = text.match(URL_REG);
  if (matched) {
    openUrl(matched[0])
  }
}
```

## 进阶问题：通过 HTTP 请求获取详细数据

这时产品觉得只拿到 URL 信息展示给用户没有太大的价值，要求展示成带有丰富信息的卡片格式，问题一下子变得复杂起来。

![](/blog/images/use-rxjs-to-handle-data-flows/22-43-16.png)

当然还是可以直接在每个 window 下去发起并接受 HTTP 请求，但这样代码就会变得越来越臃肿，该怎么办呢？

# RxJS 实现数据流

这时就不满足于只是能简单处理时间间隔的 `lodash` 的 `debounce` 和 `throttle` 函数了，我们需要可以随时掌控数据流向和速率，并且具有终止重试合并等高级功能的工具。

RxJS 作为反应式编程的翘楚映入我们的眼帘，这里简单引用一下官网的介绍。

> RxJS is a library for composing asynchronous and event-based programs by using observable sequences. It provides one core type, the Observable, satellite types (Observer, Schedulers, Subjects) and operators inspired by Array#extras (map, filter, reduce, every, etc) to allow handling asynchronous events as collections.
>
> "Think of RxJS as Lodash for events."

具体教程和 API 文档可参见官网，https://rxjs.dev/guide/overview。
以及本人严重推荐程墨老师的这本[《深入浅出RxJS》](https://book.douban.com/subject/30217949/)，可以说把基础知识和实践应用讲透了。

**下面的内容需要读者对 RxJS 有基本的了解。**

## 创建数据流

我们创建了一条最基本的数据流 `textInClipboard`，它是所有后续操作的源头。从技术角度讲，它是一个 Subject，也就是作为触发器接受数据，也能够作为 Observable 向 Observer 发送数据。

```js
const textInClipboard = new Subject();

export function checkUrlInClipboard(windowId) {
  const text = clipboard.getText();
  textInClipboard.next({
    text,
    windowId,
  });
}
```

上面的代码创建了 `textInClipboard` Subject，并创建 checkUrlInClipboard 函数，在其中将当前剪贴板里的值传递给 `textInClipboard`，这样在 window 侧只需要调用这个方法就可以触发后面的一系列数据操作了。

## 数据~~根据 memorized text~~去重

## 分发 HTTP 请求后的数据

（未完待续
