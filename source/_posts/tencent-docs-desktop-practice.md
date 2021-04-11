---
title: Electron 开发实践
date: 2020-12-06 23:56:00
tags:
  - Electron
  - React
categories: web
thumbnail: images/tencent-docs-desktop-practice/document_image_rId9.png
disqusId: tencent-docs-desktop-practice
---

前言
----

首先介绍一下腾讯文档桌面端应用，以下简称桌面端，其通过嵌入 web 端腾讯文档应用并利用 Electron 封装本地系统接口的能力实现了独立分发的桌面端 App，兼顾了 macOS 和 Windows 两大操作系统，借此实现了腾讯文档的全端覆盖。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId9.png)

两大平台，一个月时间，我们是如何做到从技术选型到项目上线的呢？

这也太标题党了，跟市面上流传甚广的 21 天精通 C++ 简直一模一样。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId10.png)

我们都知道罗马不是一天建成的，如果把软件开发比作建一座城市的话，我们的的确确在一个月时间内造出了腾讯文档桌面端应用。肯定有人要问了，为何是一个月时间呢？为什么不是半个月，三个月亦或是半年时间？

事实上，这也是我们一开始进行技术选型和开发规划时所考虑的问题，因为选择了使用 JavaScript 及 Web 技术开发客户端，就注定了与 web 开发息息相关，包括迭代周期和开发顺序等方面，web 端腾讯文档的发布周期是一周两次发布，在一个月时间内差不多可以交付一系列完整的 API，这样可以做到桌面端与 web 端并行开发，最终整合成一个整体。如果等到半年时间才交付了桌面端，这时 web 端应用的 API 和 JSBridge 等接口规范都可能随之发生改变，容易造成返工甚至二次开发。

下面，我们将从四个方面介绍腾讯文档桌面端开发实践内容：技术选型、DevOps 工程化实践、混合式开发基础建设和跨端统一用户体验。

技术选型
--------

**竞技场耸立，罗马屹立不倒；竞技场倒塌，罗马倒塌；罗马倒塌，整个世界都会崩溃。 ------圣徒比德**

技术选型与古罗马的竞技的核心并无二致，都在于选优拔萃。而我们做技术选型的目的则不在于观赏，在于为了今后的开发找到正确的方向。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId11.png)

首先是总体的开发框架选择，结果是没有疑问的，我们选择了 Electron，实际上 NW.js 前身 node-webkit 和 Electron 的开发团队具有继承关系，而 NW.js 的特点是以 html 作为启动文件，在窗口里直接调用 Node.js，但我们知道能力越大责任越大，同时风险系数也越高。Electron 的主进程是跑在 Node.js 环境下的，可以无缝使用 Node.js 能力，而单独的窗口，即渲染进程，需要显式地打开开关才能使用，这样就一定程度上降低窗口中的页面滥用 Node.js 能力对系统造成危害或者频繁调用 Node.js 能力对性能产生影响的可能性。在插件、第三方包、社区生态和搜索热度上， Electron 都完胜于 NW.js，所以我们就放心地使用 Electron 进行开发吧。

### 社区优质实践

既然选定了 Electron 作为开发框架，先来看一看业界基于 Electron 的优质实践，首当其冲的是宇宙第一 IDE 的 Visual Studio 的 ...... 挂名弟弟 ...... Visual Studio Code，同样是微软出品，现已成为 web 开发事实上的标准 IDE。

然后是 Github 出品的 Atom 编辑器，这里插一句题外话，Electron 原名"Atom Shell"，后来随着框架的进一步抽离和沉淀，改名为"Electron"，这点非常符合国外技术圈觉得"工具不好用就发明一个趁手的工具"的思路。以及同样是 GitHub 出品的 **GitHub Desktop** 客户端，其他知名的基于 Electron 开发的桌面软件还有协作办公软件 **Slack**、 IM 即时通讯软件 **WhatsApp** 和 知识协作软件 **Notion** 等。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId12.png)

经过进一步调研，我们发现鹅厂内部也有一个基于 GitHub Desktop 定制的开源项目 **Trinity**，在与其作者进行沟通探讨后决定基于这两个项目作为脚手架，搭建腾讯文档客户端应用。在开发过程中，我们主要参考了上述两个项目的目录结构，比如都是双 package 模式，运行时代码和构建打包脚本分离，以及针对当前开发与线上构建环境特定的配置文件等等。

### 构建工具

我们做桌面端应用与 web 端应用差异最大的在于分发方式不同，web 端应用打开页面浏览即为分发成功，而桌面端应用则必须要下载到本地安装后使用，所以提升下载与安装体验对用户增长率提升至关重要。而提到安装包，就不得不提一下 **electron-builder**，它不仅做到了轻配置快速构建，也带给了桌面端应用非常多的额外能力，例如系统级别的文件关联，自动签名认证功能，制品管理和安装流程定制等，这些都与后面讲到的工程化建设和跨端体验一致性密切相关。通过一套配置，即可构建出包括自动更新、App Store 发布包在内的多个制品。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId13.png)

### 单测框架

如果说安装包是团队给用户的交付物的话，代码就是开发给团队的交付物。好的代码应该是可测试、可维护和承上启下的，要做到这些的最佳实践形式就是编写测试。而多种多样的测试里最方便快速的就是单元测试了，针对 Electron 的测试方式与常见 web 端测试不同，也可以认为是分别在 JSDOM 和 Node.js 两种环境下进行测试。经过调研，我们引入了 **@jest-runner/electron** 作为我们的单测框架，它的优势是一套配置，根据文件目录分发到两种执行环境下运行，也就是前面提到的主进程和渲染进程。并且具有代码无侵入，配置简单，速度飞快等特点。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId14.png)

从下面的图可以看到，运行全部 200 多个用例仅耗时不到 30s，方便开发时快速验证功能完备性。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId15.png)

DevOps 工程化实践
-----------------

![](/blog/images/tencent-docs-desktop-practice/document_image_rId16.png)

然后是我们的 DevOps 实践。为什么要协作呢？一个团队单打独斗不舒服吗？因为不同团队不同开发人员间基础能力有差异，倒不一定是体现在技术能力，而是技术侧重点不一样。DevOps 则提供了平台赋能，将各个能力项拉齐到统一水准。就像罗马士兵拥有了统一的装备，将人变成了战士。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId17.png)

同时要注意到的是选择协作工具时不仅仅要考虑当下，也要考虑系统的伸缩性，为未来的发展壮大留有余量。

这里是我们用到的部分公司平台基础能力，例如蓝盾流水线托管构建流程，七彩石实现配置下发，Sentry 做日志监控等等。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId18.png)

最终实现了"把控代码质量"，"托管构建过程"和"运行时保障"这三大目标。

把控代码质量：

静态代码分析、ESLint 扫描、圈复杂度扫描、重复代码扫描、单元测试、自动化测试

托管构建过程：

自动构建托管、自动签名认证、自动发布、自动转工单

运行时保障：

配置下发、灰度开关、自动化故障上报、日志监控、性能监控

混合式开发基础建设
------------------

前面讲到的都是外在条件，但文档内在是 web 项目。我们需要设想一下，对于一个 web 项目而言，包括 HTML、CSS、JavaScript 和其他媒体文件等等都是外部资源，如何建设好应用在于如何利用好外部资源。

如果说将 web 应用改造成桌面端应用是建一座城的话，那么将外部的能力引入到应用内的混合式开发基础建设就像是建造罗马水道一样。将水源从山脉中引流到城市里供人饮用、灌溉农田菜圃，再将污水输送出城市，完成城市的资源循环。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId19.png)

让我们先来看看这里都有哪些系统和外界网络提供的能力呢？比如**本地的原生数据库，文件系统里存储的数据文件，服务器的计算资源和静态文件 CDN** 等。

### 本地资源：数据库、文件 IO 和 JSBridge

![](/blog/images/tencent-docs-desktop-practice/document_image_rId20.png)

首先是本地的资源，我们经过反复比较，最终选择了最高效的 **LevelDB** 作为底层数据库实现，它是由 Google 开发的 KV 数据库，具有很高的随机写，顺序读/写性能，同时原生数据库也给于客户端程序更多的操控权。我们在其上封装了包括多库多用户管理，请求指令封装、分发日志上报等能力，通过 electron 提供的基于 scheme 的渲染进程 URL 请求拦截，以及主进程 webContents 通过 executeJavaScript 向渲染进程执行脚本，实现了 JSBridge，将包括上面提到的 LevelDB 以及 **electron-store** 等存储能力引入到了 web 端，同时通过 Node.js 自带的 fs 模块将文件 IO 能力提供给桌面端应用。

外部资源
--------

然后要提到的是外界网络能力，包括服务器和静态文件 CDN 等。

这两种能力都是通过 web 技术实现的，腾讯文档目前 web 上已经实现了有限的离线编辑能力，比如自动缓存增量编辑操作，进行版本冲突处理和提交等，在静态文件上正在开发基于 **PWA** 的离线缓存方案。同时因为是桌面端，前面提到的 LevelDB 是通过拷贝二进制可执行文件到发布资源中来实现分发的，所产生的问题是对不同系统需要分发不同的二进制文件，或带来工序上的复杂和计算资源的浪费，未来对类似需求可能考虑 **WebAssembly Interface** 来做跨端分发可执行文件。

跨端统一用户体验
----------------

![](/blog/images/tencent-docs-desktop-practice/document_image_rId21.png)

既然是应用开发，用户体验是重中之重。如何在跨端情况下保证用户体验的统一性，需要我们制定一系列的规范，像同时期的罗马和秦帝国一样，立国之初就统一了包括法典、文字度量衡等规范，这大大地有利于内部进行交流协作，在处理差异性问题时有据可循。

### 弹窗

![](/blog/images/tencent-docs-desktop-practice/document_image_rId22.png)

以简单的一个系统设置弹窗为例，在设计规范中 Windows 和 macOS 上样式实现是不一致的，弹框的边框则是都采用了系统样式，但 Windows 同时需要定义标题和关闭按钮，而 macOS 则沿用了系统的红绿灯样式，同时考虑到代码一致性手动实现了标题部分。在内容部分，macOS 考虑到与系统 UI 一致，手动实现了弹窗内 tab 切换，主体内容则是基于 **DUI** 实现两端共用。这里带来的问题是，开发往往只会在一台机器上开发，如果开发需要每次都打包分发到另一个平台看效果也太麻烦了，可以通过加开关的形式进行调试。在完成对弹窗的封装以后，我们可以基于 BrowserWindow 和 React 对其进行统一的生命周期管理，保证同一类型弹窗只显示一个。

### 安装与升级

![](/blog/images/tencent-docs-desktop-practice/document_image_rId23.png)

![](/blog/images/tencent-docs-desktop-practice/document_image_rId24.png)

然后是安装与升级，Windows 是覆盖安装，mac 是拖拽安装，Windows 可自定义安装前后行为，例如安装完写入注册表，卸载后清理用户数据，mac 版则利用了系统的静默升级。而 **electron-updater** 则让两者都实现了自动下载并一键升级的功能。

### 更多桌面平台特性

我们在开发过程中还遇到了更多的桌面特性，比较顺利的是 Electron 和 electron-builder 帮助实现了非常多的系统功能如：**文件打开方式关联，QQ 消息链接自动打开 App 并打开文档，监测剪贴板链接自动打开在线文档**等等。而其中不方便实现的则是全局的 Web UI 容器，因为 Electron 自带的系统 UI 控件非常少，也大多不符合 UI 规范，需要自定义 UI 界面只能通过打开渲染窗口并加载 HTML 文件的方式。如图所示的全局 toast 在项目中应用非常广泛，如何将其与 React DUI 组件进行共用呢？

![](/blog/images/tencent-docs-desktop-practice/document_image_rId25.png)

#### 命令式创建 Web UI 组件

![](/blog/images/tencent-docs-desktop-practice/document_image_rId26.png)

首先要明确的是我们肯定是通过打开 BrowserWindow 窗口加载 html 来展示 UI。一种比较常见的思路是命令式创建 web UI 组件，比如创建 DialogManager 来统一管理多个 dialog，但这里的问题是有多少个 dialog 就需要多少个 dialog.html 文件，因为它们都是编译时就确定的，即使通过 url 分发，也必须至少创建一个 dialog 文件才能打开窗口。

![](/blog/images/tencent-docs-desktop-practice/document_image_rId27.png)

#### 声明式创建 Web UI 组件

![](/blog/images/tencent-docs-desktop-practice/document_image_rId28.png)

React 提供了声明式创建组件的方式，我们可否通过其创建组件呢？通过调研，我们发现了 React 的 createPortal 函数是可以将 React 组件挂载到新创建的 window 里去的，那么我们只需要定制新创建 window 的参数就可以实现无边框窗口加载 React DUI 组件的功能。即实现了利用 React 管理窗口的生命周期。

-   **window.open** 并通过 Electron 拦截定义新创建 Chromium 窗口

-   **React.createPortal** 将组件（如 <Snackbar/>）

挂载到新创建的窗口内

-   利用 **React** 管理窗口的生命周期

![](/blog/images/tencent-docs-desktop-practice/document_image_rId29.png)

这样可以把唤起 Web UI 的职责交给常驻后台的隐藏渲染窗口 webComponent，在其中自定义组合各种各样丰富的 React DUI，通过 React 进行统一管理，后续可以几乎零边际成本增添新组件，同时在组件与进程频繁交互时也方便通过组件树找出对应关系进行维护。

**注：本文为笔者于第一届 QQ Tech 技术周作主题演讲《腾讯文档桌面端跨平台端开发实践》演讲稿整理而来。**
