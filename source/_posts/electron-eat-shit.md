---
title: Electron 踩坑
date: 2020-08-20 19:51:09
tags: electron
categories: [web, app]
thumbnail: images/electron-eat-shit-1.jpg
disqusId: electron-eat-shit
---

来鹅厂做了俩常规项目（更新文件上传方式至 COS 及修改移动端顶部 UI）后参与了文档 App 的桌面 Electron App 开发，在 UI 层上又是一个坑接一个坑。主要有下述几点：
- 实现适应于内置 React 组件大小的 BrowserWindow，同时保证首次加载时页面不会错乱
- 使自定义弹窗可拖拽并且内部表单组件可使用
- 在 BrowserWindow 内弹出超出 Window 范围的菜单