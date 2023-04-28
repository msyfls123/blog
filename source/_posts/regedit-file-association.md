---
title: 注册表与文件关联
date: 2023-04-28 16:33:42
tags: [Windows, 注册表]
categories: Windows
thumbnail: images/regedit-file-association/16-41-14.png
disqusId: regedit-file-association
---
注册表可能是 Windows 最愚蠢同时又是最伟大的发明之一。相较于 *nix 系统汗牛充栋的 *rc 文件，Windows 一直依赖于注册表这样一个中心化的注册服务来提供各种系统功能及样式的配置。与此同时带来的就是各种复杂的软件依赖关系，甚至各大厂商都深陷其中，不得不依赖第三方软件来对注册表里塞满的无用键值进行清理。对于这样一个令人头疼的领域，这篇文章将简单介绍一下如何将应用程序关联文件管理器中特定后缀名的文件右键菜单，让用户方便地使用你开发的程序对文件进行操作。所用的语言为 NSIS Script，语法指南可参考[这个链接](https://nsis.sourceforge.io/Docs/Contents.html)。

# 通用注册表修改

## 卸载方式关联
如果只是一个 Portable 文件，那么其实不需要卸载这个过程，直接删除文件即可。但既然我们需要一个稳定、位置可知的程序来处理我们的文件，这里必须将程序注册到系统菜单中。
安装过程因各个安装引导程序而已，作者这里是用的 NSIS 安装器。这里简单介绍一下 Windows 里如何将我们自己的程序注册到程序功能列表，以便用户哪天不爽了把程序卸载掉。

![程序与功能](/blog/images/regedit-file-association/16-48-55.png)

这里将程序注册到了 `计算机\HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall` 下，这里就是卸载程序的大本营了。
```nsis
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ExampleApp" "DisplayName" "示例程序"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ExampleApp" "DisplayIcon" "$INSTDIR\Example.exe"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ExampleApp" "UninstallString" "$INSTDIR\Uninstall Example.exe"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ExampleApp" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ExampleApp" "EstimatedSize" "${ESTIMATED_SIZE}"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ExampleApp" "DisplayVersion" "${VERSION}"
```

* `$INSTDIR` 是表示程序安装目录的变量，类似于 `C:\Program Files\ExampleApp`。

## 注册为软件分类
前一步里我们简单地将程序挂载到了可卸载列表里，这一步我们将其注册成软件分类。有人可能要问了，为啥不直接将软件绑定到文件后缀名呢？事实上那样做是可以的，如果你在右键选择其他程序打开则会直接往该后缀名里直接添加一个程序路径，类似 `C:\Program Files\ExampleApp\ExampleApp.exe` 的样子。

![](/blog/images/regedit-file-association/16-59-08.png)

但这样做有个问题，如果一个程序有修改安装路径或者是卸载时，就需要一个个去各个后缀名下面修改或者删除，我们肯定想要一个比较稳定的 key 来依赖。
所以我们选择将程序注册到 `计算机\HKEY_CURRENT_USER\SOFTWARE\Classes` 下面，这样它就能被其他地方所引用了。

```nsis
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp" "" "示例程序"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp\\DefaultIcon" "" "$INSTDIR\ExampleApp.exe,0"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp\\shell" "" "open"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp\\shell\\open" "FriendlyAppName" "示例程序"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp\\shell\\open\\command" "" "$INSTDIR\ExampleApp.exe $\"%1$\""
```

到这一步完成，我们的程序就算正式被系统所承认了，盖上了检疫合格的章子。
![](/blog/images/regedit-file-association/17-11-12.png)

# 特定文件后缀名关联

我们将进行两步关联，最后的效果是分别在一级菜单和打开方式的二级菜单同时注册我们的程序，并且使他们具有不同的操作。
![](/blog/images/regedit-file-association/17-12-17.png)

## 右键菜单

最粗暴的方式是直接写入 `计算机\HKEY_CLASSES_ROOT\*\shell` 下，这样所有的文件都会带上我们的程序，但用户可能会发现打开之后啥反应都没？
所以我们应该只给我们支持的程序进行关联，比如我们要给 pptx 文件进行关联，则需要如下设置：

```nsis
!macro BIND_SHELL_COMMAND EXT
  WriteRegStr HKLM "SOFTWARE\Classes\SystemFileAssociations\${EXT}\shell\ExampleApp.Import" "" "Import with ExampleApp"
  WriteRegStr HKLM "SOFTWARE\Classes\SystemFileAssociations\${EXT}\shell\ExampleApp.Import" "Icon" '"$INSTDIR\ExampleApp.exe"'
  WriteRegStr HKLM "SOFTWARE\Classes\SystemFileAssociations\${EXT}\shell\ExampleApp.Import\command" "" '"$INSTDIR\ExampleApp.exe" "-import-file=%1"'
!macroend

!insertmacro BIND_SHELL_COMMAND ".pptx"
```

这里解释一下，`BIND_SHELL_COMMAND` 是一个宏，它会在编译期进行展开，NSIS 也有 Call & Func 和 Section 的写法，但它们不支持多个参数，所以使用 macro 成了唯一的办法。
这里会在 pptx 文件的右键菜单里增加一个 `Import with ExampleApp` 的选项，一点之后就会执行 `ExampleApp.exe -import-file=xxx.pptx` 后面的工作就交给 `ExampleApp.exe` 自己去完成了。

## 打开方式
上一种关联方式比较粗暴，且没有办法与系统做更多交互了。我们可能想要我们的程序直接成为该种后缀名文件的默认打开程序，这样就会让用户形成路径依赖。
![](/blog/images/regedit-file-association/17-22-12.png)

直接抢占默认打开方式存在诸多不确定性，比如用户安装了 Office 或者 WPS，结果安装完你的程序，发现所有 Office 文件都被你抢了，实际并不能正常使用，这就很尴尬了。

所以我们采用比较温和的添加为可选执行程序的方式，将程序添加到 `计算机\HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pptx\OpenWithProgids` 里去，这样就能在右键打开方式里占有一席之地。

```nsis
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pptx\OpenWithProgids" "ExampleApp" ""
```

看似已经大功告成了，但我们一关联上，如果用户真的没有装别的打开 pptx 的软件，就会惊奇地发现所有的 pptx 文件都变成了你的软件图标。

> 用户：中毒了，你的程序有毒！！！

真是比窦娥还冤。为了避免这种情况，我们需要给这些文件依次设置它们应有的图标，同样通过设置 `计算机\HKEY_CURRENT_USER\SOFTWARE\Classes` 来达成我们的目的。

```nsis
!macro BindExtname InstallDir Ext Description
  !insertmacro CLEAN_LEGACY "${Ext}"

  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp.${Ext}" "" "${Description}"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp.${Ext}\\DefaultIcon" "" "${InstallDir}\resources\${Ext}.ico"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp.${Ext}\\shell" "" "open"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp.${Ext}\\shell\\open" "FriendlyAppName" "示例程序"
  WriteRegStr HKCU "SOFTWARE\Classes\ExampleApp.${Ext}\\shell\\open\\command" "" "${InstallDir}\ExampleApp.exe $\"%1$\""

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.${Ext}\OpenWithProgids" "" ""
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.${Ext}\OpenWithProgids" "ExampleApp.${Ext}" ""
!macroend

!insertmacro BindExtname $INSTDIR "pptx" "Microsoft PowerPoint 演示文稿"
```

如上设置之后，我们就成功地让所有 pptx 文件都拥有了一个可选的 ExampleApp 打开方式，如果用户将其设为默认程序，则会用 `${InstallDir}\resources\pptx.ico` 作为其图标，而文档类型则保持为"Microsoft PowerPoint 演示文稿"。

看起来非常完美！

改动前：
![](/blog/images/regedit-file-association/17-33-40.png)
改动后：
![](/blog/images/regedit-file-association/17-32-33.png)

## 清理

> 自己挖的坑，自己要填。

拒绝注册表垃圾，从我做起。

```nsis
!macro UNBIND_SHELL_COMMAND Ext
  DeleteRegKey HKCU "SOFTWARE\Classes\ExampleApp.${Ext}"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.${Ext}\OpenWithProgids" "ExampleApp.${Ext}"
  DeleteRegKey HKLM "SOFTWARE\Classes\SystemFileAssociations\${EXT}\shell\ExampleApp.Import"
!macroend

DeleteRegKey HKCU "SOFTWARE\Classes\ExampleApp"
!insertmacro UNBIND_SHELL_COMMAND "pptx"
```
