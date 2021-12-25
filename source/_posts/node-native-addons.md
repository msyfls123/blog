---
title: 初探 Node.js 原生扩展模块
date: 2021-12-05 12:21:01
tags:
  - Node.js
  - C++
categories: web
thumbnail:
disqusId: node-native-addons
---

最近因项目需要开始研究 Node.js 原生模块的实现，并尝试接入自研 C++ 模块。Node.js 因其具有良好的跨平台适配性和非阻塞事件循环的特点，受到了服务端开发者的关注，但 JavaScript 毕竟基于 GC 实现的数据结构，在高性能计算上有所不足；而且很多老代码或者扩展库都以 C++ 书写，也给移植编译带来了一定的困难。如何在性能、兼容性和开发效率上取得平衡，为了解决这些个问题，让我们开始书写第一个 Node.js C++ addon 吧！

C++ addons 的原理
===

不管你看哪个教程（其实中文书也就一本，就是死月这本[《Node.js：来一打 C++ 扩展》](https://book.douban.com/subject/30247892/)），提到 Node.js 一上来就是 V8 Isolate, Context, Handle,  Scope 讲一堆，看完这两百页头已经晕了。这些都是非常基础的 V8 知识，但离实际运用还隔了很远。为了写出 C++ addons，我们只要抓住一点 ———— “JavaScript 对象就是一个个 V8 C++ 对象的映射”。

## V8

![String 类型的继承链](/blog/images/node-native-addons/20-57-34.png)

上图是 JS 里一个简单 String 的继承关系，如何创建一个简单的字符串呢？`String::NewFromUtf8(isolate, "hello").ToLocalChecked()`，是不是看了有些头大？如果告诉你这种继承关系随着 V8 的升级经常发生变化，是不是感觉血压都高了？

没错，这就是上古时期 Node.js C++ addons 的开发方式，需要指定 Node.js 的版本进行编译，只有在指定 ABI 的版本下才能运行。

https://nodejs.org/api/addons.html#hello-world ，有兴趣的读者可以阅读下 Node.js 官网对于 C++ addons 的简易劝退教程，里面展示了不少早期 Node.js 开发者与 C++ 对象搏斗的真实记录。

## 兼容性

在经历了刀耕火种的日子后，盼星星盼月亮终于迎来了 Node.js 的原生抽象 —— N-API。它利用宏封装了不同 V8 版本之间的 API 差异，统一暴露了多种识别、创建、修改 JS 对象的方法。让我们来看看如何创建一个字符串呢？

```cpp
#include <node_api.h>

napi_value js_str;
napi_create_string_utf8(env, "hello", NAPI_AUTO_LENGTH, &js_str);
```

哎~ 怎么看起来也不是很简单嘛？。。。

别骂了，别骂了，要知道 Node.js 为了兼容不同版本付出了多大的努力吗？相对来说上述的 API 调用算是很简单的了。`env` 是执行的上下文，`js_str` 是创建出来的 JS 字符串，`NAPI_AUTO_LENGTH` 是自动计算的长度，这里还隐含了一个变量，就是 `napi_create_string_utf8` 的返回值 `napi_status`，这个值一般平平无奇，但万一要是出了 bug 就得靠它来甄别各处调用是否成功了。

C++ addons 实战
===

前情铺垫结束，让我们拥抱改变吧。下面将带大家以一个简单的 Defer 模块的实现为例，走马观花式感受 C++ addons 的开发过程。

## 初始化项目

首先你得有个 Node.js，版本呢最好能到 14、16 以上，因为 N-API 有些部分在 14 的时候才加入或者稳定下来。

然后你得准备个 C++ 编译环境，下面简单介绍下各个系统下是如何操作的。

- macOS: `xcode-select --install` 基本可以解决，后面会用 llvm 进行编译。
- Windows: 啥都别说了，VS 大法好。推荐装 2019 Community 即可，然后记得把 v142 工具集装了就成。因为 node-gyp 会写死 VS 的版本号，所以如果出了问题就使用 VS installer 继续安装缺失的组件即可。
- Linux: `apt-get install gcc`.

这样就准备好正式编译我们的 C++ addons 了。

### node-gyp

通常情况下编译并链接 C++ 库是一件非常吃力不讨好的事，`cmake` 等工具的出现就是为了解决这个问题，而到了 Node.js 这一边，官方提供了同样的工具 `node-gyp`。只需 `npm i node-gyp -g` 即可，后续我们都将在 `node-gyp` 下操作。

### VS Code 相关设置

我们可以在 VS Code 中设置 C++ 环境，这会给开发带来不少的体验提升。
https://code.visualstudio.com/docs/languages/cpp
![](/blog/images/node-native-addons/23-22-13.png)

这里是一份可参考的 `.vscode/c_cpp_properties.json` 示例：
```json
{
    "configurations": [
        {
            "name": "Mac",
            "includePath": [
                "${workspaceFolder}/**",
                "/usr/local/include/node"
            ],
            "defines": [],
            "macFrameworkPath": [
                "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks",
                "/System/Library/Frameworks",
                "/Library/Frameworks"
            ],
            "compilerPath": "/usr/bin/clang",
            "cStandard": "c17",
            "cppStandard": "c++14",
            "intelliSenseMode": "macos-clang-x63"
        },
        {
            "name": "Win32",
            "includePath": [
                "${workspaceFolder}/**",
                "C:\\Users\\kimi\\AppData\\Local\\node-gyp\\Cache\\16.6.0\\include\\node"
            ],
            "defines": [
                "_DEBUG",
                "UNICODE",
                "_UNICODE"
            ],
            "windowsSdkVersion": "10.0.17763.0",
            "compilerPath": "C:/Program Files (x86)/Microsoft Visual Studio/2017/Community/VC/Tools/MSVC/14.16.27023/bin/Hostx64/x64/cl.exe",
            "cStandard": "c17",
            "cppStandard": "c++14",
            "intelliSenseMode": "windows-msvc-x64"
        }
    ],
    "version": 4
}
```

这段 JSON 最重要的就是要指向 node 头文件的 includePath，上面分别提供了当前安装版本和 node-gyp 缓存的路径，以供参考。

## 小试牛刀：开发一个简单的 Defer 模块

在学习新知识点时，以熟悉的概念切入会更有学下去的动力。我们就小试牛刀，先实现一个非常非常简陋只支持一个 Promise 调用的 Defer 模块吧！

先让我们看一下最终需要的调用方式，从 JS 侧看就是加载一个 *.node 的原生模块，然后 new 了一个对象出来，最后调用一下它的 run 方法。可能 JS 写起来 10 行都不到，但这次的目标是将 C++ 与 JS 联动，这中间的过程就有点让人摸不着头脑了。

![简单的 Defer 模块](/blog/images/node-native-addons/22-21-18.png)

别慌，遇事不决先定类型，前文中提到过，类型就是编程中的量纲，分析量纲就能得出解题思路。

### 类型定义

抛开语言的差异，来分析一下这个 Deferred 类，它的构造函数接受一个字符串进行初始化，然后有个 public 的 `run` 方法接受一个数字并返回一个 Promise，以这个数字所代表的毫秒数来延迟 resolve 所返回的 Promise。

```typescript
class Deferred {
    constructor(private name: string)
    public run(delay: number): Promise<string>
}
```

咦，这么简单吗？是的，JS 本就为了开发效率而生，但事情到 C++ 层面可就不那么简单了……

### 划分 C++ 与 JavaScript 职责

![JavaScript 与 C++ 各自的职责](/blog/images/node-native-addons/23-47-59.png)

为了 OOP，我们将数据和行为都存在 C++ 一侧，这会带来一些问题，就是我们需要思考如何在 C++ 侧创造一个 JS 的类来承载这些数据。也可以将 C++ 作为一个无状态的服务，每次都将数据从 JS 传过来，计算完了传回去即可，但这样会造成序列化的开销，需要根据具体问题具体分析。

但作为示例，我们还是按照最通用的来，就是实实在在地在 C++ 侧定义好 constructor 和类上的方法，暴露给 JS 调用即可。

### 创建 C++ 类
### 创建 JS class 的 constructor
### 设置 JS class 上的调用方法

## 高级技巧
### 线程安全调用
### Promise 的实现

C++ addons 调试与构建
===
## VSCode CodeLLDB 调试
## prebuildify 预构建
## 与 GitHub Actions 集成

C++ addons 的展望
===

## 无痛集成第三方库
## 编译目标：WebAssembly Interface？
