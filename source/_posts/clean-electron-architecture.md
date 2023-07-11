---
title: Electron 应用整洁架构
date: 2023-06-19 14:20:00
tags: [App, Electron]
categories: app
thumbnail: https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXptbHFpcTZmaHFvODFtc3hqMzd5dDFwcWJtMDF1Z2ptcG84cGd4dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/h2NxCschQ81ltiL9HV/giphy.gif
disqusId: clean-electron-architecture
---

- [框架特性](#框架特性)
  - [依赖反转](#依赖反转)
  - [路由模式](#路由模式)
    - [装饰器（Decorator）](#装饰器decorator)
      - [HTTP 类](#http-类)
      - [自定义类](#自定义类)
    - [中间件（Middleware）](#中间件middleware)
  - [数据管理](#数据管理)
    - [简单 JSON 内容](#简单-json-内容)
    - [数据库](#数据库)
  - [会话隔离](#会话隔离)
    - [Session 持久化](#session-持久化)
    - [Session 事件](#session-事件)
- [业务特性](#业务特性)
  - [插件机制](#插件机制)
    - [内置插件](#内置插件)
    - [第三方插件](#第三方插件)
    - [插件依赖](#插件依赖)
  - [窗口 UI](#窗口-ui)
    - [KISS](#kiss)
    - [命令式修改](#命令式修改)
    - [中心化状态](#中心化状态)

一个好的架构是具有良好用户体验的 App 的必备素质，反而言之，一个差劲体验的 App 一定是架构混乱甚至没有架构的。一坨一坨互相依赖，单例漫天飞的代码，足以让任何一个开发满嘴跑 F**K。

什么是好的架构？众说纷纭，但至少类似洋葱模型的中心化组织形式比较符合心智模型。设想一下，每天睁开眼睛，第一件映入脑海的事可能是下列这些问题：

- 我是谁？我是一个程序员，我每天需要写代码赚钱……
- 这是哪？这是我家，租来的房子，离公司骑车 15 分钟，所以我得赶紧起床了
- 看看今天有啥新鲜事？拿起手机，把通知和各个 IM 应用点一遍
- 开始新的一天吧？打开水龙头洗漱，出门扔垃圾，扫共享单车去上班

而这些想法和行为正好对应了 Clean Architecture 里的 **Entities**、**Use Cases**、**Interface Adapters**、**Frameworks and Drivers**。我是实体，我每天根据情景有要做的事，我接受的信息有原始的自然信息（如鸟鸣虫叫）也有经过加工的人工信息（明星八卦、国际局势），最后和社会的水电交通等公共设施打交道。任何一种好的架构都应该符合普通人的基本认知才能绵延不息。

![Clean Architecture](/blog/images/clean-electron-architecture/16-39-09.png)

光说不练假把式，同样以 Electron 框架为例子。为啥总要举它作为栗子呢？因为 Electron 天生具有 C/S 架构，同时又是客户端应用，可以说在单个体上参杂了前端、后端和客户端三种不同关注点的开发视角，所以大多数 Electron 应用往往都是一个大窗口套一个 web，主进程简单做了个数据层就完事。这种情况下既不需要架构，也不需要优化，只需要把代码堆积起来就完事了。

但时间一长，各种问题就粗来了：
- class 没有统一初始化的地方，基本是直接 export new 或者单例模式
- 功能堆砌纯线性组织，一条长长的 main 函数把所有的功能都包含了
- preload 脚本需要 ipcRenderer.sendSync 通讯，同时 ipc 可能遇到跨 frame 通讯问题
- 单元测试困难，Electron 模块随处可见，需要多次 mock

没办法，不想脱裤跑路就重构呗。天不生 Nest.js，Electron 架构万古如长夜！经过近两年的苦苦摸索，在尝试了至少三种框架的基础上，终于提炼出了用 Nest.js 框架良好组织 Electron 应用的方法，且听我缓缓道来。

# 框架特性

每个框架都会把自己的杀手锏特性都排在官网最前面，比如 React 是组件式，Vue 是渐进式，Angular 是让你有信心交付 web app，Svelte 是消失的框架（无运行时 lib），而 Nest.js 几乎是把渐进式、可靠性、扩展性等等都包圆了。实际使用下来，可以说是跟 Angular 一样的总包框架，可以管理一个 App 从启动到关闭整个生命周期。同时它也借鉴了 Angular 很多的创新点，比如依赖反转注入，装饰器模块，五花八门的中继器，以及强大的可扩展性，这也是我们得以将其应用到 Electron 项目的关键。

对于纯命令行程序，我们可以直接一个函数从头执行到尾再退出 App，而对于任何 GUI 程序，通常的解决方案都是以事件循环阻塞整个进程直至收到退出 SIGNAL，但这带来一个问题，如果进程被阻塞了，后续所有操作都无法得到响应。Node.js 的异步事件循环完美地解决了这个问题，在此基础上设计了基于消息的一系列运行机制，很好地处理了成千上万的请求。既然作为服务器都顶得住，那单机应用区区几个请求的并发更是不在话下。

我们设想这样一个应用：
- 它具有处理自定义请求事件的能力
- 它支持中继并更改请求，也就是中间件的能力
- 它可以分析模块依赖并自动按序加载
- 它可以加载外部网页并与之通讯，同时也可以与宿主机的其他应用通讯

这是一个跨端的带界面的服务器。

## 依赖反转

![依赖反转](/blog/images/clean-electron-architecture/17-06-06.png)

这个特性可太重要了，可以说没有它就没有后续所有的模块设计。每个上古项目都有一堆不明所以的头文件或者配置文件，或者不知从哪引入的构建脚本，又或是一串 token 或密码，这些东西都应该被管理起来。

我们需要一个简单的心智模型，所有第三方内容都是输入资源，不管是代码还是配置，webpack 就是把所有的内容都当作资源对待。但 webpack 在打包时也支持给 import 加参数，比如指定图片内嵌为 base64 的最大体积，支持输入参数也是我们的目标之一。

同时，webpack 也支持拆分模块，延迟至使用时加载，这一点更是杀手锏。因为客户端的生命周期一般比网页要长得多，但对体积相对不敏感，使用一些 preload 技术可以不在影响用户正常使用的情况下在快速响应页面和保证功能随时可用间达到平衡。

模块存在的意义就是复用，虽然 web 上各种框架的教条都是不要复用组件，多用组合而不是嵌套继承，但实际上数据和 UI 就是不同的组织形式。我们可以精确定义每个模块的使用究竟是全局唯一，每次实例化使用一个新的，还是每次调用就直接新建一个。

![](/blog/images/clean-electron-architecture/16-56-47.png)

参考：
- [Custom providers](https://docs.nestjs.com/fundamentals/custom-providers)
- [Injection scopes](https://docs.nestjs.com/fundamentals/injection-scopes)

## 路由模式

组件是前端的组织方式，而路由则是后端的组织方式。

不管是 HTTP 还是 IPC，甚至系统菜单，都可以作为路由端点。我们也可以用自带的 EventEmitter 在应用间不同路由间穿梭。

### 装饰器（Decorator）

#### HTTP 类

- 路由：@Get / @Post / @Sse
- 参数：@Param / @Header
- 响应：@Render

#### 自定义类

- 获取参数：@WebContents
- 装饰路由：@IpcHandle, @IpcOn

### 中间件（Middleware）

https://stackoverflow.com/questions/54863655/whats-the-difference-between-interceptor-vs-middleware-vs-filter-in-nest-js

![](/blog/images/clean-electron-architecture/17-22S-56.png)

## 数据管理

### 简单 JSON 内容

### 数据库

## 会话隔离


### Session 持久化

### Session 事件

例如自定义下载行为，针对特定协议进行重定向。

# 业务特性

## 插件机制

### 内置插件

### 第三方插件

### 插件依赖

## 窗口 UI

### KISS

不要动原生对象！\
不要动原生对象！\
不要动原生对象！

重要的事说三遍。

### 命令式修改

### 中心化状态
