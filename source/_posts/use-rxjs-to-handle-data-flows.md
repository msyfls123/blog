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
在前端开发中，虽然大部分时间都是在”接受用户操作数据将它们发送给服务器，再从服务器拉取数据展示成 UI 给用户“，但偶尔还是会有一些操作和显示不同步的情形，例如用户不停地在搜索框输入文字，那么在用户输入的时候其实是不希望一直去网络请求“建议搜索项”的，一方面会闪烁很厉害，一方面也会发出不必要的请求，可以用防抖 `debounce` 和节流 `throttle` 函数优化输入体验。

![](/blog/images/use-rxjs-to-handle-data-flows/20-41-12.gif)

单个组件也许只需要加个 `lodash` 的纯函数即可，但遇到**更复杂**的输入情形会是如何呢？

# 实际问题

## 问题 1：简单识别 URL

![识别 URL](/blog/images/use-rxjs-to-handle-data-flows/21-42-51.png)

如上图所示，左侧是一个 window，从其他地方将一个带有超链接的文本复制到剪贴板之后切换到这个 window，我们希望在 window 的 `focus` 事件发出时能够识别到这个链接并打开。

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

![记忆已识别的文本](/blog/images/use-rxjs-to-handle-data-flows/22-06-27.png)

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

![链接卡片](/blog/images/use-rxjs-to-handle-data-flows/22-43-16.png)

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

我们创建了一条最基本的数据流 `textInClipboard`，它是所有后续操作的源头。从技术角度讲，它是一个 `Subject`，也就是作为触发器接受数据，也能够作为 Observable 向 Observer 发送数据。

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

上面的代码创建了 `textInClipboard` Subject，并创建 `checkUrlInClipboard` 函数，在其中将当前剪贴板里的值传递给 `textInClipboard`，这样在 window 侧只需要调用这个方法就可以触发后面的一系列数据操作了。

```diff
thisWindow.on('focus', () => {
  const text = clipboard.getText();
-   handleClipboardText(text);
+   checkUrlInClipboard(text);
})
```

## 数据~~根据 memorized text~~去重

创建完了接受用户操作的数据流之后，就需要对输入做去重，连续触发多次（例如用户在多个窗口间切换并不会连续识别 URL，而是只识别**不同的第一个**。

![去重](/blog/images/use-rxjs-to-handle-data-flows/23-51-12.png)

这在 RxJS 中非常容易实现，可以使用 [distinctUntilKeyChanged](https://rxjs-dev.firebaseapp.com/api/operators/distinctUntilKeyChanged) 运算符。

加上常用的 [filter](https://rxjs-dev.firebaseapp.com/api/operators/filter) 和 [map](https://rxjs-dev.firebaseapp.com/api/operators/map)，我们就组合出了一套简易过滤**有效 URL**的管道，将上面的 `textInClipboard` 灌进去试一试。

```js
import { map, filter, distinctUntilKeyChanged } from 'rxjs/operators';

const URL_REG = /(?:(?:https|http):\/\/)?docs\.qq\.com\/\w+/;

const filteredUrlInClipboard$ = textInClipboard.pipe(
  distinctUntilKeyChanged('text'),
  map(({ text, ...rest }) => {
    const matched = text.match(URL_REG);
    if (matched) {
      return {
        url: matched[0],
        ...rest,
      }
    }
  }),
  filter(Boolean(e?.url)),
);

filteredUrlInClipboard$.subscribe(console.log);
```

演示一下。

![](/blog/images/use-rxjs-to-handle-data-flows/00-52-12.gif)

## 分发 HTTP 请求后的数据

处理完了重复的文本，下面就该将筛选出的 URL 通过 HTTP 请求去获取详细信息了。

现在前端通常使用 `fetch` 直接发起 HTTP 请求，得到的是一个 `Promise`，如何将 `fetch` 与 `RxJS` 有机结合起来？RxJS 自身提供了 [`from`](https://rxjs-dev.firebaseapp.com/api/index/function/from) 创建符，将一个 `Promise` 转变成 Observable 是非常容易的。

```js
import { from } from 'rxjs';

const fetch$ = from(fetch(someUrl));
```

但这里我们对程序的可维护性和健壮性提出了更高的要求：

- **同时支持多个 HTTP 请求，并且将它们放在一个 Observable 里处理。**
- **支持 HTTP 请求的错误重试及 log 功能。**

### mergeMap 拍平请求

![](/blog/images/use-rxjs-to-handle-data-flows/00-27-00.png)

针对第一个要求，可以使用 [`mergeMap`](https://rxjs-dev.firebaseapp.com/api/operators/mergeMap) 来将 URL 一一映射成 `fetch` 得到的 Observable，因为是在一个 Observable 里创建出的 Observable，所以是高阶 Observable，再将这些高阶 Observable 收集起来变成 Observable 吐出的一个个值，就成为了 `docInfo$` 的新 Observable，其中每一个值都是从 HTTP 请求返回的文档信息。

```js
import { from } from 'rxjs';
import { mergeMap } from 'rxjs/operators';

const CGI_URL = 'example.com/get-info';

const docInfo$ = filteredUrlInClipboard$.pipe(
  mergeMap(url => from(
    fetch(`${CGI_URL}?url=${encodeURIComponent(url)}`)
  ))
);
```

其实 `mergeMap` 原来叫做 `flatMap`，是不是更有拍平摊开的意味？

### 带有重试功能的请求

![](/blog/images/use-rxjs-to-handle-data-flows/23-47-11.png)

RxJS 里的 Observable 如果出错了，默认是直接在当前 Observable 发出 error，并且终止，意味着一次失败的请求后面的请求将永远不会被发出了，这肯定不是我们希望看到的。首先我们得接住这个爆出来的 error，可以用 [`catchError`](https://rxjs-dev.firebaseapp.com/api/operators/catchError) 操作符。接下来考虑网络不稳定的情形，添加自动重试逻辑，这里会用到比较多的操作符，先将示例代码展示在这里，感兴趣的同学可以自行研究 RxJS 的重试机制，相信会大有裨益。

```js
import { defer, timer, NEVER, throwError } from 'rxjs';
import { retryWhen, concatMap, mergeMap, catchError } from 'rxjs/operators';

const CGI_URL = 'example.com/get-info';

const retryThreeTimesWith500msDelay = retryWhen(errors => ( // <-- projector
  errors.pipe(concatMap((e, i) => {
    console.error(`第 ${i + 1} 次失败`, e.toString());
    return i >= 3 ? throwError(e) : timer(500);
  }))
));

const docInfo$ = filteredUrlInClipboard$.pipe(
  mergeMap(url => (
    defer(() => fetch(`${CGI_URL}?url=${encodeURIComponent(url)}`)).pipe(
      retryThreeTimesWith500msDelay,
      catchError((error) => {
        console.error(`获取 url=${url} 的信息失败`, error.toString());
        return NEVER;
      })
    )
  ))
);

```

这段代码做了很多事情，`retryThreeTimesWith500msDelay` 里的 `retryWhen` 接受一个 projector 函数，传入的 errors 是一个 Observable，它在上游每次报错时吐出一个值 e，这里可以拿到 e 和索引 i，而这个 projector 返回的 Observable 一旦发出值就会重新 subscribe 上游 Observable（相当于再来一次），而当它报错时，这个错误将会抛给上游 Observable 并完结，是不是听的一头雾水？看看 GIF 图吧。

![](/blog/images/use-rxjs-to-handle-data-flows/01-18-26.gif)

然后特别需要重点注意的是，这里替换掉了 `from` 创建符，而使用 `defer` 代替，为什么？

**因为 from 是 hot observable，也就是无论有么有被订阅都会自顾自发出值，并且再次订阅后也不会重复发出已有值，就像直播一样。**
**而 defer 则像是视频，它是 cold observable，每次被订阅都会重新走一遍流程。**

这点非常重要，所以在需要重复操作的地方还是需要 `defer` 来重复创建可利用的 Observable。

而在最后我们 `catchError` 里，处理掉错误信息并打 log 后，直接返回 `NEVER`，也就意味着这个错误将消失在漫漫长河里，不会对下游造成影响。

## 拓展边界

# RxJS 的意义

（未完待续
