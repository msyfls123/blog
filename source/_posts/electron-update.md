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

- **什么版本可以更新**
- **可以更新到什么版本**

说人话就是从哪儿来，要到哪儿去。本文将要为你解答的就是如何通过一系列配置服务及本地设置，完成包含灰度更新、强制更新、静默更新以及 GUI 更新过程展示在内的可操纵动态更新策略。

# 发布与更新
首先确定一点，我们依然用的是 Electron 提供的更新功能，但主要用了 electron-builder 封装后的 [electron-updater](https://www.electron.build/auto-update)。这里的文档和 Electron 官方文档比较类似，有点啰嗦，下面就使用自定义 CDN 这条路提纲挈领地给大家梳理关键步骤。

## 生成制品信息
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

## 配置自动更新信息

来到这一步需要保证 `https://your.cdn/update-path/latest-win32.yml` 已经是可以访问到的了，后面就是如何在端内把 electron-updater 支棱起来。

首先安装 electron-updater: `npm i electron-updater`。
**这里作者实操中有个问题，electron-updater 打包后失效了，暂未明确原因，故在 webpack 中将其设为 externals 并在最终由 electron-builder 打包的目录 projectDir 里安装了 electron-updater。**

接下来，为了开发调试我们需要做一点骚操作，在下图所示目录中有 `app-update.yml` 文件。
![mac app-update.yml](/blog/images/electron-update/22-36-06.png)
![windows app-update.yml](/blog/images/electron-update/22-37-11.png)
这个文件里面内容是这样的，将它复制到项目根目录下并改名叫 `dev-app-update.yml`，后面就能调试更新了。
![](/blog/images/electron-update/22-40-35.png)

**需要说明的是，macOS 上自动更新只有在签名后的 App 上才能进行，在后续步骤的退出并安装前会校验签名，校验失败时会报错。**

## 自动更新
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
对，就是这么简单，一旦下载更新完成立即以迅雷不及掩耳之势退出 App 进行更新并重启。这是不是太快了点？都没留给用户反应的时间了。别着急，可以通过 autoUpdater 上的各种事件，参考这篇文章做一个漂亮的更新界面出来。
https://blog.csdn.net/Wonder233/article/details/80563236

autoUpdater 事件：
- error
- checking-for-update
- update-available
- update-not-available
- download-progress
- update-downloaded

# 精细化更新

## 静默更新

如果把上面的退出更新步骤去掉，离静默更新就只差一步了。
```diff
+ autoUpdater.autoInstallOnAppQuit = true;
- autoUpdater.on('update-downloaded', () => {
-     autoUpdater.quitAndInstall();
- });
```

至这一步为止，你已经做完了一个不断更新到最新版本的 Electron App 所需要的一切了。

## 强制更新

即使你设置了每次都会自动更新，依然免不了有用户不肯买账，或者说会在各种网络差的情况下没法及时更新到最新版本，我们可以通过下发一个配置文件，来控制一些有废弃 API 或者有严重 bug 的版本被继续使用。

例如在[七彩石系统](http://rainbow.oa.com/)上生成一个如下的配置，其中 `force_update_version_list` 就是一串 semver 规范的版本范围。
![配置字段](/blog/images/electron-update/23-27-57.png)

在使用时只需要判断一下 APP_VERSION 是否在这些个区间内即可。
```js
import * as semver from 'semver';

const config = await fetchUpdateConfig(key);
const forceUpdateVersions = config.force_update_version_list;
const shouldForceUpdate = forceUpdateVersions.length &&
    semver.satisfies(APP_VERSION, forceUpdateVersions.join('||'));
```

这里在发出七彩石请求时出现了一个 `key`，这个 `key` 提供了本地去决定使用哪个七彩虹配置组的能力，比如测试就填 Test，线上默认为 Production，方便测试。

## 灰度更新

强制更新解决了哪些版本必须更新的问题，如果我们只想让某些版本或是用户更新到指定版本呢？这也就是通常所说的金丝雀发布、A/B 测试之类的了。同样可以用从网络拉取一个配置文件来解决，正好七彩石平台也满足我们的这种需要。

### 配置下发

![七彩石配置](/blog/images/electron-update/23-39-23.png)

首先七彩石支持根据 uin、ip 等进行灰度发布，我们选择了将 uid 后两位截取为 uin 上传七彩石，七彩石拿到 uin 后根据灰度规则（上图配的是 30% 的比例）下发最新更改的配置项。

![逐天放开灰度比例](/blog/images/electron-update/23-53-15.png)

直至 100% 比例后，可以进一步替换官网链接，完成全量发布。

### 更新路径划分

聪明的读者已经发现了，在[发布与更新](#自动更新)中，我们设置了统一的更新目录 `https://your.cdn/update-path`，如果有不同的更新版本，我们就需要设置不同的文件或是目录来控制。该用哪一种呢？

|版本排布方式|优势|劣势|
|---|---|---|
|按目录|一个目录一个版本|无统一更新地址|
|按文件|目录层级扁平|文件混杂难分清|

综合考虑后，我们选择了按目录划分版本的方式。
![版本](/blog/images/electron-update/00-07-14.png)
![文件](/blog/images/electron-update/00-07-44.png)

在上面的自动更新代码中替换如下内容即可享受精细控制的灰度更新功能。

```diff
import { autoUpdater } from 'electron-updater';

+ const config = await fetchUpdateConfig(key);

// 设置为指定发布版本，以防错读为 Electron 版本
autoUpdater.currentVersion = APP_VERSION;
autoUpdater.setFeedURL({
    provider: 'generic',
    channel: os.platform() === 'darwin' ? 'latest' : 'latest-win32',
-   url: `https://your.cdn/update-path`,
+   url: `https://your.cdn/update-path/${config.version}`,
});
autoUpdater.checkForUpdates();
autoUpdater.on('update-downloaded', () => {
    autoUpdater.quitAndInstall();
});
```

# 尾声

## 按渠道分发
更新和下载一样是为了分发，当我们有了更多渠道时也可能需要考虑渠道间的差异性。渠道包可以通过配置文件进行区分，更新时只更新资源而不更新配置文件，这样就可以做到不同的安装渠道在同一更新下保持自身渠道特殊性。

## 永远递增你的版本号
The lastest, the best.