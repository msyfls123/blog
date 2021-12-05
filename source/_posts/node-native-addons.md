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

## V8
## 兼容性

C++ addons 实战
===

## 初始化项目
### node-gyp
### 系统相关设置

## 开发一个简单的 Defer 模块
### 类型定义
### 划分 C++ 与 JavaScript 职责
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
