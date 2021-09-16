---
title: Electron 客户端自动更新
date: 2021-09-16 11:49:17
tags: electron
categories: [web, app]
thumbnail: images/electron-eat-shit-1.jpg
disqusId: electron-update
---

随着科技的进步，啊不，是网络通信技术的提升，客户端用户不再受限于拨号上网那样的小水管，百兆宽带触手可达，随时随地自动更新版本成为了标配。作为跨端框架的翘楚，Electron 自然也是内置了自动更新功能，但查阅其官网发现其提供的 [autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater/) 并无明确的操作路径可言，读完仍是一头雾水，尤其是还需要私有 CDN 部署时更是两眼一抹黑。

![漫漫更新路](/blog/images/electron-update/21-41-04.png)

让我们从零开始，更新逻辑其实很简单，每次发版时将更新文件分发到 CDN 上，客户端通过检查 CDN 上有无更新文件继而下载文件并安装即可完成更新。抛开上传下载这种技术问题不谈，要解决两点：

- 什么版本可以更新
- 可以更新到什么版本

说人话就是从哪儿来，要到哪儿去。本文将要为你解答的就是如何通过一系列配置服务及本地设置，完成包含灰度更新、强制更新、静默更新以及 GUI 更新过程展示在内的可操纵动态更新策略。

## 发布与更新
首先确定一点，我们依然用的是 Electron 提供的更新功能，但主要用了 electron-builder 封装后的 [electron-updater](https://www.electron.build/auto-update)。这里的文档和 Electron 官方文档比较类似，有点啰嗦，下面就使用自定义 CDN 这条路提纲挈领地给大家梳理关键步骤。

### 生成制品信息
这里假定你一定是通过 electron-builder 进行打包了，需要在 electron-builder-config 中加入如下字段（[详细字段配置](https://www.electron.build/configuration/publish)）
```js
const config = {
    ...others,
    publish: {
        provider: 'generic',
        channel: 'latest-win32',
        url: 'https://your.cdn/update-path',
    },
}
```

这里假设你的更新文件会被放在 `https://your.cdn/update-path` 目录下，通过这个配置打出来的安装文件就会多出一个 `latest-win32.yml` 文件，这个文件长下面这样子。

![制品信息](/blog/images/electron-update/22-21-14.png)

这里面主要包含了版本号、更新资源文件的文件名及校验 hash 及发布日期等关键信息，对于后续步骤最重要的就是资源的文件名了。

将安装包与 yml 文件一起上传到 CDN 的 `https://your.cdn/update-path` 目录下就完成了生成制品信息的这一步。
![](/blog/images/electron-update/22-34-19.png)

### 配置自动更新信息

来到这一步需要保证 `https://your.cdn/update-path/latest-win32.yml` 已经是可以访问到的了，后面就是如何在端内把 electron-updater 支棱起来。

首先安装 electron-updater: `npm i electron-updater`。
**这里作者实操中有个问题，electron-updater 打包后失效了，暂未明确原因，故在 webpack 中将其设为 externals 并在最终由 electron-builder 打包的目录 projectDir 里安装了 electron-updater。**

接下来，为了开发调试我们需要做一点骚操作，在下图所示目录中有 `app-update.yml` 文件。
![mac app-update.yml](/blog/images/electron-update/22-36-06.png)
![windows app-update.yml](/blog/images/electron-update/22-37-11.png)
这个文件里面内容是这样的，将它复制到项目根目录下并改名叫 `dev-app-update.yml`，后面就能调试更新了。
![](/blog/images/electron-update/22-40-35.png)

进入激动人心的代码环节！
```js
import { autoUpdater } from 'electron-updater';

// 设置为指定发布版本，以防错读为 Electron 版本
autoUpdater.currentVersion = APP_VERSION;
autoUpdater.setFeedURL({
    provider: 'generic',
    channel: os.platform() === 'darwin' ? 'latest' : 'latest-win32',
    url: `https://your.cdn/update-path`,
});
autoUpdater.checkForUpdates();
autoUpdater.on('update-downloaded', () => {
    autoUpdater.quitAndInstall();
});
```
对，就是这么简单，一旦下载更新完成立即以迅雷不及掩耳之势退出 App 进行更新并重启。这是不是太快了点？都没留给用户反应的时间了。别着急，可以参考这篇文章做一个漂亮的更新界面出来。
https://blog.csdn.net/Wonder233/article/details/80563236

### 静默更新

如果把上面的退出更新步骤去掉，离静默更新就只差一步了。
```diff
+ autoUpdater.autoInstallOnAppQuit = true;
- autoUpdater.on('update-downloaded', () => {
-     autoUpdater.quitAndInstall();
- });
```

至这一步为止，你已经做完了一个不断更新到最新版本的 Electron App 所需要的一切了。