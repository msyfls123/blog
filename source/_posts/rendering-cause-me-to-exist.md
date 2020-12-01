---
title: 我渲染故我在，Electron 窗口开发指北
date: 2020-12-01 22:54:54
tags:
  - Electron
  - React
  - UI
categories: web
thumbnail: images/rendering-cause-me-to-exist/document_image_rId9.png
disqusId: rendering-cause-me-to-exist
---

前情摘要
========

在前一篇文章中笔者主要介绍了使用 Electron 进行开发过程中打包、构建、自动升级与文件关联相关的内容，细心的读者可能已经发现其中并没有提到与界面相关的话题。时隔一个月，中间又经历了一些需求迭代开发和代码维护，这篇文章将会尽可能详细地介绍 Electron 跨端开发中用户界面部分与平台及系统差异相关的注意点，并探索建立支持自定义多范式的窗口管理方式。

窗口开发基础
============

我住长江头，君住长江尾，日日思君不见君，共饮长江水。 ------ 李之仪

通信方式
--------

我们知道所有 Electron 自定义的窗口界面都是跑在渲染进程里的，而讲到渲染进程则不得不提到主进程。《卜算子》这首小令非常形象地道出了同一个应用里不同渲染进程和主进程之间的关系：一个应用实例只有一个主进程，而会有多个渲染进程。渲染进程之间是无法直接通信的，他们必须要通过主进程这条"长江"来通讯。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId10.png)

一个渲染进程就是管理一个 Window 的进程，通常意义上总是这样。它可以用 IPC 消息和主进程通讯，而主进程通常情况下是作为调度器来衔接各个渲染进程的，只能在收到消息后进行回复。但其实渲染进程和实际展示的网页还是有所不同的，下图简单梳理了一下「主进程 - 渲染进程 - 窗口」直接通信的方式。![](/blog/images/rendering-cause-me-to-exist/document_image_rId11.png)

上图中，ipcMain 和 webContents 都存在在主进程里，它们之间可以无缝直接调用，每个 webContents 管理一个窗口，一一对应浏览器里的 window 对象，而每个 window 对象里通过打开 nodeIntegration 开关赋予调用 Electron 的 ipcRenderer 模块发送异步或同步消息则是进程间通信的关键点。

这里有几个注意点，理清它们才能更好地规划应用的架构：

1.  ipcRenderer 通常是通信的发起者，ipcMain 只能作为通信的接受者，而 webContents 则作为中间枢纽，代理了部分 ipc 消息（如 send 或者 sendSync 消息可以直接被 webContents 截获并处理）。

2.  ipcMain 只有在接受消息时才知晓渲染进程的存在，本身应该作为一个全局的无状态的服务器。

3.  webContents 作为既存在于主进程又可以直接对应到单个 window     的对象，有效地隔离了 ipc 消息的作用域。

通常情形下，我们应该尽可能直接使用 webContents 和 ipcRenderer 之间的通讯，只有涉及到全局事件时才通过 ipcMain 进行调度。

窗口结构
--------

Electron 提供了基于 Chromium 的丰富多彩的窗口能力，注意它是基于 Chromium，所以在 Electron 里看到的几乎所有窗口（有些文件选择弹窗之类的是系统原生实现）都是一个个浏览器。这些窗口都有很丰富的选项和能力，比如最强大的 nodeIntegration 可以在浏览器环境下使用 Node.js 的能力。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId12.png)
一个简单的弹窗

![](/blog/images/rendering-cause-me-to-exist/document_image_rId13.png)
一个 DUI 的 Snackbar 

![](/blog/images/rendering-cause-me-to-exist/document_image_rId14.png)
一个复杂的多 Tab 应用

它们都是 BrowserWindow。这时问题就产生了，如何有序地管理这些窗口？Electron 是一个客户端应用，但它跑在 Node.js 上，而 Node.js 最出色的特性比如 stream 和 Event Loop 和它似乎都没啥关系。那就看看我们所熟知的 Web 应用是如何管理"多任务"的吧：在服务端，我们有基于 MVC 的路由，根据 url 转发到不同的 view 进行处理并返回，在客户端，我们也有前端路由，同样根据 url，不过是渲染成不同的 DOM 节点。

<img src="/blog/images/rendering-cause-me-to-exist/document_image_rId15.png" width="380" />
<img src="/blog/images/rendering-cause-me-to-exist/document_image_rId16.png" width="380" />

可见，任务组织结构与实际节点的物理/逻辑拓扑关系是息息相关的，任何组织结构都是服务于节点间更好地进行沟通交流，以及根节点对子节点有效的管理。所以，我们可以得出一个简单的结论：

1.  如果是抽象关联节点的话，可以用哈希表（如 Map）来对应单个窗口

2.  如果是具象关联节点的话，可以用树状结构（如 XML）来对应单个窗口

但这时有一个问题，窗口内加载的仍是 web 页面，本质是一个个 HTML 文件，而我们知道 HTML 并不能互相嵌套 ...... 虽然曾有过 HTML Imports，但其在 MDN docs 上已被标记为过时且不建议使用，我们仍然需要一个组合 HTML 的机制否则我们的页面文件随着需求的增加就会变成一个冗长的 entry 列表。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId17.png)

代码风格
--------

> "Imperative programming is like **how** you do something, and declarative programming is more like **what** you do."

我们知道代码风格有命令式和声明式两种，命令式编程意味着你告诉计算机每一步应该做什么，而声明式则更多关心计算机执行的最后结果，即告诉计算机要什么，怎么做到我不管。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId18.png)

上面两段代码估计早期前端开发都曾写过，第一个函数的作用是将数组的每一项乘以 2 并返回所得的新数组，第二个函数是求数组内所有项的和。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId19.png)

这一段代码在上一段代码基础上利用 Array.prototype 上的 map 和 reduce 高阶函数对迭代操作进行了封装，可以注意到函数的行数明显下降了，并且读者并不用关注具体迭代过程是怎么样的，也不用关注这些计算过程。

阅读代码的人只需要知道：

1.  将 arr 的每一项都映射到这一项取值的 2 倍

2.  设置初始值为 0，将 arr 的每一项加上初始值之后赋值给初始值

具体每一项是如何取值的，又是如何赋值的，写代码和阅读代码的人都不必关注。可能 map 和 reduce 的例子还不够充分，sort 这个方法是诠释声明式编程最好的例子。

```js
arr.sort((a, b) => {
  return a - b;
})
```

如上图，如果 `a - b < 0`，则将 a 放在 b 的左边，如果 `a - b === 0` 则保留两者位置不变，如果 `a - b > 0`，则将 a 放到 b 的右边，简单朴素地说明了排序的基本原则，而具体排序是用什么方式，时间复杂度和空间复杂度都不要用户去关注（如果想要进一步了解 Array.sort 的实现可参见[这篇 StackOverflow 的回答](https://stackoverflow.com/questions/234683/javascript-array-sort-implementation)）。

理清了上面这一点我们可以通过一个更进一步的例子来说明为什么声明式编程更适合 UI 开发？

![](/blog/images/rendering-cause-me-to-exist/document_image_rId21.png)

这个例子是一个初学 jQuery 的学徒都可以轻松写出的代码，逻辑也比较清晰，但做的事情已经开始混杂了：

-   highlight 这个 class 与文本的对应关系不明，需要更多上下文或者结合 HTML 考虑。

-   "Add Highlight" 被重复写了两遍，并且以 DOM 文本属性作为状态有点违背 Model View 分离的原则。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId22.png)

上图则是 React 中表达一个 Btn 组件的方式，可以看到 highlight 存在于 this.state 之上，成为脱离 UI 的状态，并且 onToggleHighlight 将调用关系绑定给 handleToggleHighlight，而 highlight 属性则是绑定给了 state 里的同名值。用通俗的话讲就是将数据状态和 UI 给串联起来了，盘活了。一旦数据状态发生变化就会自动映射到 UI 上，而 UI 上接受到事件也可以对数据做出相应改变，一个数据状态就对应了一个 UI 状态，童叟无欺。

这正是我们需要的组合 Web UI 的最佳形式。

窗口管理器
----------

综上所述，我们需要一个数据即 UI，惰性更新窗口样式以及生命周期能够被主进程统一管理的窗口管理器，它应该具有以下几个功能：

1.  提供包含组件及函数方法等多种创建销毁更新组件的方式

2.  将数据与 UI 绑定，无需一一手动设置窗口样式

3.  组件生则窗口生，组件卸载则窗口关闭

4.  主进程与窗口可以进行直接或间接的通讯，交换数据


Electron 及 React 相关 API 解析
===============================

![](/blog/images/rendering-cause-me-to-exist/document_image_rId23.png)

说好了不讲具体 API 的，摔！但不理解这些 API 就很难开发一个高效的窗口管理系统，遇到了具体问题也会找不着北，所以还是忍住睡意看一下会用到哪些神奇的
API 吧\~

BrowserWindow
-------------

首先是 Electron 的窗口类，这是我们与窗口外观打交道的主要途径了，在它上面有从窗口尺寸位置到标题栏样式乃至窗口内包括 JavaScript 和各种 Web API 是否开启等设置项，可以说就是一个定制版的小 Chrome。下面列出比较重要的几项：

-   frame: 窗口边框

-   titleBarStyle: 标题栏样式，包括 macOS 的红绿灯样式

-   webPreferences: web 相关设置

    -   nodeIntegration: 是否在内部浏览器开启 Node.js 环境

    -   preload: 预加载脚本

    -   enableRemoteModule: 启用远程模块，例如在浏览器中访问只属于主进程的 app 对象等

    -   **nativeWindowOpen**: 是否支持原生打开窗口，这个属性非常重要，是实现跨窗口通讯的基础，当前工作窗口必须设置为 true

webContents
-----------

webContent 是 BrowserWindow 下面具体管理 web 页面的一个对象，它同时也是一个 EventEmitter。我们只关心它上面关于创建窗口最重要的一个事件：**'new-window'**。

```js
const window = new BrowserWindow({
  webPreferences: {
      nativeWindowOpen: true,
  },
});

window.webContents.on('new-window', (event, url, frameName, disposition, windowOptions) => {
  if (frameName.startsWith('windowPortal')) {
    event.preventDefault()
    const options: BrowserWindowConstructorOptions = {
      ...windowOptions,
      frame: false,
      titleBarStyle: 'default',
      skipTaskbar: true,
      show: false,
      width: 0,
      height: 0,
    }
    const newWindow = new BrowserWindow(options)
    event.newGuest = newWindow
  }
})

```

上面这段代码的最终结果是将创建新窗口的过程的控制权交给 Electron 这边，比如设置无边框、默认标题栏样式、宽高都为 0 并且不显示，最后将这个完全为空的窗口交给 event.newGuest 交还给 window.opener。

React
-----

关于 React 的教程网上也是汗牛充栋了，我们这里同样弱水三千，只取一瓢。

```js
ReactDOM.createPortal(child, container)
```

[createPortal API](https://reactjs.org/docs/portals.html) 相信大家都用过，但大部分用途应该都只是将 React 组件渲染到 body 上变成模态框之类的，但如果我们**将整个桌面看做一个 body，而其中的某个窗口看做一个 div 容器**呢？答案是这样做可行！！！

我们可以**将 React 的组件直接 createPortal 到上面新生成的 window 里去**，这样就走通了 React 组件化开发并管理 Electron 窗口的关键链路。

窗口管理器实践
==============

我们已经拥有了在渲染进程里动态创建一个 Electron 窗口的全部知识，下面话不多说直接贴代码，手把手教你玩转 **Electron \'Portal\'**！

![](/blog/images/rendering-cause-me-to-exist/document_image_rId25.png)

React + Electron
----------------

我们需要拷贝样式至新窗口，在网上找到了如下一段代码，可以将外部样式表 link 和内联样式表 style 统统拷贝到新打开的 document 里。

```typescript
export function copyStyles(sourceDoc: Document, targetDoc: Document) {
    const documentFragment = sourceDoc.createDocumentFragment();
    Array.from(sourceDoc.styleSheets).forEach((styleSheet) => {
        // for <style> elements
        if (styleSheet.cssRules) {
            const newStyleEl = sourceDoc.createElement('style');

            Array.from(styleSheet.cssRules).forEach((cssRule) => {
                // write the text of each rule into the body of the style element
                newStyleEl.appendChild(sourceDoc.createTextNode(cssRule.cssText));
            });

            documentFragment.appendChild(newStyleEl);
        } else if (styleSheet.href) {
            // for <link> elements loading CSS from a URL
            const newLinkEl = sourceDoc.createElement('link');

            newLinkEl.rel = 'stylesheet';
            newLinkEl.href = styleSheet.href;
            documentFragment.appendChild(newLinkEl);
        }
    });
    targetDoc.head.appendChild(documentFragment);
}
```
下面是实现 Portal 的关键代码，关于其实现有以下几个技术要点：

-   通过 **forwardRef 暴露 getSize 等获取实际渲染元素的状态信息**方法，因为这些也是命令式的方法，正好契合了 useImperativeHandle 的名字，可以被父组件用 ref 来缓存后用于计算多个组件的位置关系。

-   在 useEffect 中返回关闭 window 的方法以便销毁窗口。

-   **封装 getWorkArea 方法以便适配多显示器**。

-   初次显示窗口时切记要**先 show 一个 0×0 的窗口，将它移动到指定位置再扩张尺寸使其显示**，如果 show 放在最后的话，在 macOS 全屏模式下会另起一个全屏窗口，这不是我们所需要的。

-   巧用 useEffect 的 dependency 监测 props 里位置信息的改变，自动映射到窗口上去。

-   灵活提供 mountNode 参数给子组件，以便一些原本挂载到 document.body 上的全局组件（如 Modal 和 Toast）渲染到指定位置，仿佛它们是挂载到了 desktop.body 上一样。

```jsx
const Portal = ({
    children,
    x,
    y,
    horizontalCenter,
    verticalCenter,
    inactive,
    alwaysOnTop,
}, ref) => {
    const [mountNode, setMountNode] = useState(null);
    const windowRef = useRef();
    useImperativeHandle(ref, () => ({
        getSize: () => {
            if (mountNode) {
                const { clientWidth, clientHeight } = mountNode;
                return [clientWidth, clientHeight];
            }
            return null;
        },
    }));
    // 创建窗口和 mountNode
    useEffect(() => {
        const div = document.createElement('div');
        div.style.display = 'inline-block';
        const win = window.open('about:blank', `${WINDOW_PORTAL}-${String(new Date().getTime())}`);
        if (!win.document) return;
        copyStyles(document, win.document);
        win.document.body.appendChild(div);
        windowRef.current = win;
        setMountNode(div);
        return () => {
            if (windowRef.current) {
                windowRef.current.close();
            }
        };
    }, []);
    
    // 获取工作窗口的位置尺寸
    const getWorkArea = useCallback(() => {
        if (windowRef.current) {
            const { remote } = windowRef.current.require('electron');
            return remote.screen.getDisplayNearestPoint(remote.screen.getCursorScreenPoint()).workArea;
        }
    }, [windowRef.current]);

    const getPosition = useCallback(() => {
        const workArea = getWorkArea();
        const xPos = (horizontalCenter ? (workArea.width / 2) - (mountNode.clientWidth / 2) : x) | 0;
        const yPos = (verticalCenter ? (workArea.height / 2) - (mountNode.clientHeight / 2) : y) | 0;
        return [workArea.x + xPos, workArea.y + yPos];
    }, [getWorkArea, x, y, horizontalCenter, verticalCenter]);

    // 初始化窗口
    useEffect(() => {
        if (mountNode && windowRef.current) {
            const win = windowRef.current;
            const { clientWidth, clientHeight } = mountNode;
            const { remote } = win.require('electron');
            const browserWindow = remote.getCurrentWindow();
            if (inactive) {
                browserWindow.showInactive();
            } else {
                browserWindow.show();
            }
            if (alwaysOnTop) {
                browserWindow.setAlwaysOnTop(true);
            }
            browserWindow.setPosition(...getPosition());
            browserWindow.setSize(clientWidth, clientHeight);
        }
    }, [mountNode, windowRef.current]);

    // 位移
    useEffect(() => {
        if (windowRef.current && mountNode) {
            const win = windowRef.current;
            const { remote } = win.require('electron');
            remote.getCurrentWindow().setPosition(...getPosition(), true);
        }
    }, [mountNode, windowRef.current, getPosition]);

    return mountNode && createPortal(
        children instanceof Function ? children({ mountNode }) : children,
        mountNode,
    );
}

export default forwardRef(Portal);
```

Svelte + Electron
-----------------

如果一种范式只有一种实现方式，那说明它还不够通用。为了证明这种管理 web 窗口的方式真的有意义，笔者尝试用 Svelte 实现了同样的功能。这里先向不了解Svelte 框架的同学安利一下这个神奇的框架，它一开始的口号是"消失的框架"，什么意思呢？它不像 React、Vue 之类的打包后还需要一个运行时的 lib 提供各种工具函数，比如 React.createElement 方法，它是完全的编译时框架，编译后只有组件代码即可运行。所以在只需要渲染一两个动态组件时，其体积和性能优势非常明显，尤其是配合其作者开发的 Rollup 时。由于 Electron 对其内 web 浏览器具有完全的操控权，我们可以放心地交付 ES6+ 的代码，不必过多 care 兼容性。下面给出试用 Svelte 写的 Portal 组件代码，感兴趣的同学可以尝试下哈，感受下别样的框架风情\~

```html
<div bind:this={portal} class="portal">
  <slot></slot>
</div>

<style>
  .portal { display: inline-block; }
</style>

<script context="module" lang="ts">
  function copyStyles(sourceDoc: Document, targetDoc: Document) {
    Array.from(sourceDoc.styleSheets).forEach(styleSheet => {
      if (styleSheet.cssRules) { // for <style> elements
        const newStyleEl = sourceDoc.createElement('style');

        Array.from(styleSheet.cssRules).forEach(cssRule => {
          // write the text of each rule into the body of the style element
          newStyleEl.appendChild(sourceDoc.createTextNode(cssRule.cssText));
        });

        targetDoc.head.appendChild(newStyleEl);
      } else if (styleSheet.href) { // for <link> elements loading CSS from a URL
        const newLinkEl = sourceDoc.createElement('link');

        newLinkEl.rel = 'stylesheet';
        newLinkEl.href = styleSheet.href;
        targetDoc.head.appendChild(newLinkEl);
      }
    });
  }
</script>

<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import type Electron from 'electron'

  type PortalWindow = Window & {
    require: (...args: any) => {
      remote: Electron.Remote
    }
  }
  let windowRef: PortalWindow
  let portal: HTMLDivElement
  
  onMount(() => {
    windowRef = window.open('about:blank', 'windowPortal') as unknown as PortalWindow
    copyStyles(document, windowRef.document)
    windowRef.document.body.appendChild(portal)

    const { clientWidth, clientHeight } = portal
    windowRef.requestAnimationFrame(() => {
      const { remote } = windowRef.require('electron')
      const win = remote.getCurrentWindow()
      const workArea = remote.screen.getDisplayNearestPoint(remote.screen.getCursorScreenPoint()).bounds
      win.showInactive();
      win.setPosition(workArea.x + 50, workArea.y + 50);
      win.setSize(clientWidth, clientHeight);
    })
  })
  
  onDestroy(() => {
    if (windowRef) {
      windowRef.close()
    }
  })
  
</script>
```

对 Svelte 和 Electron 结合感兴趣的同学还可以移步我的个人项目地址：[https://github.com/msyfls123/diablo2-wiki](https://github.com/msyfls123/diablo2-wiki)

"中央处理器"
------------

The last but not the least.

前面我们从一个带有 nativeWindowOpen 的 BrowserWindow 开始，经过 React.createPortal 创建新的 BrowserWindow 并将其交还给 React 渲染组件，并通过一系列的 effect 和 ref 方法使其得到了良好的管理，但实际上这个"窗口管理器"只存在渲染进程中，它与外界的通讯必须通过最开始那个 BrowserWindow 进行。我们需要将它封装成一个"中央处理器"，以便处理更加多样的调用。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId27.png)

这里不再赘述如何去用代码实现一个 WebUI 的类，因为它是全局唯一的，所以需要单例模式。在主进程入口，创建一个上面提到的用于承载各种窗口的 BrowserWindow，将这个 Window 通过 WebUI 的 init 方法注入到实例上，后续就可以通过公共的方法来调用这个中央处理器了。

```js
class WebUI {
    init(window) {
         this.window = window;
         this.window.webContents.on('ipc-message', this.handleIpcMessage);
    }
    showDialog(type, payload) {
        if (this.window) {
            this.window.webContents.send('show-dialog', type, payload);
        }
    }
    handleIpcMessage(event, channel, payload) {
        ...
    }
}
```

主进程中使用只需要直接调用单例的方法，如果需要暴露给渲染进程则可以如法炮制一个 ipcServer 转发来自其他渲染进程的消息。

意义
----

首先是声明式渲染 vs 命令式渲染，声明式责任在自己，命令式责任在对方。为啥呢？从 Electron 加载页面的方式就可以看出来了，加载一个 GitHub 的首页，只要网页一变，必然需要调用方处理相关的改动，且是被动处理。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId28.png)

改为声明式渲染则可以把主动权把握在自己手里。因为不存在 URL，所以无需考虑跳转之类的问题，仅需考虑最大程度复用组件，可做到比 SPA 更进一步。但这里存在一个小小的问题，没有 URL 也意味着相对路径引用的文件资源统统不可用了，比如 './images/a.png' 这样简单的引用图片的方式是无法做到的，只能变成绝对路径或者是 dataURL 内联，后续将进一步探索更合适的资源加载方案。

然后是这种后台常驻一个渲染服务进程看似和市面上常见的预加载 + 显示隐藏窗口提升性能的方案大同小异，其实不然，那种方式本质上还是多对多地维护"窗口缓存"，数量上去了一样很卡。但这套方案后台渲染进程恒为 1，做到了 O(1) 空间复杂度，并且在页面加载上完全无需考虑 DOM 解析和 JavaScript 加载（因为根本就不需要，Portal 的渲染都在已经加载完成的那个窗口进行），做到了最小化资源占用。像 Serverless 追求的也是快速热启动，既然我们已知用户所有的操作路径，又有最高效的窗口管理方式，何乐而不为呢。

还有一点是，通过 Portal 可以实现**任意渲染窗口不借助主进程独立创建并管理一个新的渲染窗口**，这一点给了 Electron 更多新的玩法，比如自定义右键菜单、常驻任务栏等都可以借此实现，直接脱离原 DOM 树，给予更多的 UI 操作自由和想象空间。

![](/blog/images/rendering-cause-me-to-exist/document_image_rId29.png)

注意事项
========

编译时与运行时区分
------------------

因为是跨端开发，所以一套代码会运行在多个平台上，需要区分编译时和运行时。

-   编译时可以确定的值应该使用 webpack.DefinePlugin 替换成常量，如 process.env.NODE_ENV，这些是一旦打包以后再也不会发生改变了。

-   运行时确定的值应该尽可能使用 os.platform 动态判断，原因是如果某一平台不支持某些属性，而开发时为了 debug 将功能开启，却忘了删 debug 开关，上线即造成这一平台的用户体验 crash 套餐。

参考
====

1.  [https://ui.dev/imperative-vs-declarative-programming/](https://ui.dev/imperative-vs-declarative-programming/)

2.  [https://www.electronjs.org/docs/api/browser-window](https://www.electronjs.org/docs/api/browser-window)

3.  [https://medium.com/hackernoon/using-a-react-16-portal-to-do-something-cool-2a2d627b0202](https://medium.com/hackernoon/using-a-react-16-portal-to-do-something-cool-2a2d627b0202)

![](/blog/images/rendering-cause-me-to-exist/document_image_rId33.png)
