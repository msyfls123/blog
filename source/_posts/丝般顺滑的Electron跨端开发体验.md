---
title: 丝般顺滑的 Electron 跨端开发体验
date: 2020-11-02 23:30:01
tags:
  - Electron
  - electron-builder
categories: web
thumbnail: /images/electron-build.png
disqusId: electron-build
---
简介
====

减化软件开发复杂度的核心奥义是分层与抽象，汇编语言抹平了不同 CPU 实现的差异，做到了"中央处理器"的抽象，而操作系统则是抽象了各种计算机硬件，对应用程序暴露了系统层的接口，让应用程序不需要一对一地对接硬件。

回到这篇文章的标题，目前主流的桌面端主要为 Windows、macOS 和 Linux 三种，考虑覆盖人群，实际做到覆盖前两端即可覆盖绝大多数用户。或许有同学就要问了，都 2020 年了还有必要开发桌面端应用吗？？Web 它不香吗？答案是：香，但它还不够香。网页因为各种安全方面的限制，现在还无法很好地和系统进行交互，比如文件读写（实际已经有了 Native File System [[https://web.dev/file-system-access/](https://web.dev/file-system-access/)）和更改各种系统配置的能力，这些往往是处于安全和兼容性的考虑。如果想强行在 Web 里做到这些部分也不是不可以，但相对普通 Web 开发，成本就显得过高了点，这点先按下不表。
 俗话讲"酒香不怕巷子深"，Web 在富 UI 应用的场景下已经一枝独秀遥遥领先于其他 GUI 方案，像早期 Qt、GTK 等跨端 GUI 开发方案已经几乎绝迹（PyQt 还过得比较滋润，主要是 Python 胶水语言的特性编写简单界面比较灵活），随着移动端浪潮的袭来以及 Node.js 的崛起，更多开发者选择 JavaScript （包括附属于其上的语言和框架）进行跨桌面、移动端和 Web 的混合开发，像 Ionic、Cordova(PhoneGap) 等框架在 2011 年以后如雨后春笋般冒了出来，当然随着 Facebook 和 Google 发布 React Native 和 Flutter，广大 Web 开发者终于可以喘口气，看到了只学一种框架就用上五年的曙光。

移动端的竞争如此激烈，但桌面端则目前只有一个王者，那就是 Electron。我们来看看它究竟是什么?

![](/blog/images/electron-build/document_image_rId10.png)

这个问题的答案很简单，Electron 就是 Chromium（Chrome 内核）、Node.js 和系统原生 API 的结合。它做的事情很简单，整个应用跑在一个 main process（主进程） 上，需要提供 GUI 界面时则创建一个 renderer process（渲染进程）去开启一个 Chromium 里的 BrowserWindow/BrowserView，实际就像是 Chrome 的一个窗口或者 Tab 页一样，而其中展示的既可以是本地网页也可以是线上网页，主进程和渲染进程间通过 IPC 进行通讯，主进程可以自由地调用 Electron 提供的系统 API 以及 Node.js 模块，可以控制其所辖渲染进程的生命周期。

![](/blog/images/electron-build/document_image_rId11.png)
Electron 做到了系统进程和展示界面的分离，类似于 Chrome或小程序的实现，这样的分层有利于**多窗口应用**的开发，天然地形成了 **MVC架构**。这里仅对其工作原理做大致介绍，并不会详尽阐述如何启动一个 Electron App 乃至创建 BrowserWindow 并与之通讯等，相反，本系列文章将着重于介绍适合 Web 开发者在编码之余需要关注的**代码层次、测试、构建发布**相关内容，以「腾讯文档桌面端」开发过程作为示例，阅读完本系列将使读者初步了解一个 Electron 从开发到上线所需经历的常见流程。

在这里，笔者将着重介绍与读者探讨以下几个 Electron 开发相关方面的激动人心的主题：

-   我只有一台 MacBook，可以用 Electron 开发出适用于其他平台的 App 吗？

-   我需要为不同平台分发不同的版本吗？它们的依赖关系如何？

-   如何让用户觉得我开发的应用是可信任的和被稳定维护的？

-   我想让用户在"更多场景"下使用我的应用，我该怎么做？

-   我是一个 Web 开发者，Electron 看起来是 C/S 架构，应该如何设计消息传递机制？

-   用 Electron 开发的 App 可测试性如何，可以在同一套测试配置下运行吗？

不用担心，以上问题的回答都是"Yes，Electron 都能做到"。下面我们就进入第一个主题吧，如何构建你的 Electron 应用。

打包应用
========

首先我们假定你已经创建了一个 main.js 的文件，同时创建了一个名叫 renderer.html 的文件用于展示渲染内容，这时候你就可以直接将这个文件夹压缩后发给你的用户了，请用 Terminal 切换到该文件夹下，键入 `electron .` 并回车即可运行应用，全文完！撒花 ✿✿ヽ(°▽°)ノ✿

当然不是这样简单，我们需要交付的是一个完整的独立运行的 App，至少我们得把代码和 Electron 的可执行文件都打包进去。但首先第一步是，既然用户是下载了一个大几十 M 的 App，我们是不是可以直接在 App 里 serve 源码了？简而言之，是的，你可以将你的源文件连同 node_modules 一起发给用户，但是 ------

![](/blog/images/electron-build/document_image_rId12.png)

巨巨...... 怕了怕了，并且直接 server 源代码也可能会将一些敏感信息或者你写得不咋滴的代码直接暴露给用户，带来不必要的安全风险。这里介绍一下使用 Webpack 和 Rollup 打包 Electron App 的关键代码：

使用 Webpack 打包
-----------------

用 Webpack 打包还是相对简单的，只需要将 config.target 设置成 'electron-main' 或者 'electron-renderer' 即可
 ```js
// webpack.config.js
const config = {
    target: 'electron-main' | 'electron-renderer'
}
```

其原理是对不仅包括 Node.js 原生模块，同时也包括 Electron 相关模块都不打包了，交给 Electron 自己在运行时解决依赖，见链接：[[https://github.com/webpack/webpack/blob/3610012f42e4ba9cf80a0e8a58a165b5121d8582/lib/electron/ElectronTargetPlugin.js\#L24-L64]{.ul}](https://github.com/webpack/webpack/blob/3610012f42e4ba9cf80a0e8a58a165b5121d8582/lib/electron/ElectronTargetPlugin.js#L24-L64)

使用 Rollup 打包
----------------

既然实际项目中都是拿 Webpack 打包的，何不尝试下新的方式呢，Rollup 作为打包 npm 模块的最佳工具，想必也是能打包 Electron 应用的吧...... 但 Rollup 就没有这么简便的配置方式了，需要做一番小小的手脚：

```js
// rollup.config.js
export default [
    {
        input: 'src/main-process/main.ts',
        output: {
            format: 'cjs',
        },
        external: ['electron'],
    },
    {
        input: 'src/renderer/index.tsx',
        output: {
            format: 'iife',
            globals: {
                electron: "require('electron')",
            },
        },
        external: ['electron'],
    },
]
```

解释一下，format 为 'cjs' 或 'iife' 是表明适用于 Node.js 环境的 commonjs 或者是浏览器环境的立即执行格式，而他们同样都需要将 electron 设置为外部依赖，同时在渲染进程里还需要指定 `electron = require('electron');`。等等，这里竟然在 window 下直接 require？？？是的，通过创建 BrowserWindow 时设置 `nodeIntergration: true` 即可在打开的网页里使用 Node.js 的各种功能，但能力越大所承担的风险也越大，所以是得禁止给在线网页开启这个属性的。

![](/blog/images/electron-build/document_image_rId14.png)

这里还有个类似的属性 `enableRemoteModule`。 它的含义是是否开启远程模块，这样就能直接从渲染进程调用主进程的一些东西，但这样做同样有包括[[性能损耗在内的一系列问题]{.ul}](https://medium.com/@nornagon/electrons-remote-module-considered-harmful-70d69500f31)，所以 Electron 10.x 以后已经默认关闭了这个开关，手动开启同样需要慎重。

![](/blog/images/electron-build/document_image_rId16.png)

不进行打包的依赖
----------------

虽然 node_modules 确实很大，但因为是桌面应用，总有些库或者包里的内容是不需要或者说没法去打包的，这时候就要将他们拷贝到生成文件夹里去，比如项目里用到的 levelDB 针对 Windows 32 位和 64 位以及 macOS 都有不同的预编译文件，这时将它们直接拷贝过去就好啦。

构建完成后，我们的应用已经有了直接 `electron .` 跑起来的能力，离可发布的 MVP 只差打包成可执行文件这一步了！

构建可执行文件
==============

将代码打包成可执行文件同样需要市面上的第三方解决方案，有 electron-packager 和 electron-builder 可选，实际比较下来 electron-builder 提供了包括安装和更新在内的一系列流程，体验极好，所以只以其作为构建工具作介绍。

electron-builder 也是一个对开发代码无侵入的打包构建工具，它只需要指定好各种路径以及需要构建的目标配置即可一键完成打包构建、签名、认证等一系列流程。

electron-builder 是具有同时打包出多个平台 App 的能力的，具体在 Mac 上是通过 Wine 这个兼容层来实现的，Wine 是 Wine Is Not an Emulator 的缩写，从名字里强调它不是一个模拟器，它是对 Windows API 的抽象。打包后的应用与 Windows 上构建的应用没有区别，但构建时的 process.platform 会被锁在 'darwin' 即 macOS，这是个看起来微不足道，但实则遇到会让人抓耳挠腮的情形，后面会详细展开。

![](/blog/images/electron-build/document_image_rId20.png)

但 Windows 就没有这么好运气了，笔者并没有找到可以在 Windows 上打包出 macOS 可用执行文件的方式，所以上面的同时出两个平台可执行文件的方式亲测还是只能给 macOS 用的。

![](/blog/images/electron-build/document_image_rId21.png)

自动升级
========

electron-builder 提供了生成自动升级文件的能力，配置好对应平台的 publish 字段后会同步生成升级 yml 文件，将它们和安装包一起上传到 CDN 并配置 electron-updater 即可以实现自动升级。![](/blog/images/electron-build/document_image_rId22.png)

配置 electron-updater 需要注意以下三点：

1.  electron-builder 会在应用打包时偷偷塞进去一个 app-update.yml，本地开发时没有读到相似的开发配置会无法调试，需要手动复制一份并重命名成 dev-app-update.yml 放到开发目录下才能继续升级，但最后一定会自动升级失败，因为开发时的代码没有签名。

2.  electron-updater 会去读 package.json 文件的 version 字段，如果是主目录和 App 目录不相同的开发模式的话，需要手动指定 autoUpdater.currentVersion。同样需要手动指定的还有 autoUpdater.channel，这里有个 bug，mac 虽然用的是 `latest-mac.yml` 文件但 channel 却要设置成 `latest`，electron-updater 似乎会自动补上 `-mac` 字样。

3.  与 macOS 静默升级不同，nsis 包的 Windows 升级动静很大，所以如果用户不是想立马升级的话最好将 autoInstallOnQuit 设置成 false，否则用户就会惊奇地发现哪怕取消了自动安装还是在退出后立马更新了。

```js
autoUpdater.currentVersion = APP_VERSION;
autoUpdater.autoInstallOnAppQuit = false;
autoUpdater.channel = os.platform() === 'darwin' ? 'latest' : 'latest-win32';
```
文件关联
========

在移动端 App 大杀四方，Web 大行其道，小程序蠢蠢欲动的当下，一个桌面应用的生存空间是极其狭小的，通常都不需要什么竞争对手，可能自身产品的其他端就把自己给分流耗竭而亡了......我们提到桌面端，不得不提的就是文件系统了，如果 iPhone & Android 都有便捷好用的文件管理系统，那感觉桌面端的黄昏真的就来到了。

但这里首先还是看一看 electron-builder 可以给我们带来什么能力吧。

系统关联文件类型
----------------

这就是文件右键菜单里的打开方式了，设置方式也很简单，通过设置 electron-builder config 里的 fileAssocaitions 字段即可。
```js
const config = {
    fileAssociations: {
        ext: ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf', 'txt', 'csv'],
    }
}
```

![](/blog/images/electron-build/document_image_rId23.png)

![](/blog/images/electron-build/document_image_rId24.png)

QQ AIO 结构化消息打开应用（Windows）
------------------------------------

QQ 通过唤起写入注册表里的腾讯文档地址来打开腾讯文档 App 同时带上了 --url=https://docs.qq.com/xxx 的参数，继而打开对应的文档。

electron-builder 配置 nsis.include 参数带上 nsh 脚本，写入如下设置（注：该配置并不完全）即可帮助 QQ 定位已安装的腾讯文档应用。

```nsis
WriteRegStr HKLM "SOFTWARE\Tencent\TencentDocs" "Install" "$INSTDIR"
```

NSIS 脚本还可以做很多事情，比如卸载 App 后清理数据或者检查是否安装了老版本等，具体可参见其官方文档。

```nsis
Delete "$APPDATA\TDAppDesktop\*.*"
RMDIR /r "$APPDATA\TDAppDesktop"
```

在 QQ 发起消息后，文档这边需要支持解析所带的参数，从进程参数中解出相关信息再打开对应 Tab 页面。

```js
const args = process.argv;
if (argv.length > 1) {
    handleCommandArguments(argv.slice(1));
}
```

小结
====

本文简述了通过 Electron 构建应用过程中采用不同方式和配置打包文件、使用 electron-builder 构建可执行文件，同时用其提供的功能实现自动升级与文件关联，完成了在单个平台（macOS）开发并构建出跨端应用的任务。笔者接触 Electron 开发时间较短，行文中多是开发中所见所闻所感，如有错误纰漏之处，还望读者不吝包涵指正。后续文章将介绍在跨端开发中处理兼容性时遇到的问题，以及如何优雅地在产品设计和功能间进行取舍。
