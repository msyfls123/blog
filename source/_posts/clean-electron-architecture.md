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
    - [跨进程共享数据（preload）](#跨进程共享数据preload)
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
- [原则](#原则)
  - [防呆设计](#防呆设计)
  - [保持功能独立](#保持功能独立)

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

我们需要一个简单的心智模型，所有第三方内容都是输入资源，不管是代码还是配置，webpack 就是把所有的内容都当作资源对待。但 webpack 在打包时也支持给 import 加参数，比如指定图片内嵌为 base64 的最大体积。**支持输入参数**也是我们的模块建设目标之一。

同时，webpack 也支持拆分模块，**延迟至使用时加载**，这一点更是杀手锏。因为客户端的生命周期一般比网页要长得多，但对体积相对不敏感，使用一些 preload 技术可以不在影响用户正常使用的情况下在快速响应页面和保证功能随时可用间达到平衡。使用 Nest.js 的 `useFactory` 可以轻松将模块变为 `import(...)` 延迟加载并且在使用时只需从 constructor 进行注入，避免全局的 lazy import 污染。

模块存在的意义就是复用，虽然 web 上各种框架的教条都是不要复用组件，多用组合而不是嵌套继承，但实际上数据和 UI 就是不同的组织形式。我们可以精确定义每个模块的使用究竟是全局唯一，**每次实例化**使用一个新的，还是**每次调用**就直接新建一个。

![](/blog/images/clean-electron-architecture/16-56-47.png)

参考：
- [Custom providers](https://docs.nestjs.com/fundamentals/custom-providers)
- [Injection scopes](https://docs.nestjs.com/fundamentals/injection-scopes)

## 路由模式

组件是前端的组织方式，而路由则是后端的组织方式。

路由模式和消息监听机制很像，区别是路由是编译时即唯一确定的，而消息监听则往往是运行时动态注册。这里动态注册的消息机制带来了两个严重的问题：

- 首次加载时无法确定消息处理的顺序，往往需要等待一个消息监听器绑定之后再触发事件，要是没监听上就丢失了。
- 消息监听可以放在全局，或者跟随模块。前者污染了全局环境，后者层层嵌套之后难以确认依赖层级。

既然消息机制具有如此多的不稳定性，我们还是更倾向于跟服务器一样一次性注册所有路由。

不管是 HTTP 还是 IPC，甚至系统菜单，都可以作为路由端点。我们也可以用自带的 EventEmitter 在应用间不同路由间穿梭。下面这段代码就演示了一个简单的创建或更新对象的路由端点，可以看到路由的组件由装饰器标识，在函数参数里通过装饰器来捕获不同的参数，经过 `this` 上的数据库及 logger 对象，完成了数据的持久化和日志功能，最后把创建结果以 JSON 格式返回。

```typescript
@Post('/:id')
public async upsert(
  @Param('id') id: string,
  @Param('name') name: string
  @WebContents() webContents: WebContents,
) {
  this.logger.log(`Got message from webContents-${webContents?.id}`);
  const db = this.database;
  try {
    const doc = await db.get(id);
    return db.put({
      _id: id,
      _rev: doc._rev,
      name,
    });
  } catch (err) {
    this.logger.error(err);
    return db.put({
      _id: id,
      name,
    });
  }
}
```

### 装饰器（Decorator）

大家肯定也看到上面代码中四个大大的 `@`，这就是 JavaScript 中的装饰器语法。只是可惜的是 parameter decorator 最终没有进入 stage 3，也就意味着 Typescript 以后肯定会对这个调用方式进行更改，不过这件事还没有尘埃落定，加上这么大一个框架，根本不用担心。

让我们庖丁解牛一下“装饰器”究竟是个什么东西？装饰器的重点自然是在装饰上，也就是给被装饰的类、函数方法、参数等实现一个不同的外观，从而在程序运行起来时以指定的方式调用/生成被装饰的对象。这句话读起来还是很别扭，实际上装饰器是元编程的一种形式，也就是不改变代码结构的前提下给代码走不同路径的方式，可以理解成打补丁。

举几个例子，比如常见的 debounce 和 throttle 方法，它们接受一个函数，返回防抖和节流后的函数版本。

```javascript

function debounce(fn, timeout) {
  let timer = null
  return function(...args) {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, timeout)
  }
}

function log(data) {
  console.log(data)
}

class Logger {
  debounceLog = debounce(log, 1000)
}
```
无装饰器版本

```javascript

const debounce = (timeout: number) => (value: any, context: ClassMethodDecoratorContext<any>) => {
  let timer: undefined | NodeJS.Timeout = undefined
  context.addInitializer(function () {
     const fn = this[context.name]
     this[context.name] = (...args: any[]) => {
      if (timer) {
          clearTimeout(timer)
          timer = undefined
        }
        timer = setTimeout(() => {
          fn.apply(this, args)
          timer = undefined
        }, timeout)
     };
  });
}

class Logger {
  @debounce(1000)
  log(data: any) {
    console.log(data)
  }
}
```
装饰器版本

可以看到装饰器版本将业务逻辑内聚成了一个函数，而不是必须要用函数套函数的方式。让代码分层有助于隔离关注部分，我们通常会把路由的执行逻辑和路由的路径给绑定在一起，但又不想变成每个路由端点都是一个类，这就是装饰器常见的应用场景了。

#### HTTP 类

Nest.js 自带了很多 HTTP 服务的默认装饰器，对于绝大多数场景而言已经足够了。支持 HTTP 不同的请求类型，从请求中获取数据，并最终将内容用模版拼合并返回。

- 路由：@Get / @Post / @Sse
- 参数：@Param / @Header
- 响应：@Render

#### 自定义类

- 获取参数：@WebContents
- 装饰路由：@IpcHandle, @IpcOn

### 中间件（Middleware）

https://stackoverflow.com/questions/54863655/whats-the-difference-between-interceptor-vs-middleware-vs-filter-in-nest-js

![](/blog/images/clean-electron-architecture/17-22-56.png)

## 数据管理

### 简单 JSON 内容

### 数据库

### 跨进程共享数据（preload）

## 会话隔离


### Session 持久化

### Session 事件

例如自定义下载行为，针对特定协议进行重定向。

# 业务特性

## 插件机制

### 内置插件

### 第三方插件

### 插件依赖

插件一多，就跟模块一样存在互相依赖的问题。内置插件还好说，毕竟在同一个仓库里维护，第三方插件完全是脱离控制的存在。

一种简单的办法，插件具有版本，互相引用需要带版本号进行关联，但很明显这是种不经济的做法。况且为了不强依赖于某个版本，大家都会心照不宣地做成向上兼容模式，这时候一个实习生发了 x.x.n+1 的版本，但实际废除了一个重要 API，画面太美不敢想象。事实上没有一颗避免循环版本依赖的银弹，业界通常做法是深度遍历之后在遍历到一定层数，返回循环依赖的报错。

这时候就不得不提一种脱离 RestFul 的查询语言：GraphQL。用它进行查询时，所有的层级都必须显式注明，无法进行无限嵌套查询。这有点像加上了 SQL 的 RestFul 接口，并且它还支持动态 join。

我们可以设计一种生命周期，插件安装完成后根据一系列钩子获取到插件系统的状态，同时将输入输出连接到插件系统，这样任何的行为表现都交给了系统。比如插件 A 需要插件 B 的数据，它会试图先询问系统在存储空间内有没有插件 B 写入的数据，得知不存在时请求调用插件 B 的功能，得知插件 B 不存在时唤起插件系统的下载功能对插件 B 进行加载。

## 窗口 UI

### KISS

不要动原生对象！\
不要动原生对象！\
不要动原生对象！

重要的事说三遍。

### 命令式修改

### 中心化状态

# 原则

## 防呆设计

虽然只是一个很小的点，但实际操作中还是很容易被忽略，那就是没有一个用户会 100% 按照你的预期来使用你的产品。例如给用户一个删除按钮时，用户会毫不犹豫地点下它，然后等待确认删除的弹窗弹出来。什么？直接把文件删除了？你们这是欺诈消费者。所以业界共识都是删除往往都是只标记数据为已删除而不是真正删除，实际在磁盘清理或是存储服务缩容时才会丢弃这部分数据。但不符合用户预期的行为一定会带来用户的困惑，所以一定需要反复确认这种反人性但必要的功能。

另一个小点，用户的数据是我们第一优先级要保障的内容。撇开上面用户主动要删除资源的情形，如果遇到不可抗力，比如网络错误，或者数据格式解析失败，第一步也是尽可能备份用户的数据并提示用户自行转移，而不是失败了提示刷新页面，用户一点，咣的一声数据就没了。这就是为什么危险操作往往用红色标识，但一种趋势是：用户甚至不关心你在表达啥，他只是想把这个该死的弹窗给 × 掉。所以 Windows 更新才会以那么粗暴且不可取消的方式抢占用户的操作。

## 保持功能独立

没有什么比功能耦合更折磨程序员了，简单的小功能往往最后变得不可收拾，这通常是产品 feature 没有被良好地拆解消化，也可能是 DDL 倒排导致的赶工。总之，连 Chrome 都只能用多进程来解决不同网页的内存泄漏问题，就更不用说我们这些仓促写就的代码了。保持功能独立主要有以下几点：

- 数据的唯一性，参数的正交性。这个可以参见我之前的一篇文章[掌控前端数据流，响应式编程让你看得更远](https://www.infoq.cn/article/kzyb9iej6iyhegbnrlgd)，只有做到数据独立，才能最大程度减少错误状态给整体带来的危害。
- 对于外部 API/SDK 足够的不信任。也就是说任何未经严格测试的第三方内容都需要加兜底处理，以防击穿层层防护使应用崩溃。
- 组合优于继承。虽然这是句老生常谈的话，但实际运用中，加一个 if else 或是添加一个类似命名的方法都是在进行继承操作。如果有那么一点成本上的可能，我们甚至应该对每时每刻每分每秒的代码都部署一个版本，这样我们总能在漫漫时间长河里找到能用的那个版本。
