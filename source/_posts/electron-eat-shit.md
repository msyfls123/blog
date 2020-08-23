---
title: Electron 踩坑
date: 2020-08-20 19:51:09
tags: electron
categories: [web, app]
thumbnail: images/electron-eat-shit-1.jpg
disqusId: electron-eat-shit
---

来鹅厂做了俩常规项目（更新文件上传方式至 COS 及修改移动端顶部 UI）后参与了文档 App 的桌面 `Electron` App 开发，在 UI 层上又是一个坑接一个坑。主要有下述几点：
- 实现适应于内置 `React` 组件大小的 `BrowserWindow`，同时保证首次加载时页面不会错乱
- 使自定义弹窗可拖拽并且内部表单组件可使用
- 在 `BrowserWindow` 内弹出超出 Window 范围的菜单
- 跨端编译打包后发现 runtime 对不上

## 使 `BrowserWindow` 自适应 `React` 组件

我们知道 `Electron` 的 `BrowserWindow` 的默认尺寸为 `800 × 600`，虽然可以初始化设置弹窗大小，但是并不知道弹窗内容尺寸呀！于是乎，需要先隐藏弹窗直至 `compsnentDidMount` 时获取到 dialog 内容尺寸再设置 `BrowserWindow` 的大小并显示。

```typescript
// main-process 打开弹窗
import { ipcMain } from 'electron'

export function openDialog() {
  const dialog = new BrowserWindow({
    show: false
  })
  ipcMain.once('dialog-did-mount', () => {
    dialog.show()
  })
}

```

```javascript
// renderer 页面在组件加载后设置宽高并返回消息显示 window
import React, { useEffect, useRef } from 'react'
import { ipcRenderer, remote } from 'electron'

export default function Dialog() {
  const dialogRef = useRef()
  useEffect(() => {
    const window = remote.getCurrentWindow()
    const { clientWidth, clientHeight } = dialogRef.current
    window.setSize(clientWidth, clientHeight, true/* animate */)
    window.center()
    ipcRenderer.send('dialog-did-mount')
  })
  return <div ref={dialogRef}>
    contents...
  </div>
}
```

## 拖拽窗口

[官方解答](https://www.electronjs.org/docs/api/frameless-window#%E5%8F%AF%E6%8B%96%E6%8B%BD%E5%8C%BA)
遇到的坑是设置好 dialog 内部 `button/input` 的 `no-drag` 后发现 `dui`（某鹅厂组件库）会直接在 `body` 下生成 DOM 节点，哪怕设置上了 `dui-*` 这样的通配符都没用，在 `Windows` 上点击事件还是穿透了组件，只好给整个内容的区域都打上了 `-webkit-app-region: no-drag`。

## 弹出超出 `Window` 的菜单

[官方做法](https://www.electronjs.org/docs/api/menu#menupopupoptions)
设计觉得 `Windows` 下不好看，于是要自定义 `BrowserWindow`。

```typescript
// main-process 打开弹窗
import { BrowserWindow } from 'electron'

function openMenu(x, y) {
  const menu = new BrowserWindow({ x, y })
  menu.loadUrl(`file://${__dirname}/menu.html`)
  menu.on('did-finish-load', () => {
    menu.show()
  })
}
ipcMain.on('open-menu', (event, x, y) => openMenu(x, y))
```

```typescript
// renderer 渲染进程捕获触发元素
import { remote } from 'eletron'
import React, { useRef, useEffect } from 'react'

export default function App() {
  const btnRef = useRef()
  useEffect(() => {
    const window = remote.getCurrentWindow()
    const { x: windowX, y: windowY } = window.getBounds()
    const { x: elX, y: elY, height } = btnRef.current.getBoundingClientRect()
    const x = windowX + elX
    const y = windowY + elY + height
    ipcRenderer.send('open-menu', x | 0, y | 0)
  })
  return <div>
    content...
    <button ref={btnRef}>点我出菜单</button>
  </div>
}
```

其中
```typescript
ipcRenderer.send('open-menu', x | 0, y | 0)
```

非常重要 😂 因为 `Electron` 打开 menu 的 `x & y` 只认整型，而 `getBoundingClientRect()` 返回了浮点数，直接用就崩了……

## 区分「开发时」「编译时」和「运行时」

跨端开发的优势就是 `Write Once, Run Everywhere`。代码能贴近运行时判断就贴近运行时判断，不过为了开发和打包大小，有如下几个优化思路。

- 跨端开发 UI 需要调试查看其他端上的状态，所以会需要一个全局的样式开关，目前只区分了 `macOS` 和 `Windows`，写作
  ```typescript
  // constants/setting.ts
  const useMacStyle = process.platform === 'darwin'
  ```
  开发时只需要按需加 `!` 取反就可以方便切换样式了，`process.platform` 是啥？这就是编译时了。
- 编译时需要确定目标对象，一般会写成不同脚本或者是一个脚本里根据 `platform` 分发并写入进程参数，为了锁死各种依赖关系，假设某处写了 `process.platform === 'darwin` 如果 `platform`  不符合就会直接剪枝掉后面的部分。
- 而运行时就广泛得多，比如关闭所有窗口时默认退出 App。
  ```typescript
  import os from 'os'
  import { app } from 'electron'
  app.on('window-all-closed', () => {
    if (os.platform() !== 'darwin') {
      app.quit()
    }
  })
  ```
  再比如根据系统类型开启不同的提示文本，这些都需要运行时判断，虽然也可以直接编译时判断，但终究不够灵活。

__结论__：类似于配置下发的流程，如果是偏开发侧的内容可以在一处统一管理，如果是偏向本地系统的功能可以根据实际运行环境开闭，做到尽量少依赖于编译时以求在多端最大化复用代码逻辑。

-----
To be continued……
