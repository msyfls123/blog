---
title: 非主流 App GUI 框架 - Druid
date: 2021-05-18 23:10:26
tags:
  - Rust
  - App
categories: GUI
thumbnail: images/druid-a-new-gui-framework/23-45-28.png
disqusId: druid-a-new-gui-framework
---

不会吧，不会吧，都 2021 年了还有人在写桌面端应用吗？不都是 `Electron` 一统江湖了吗？对，也不对，`Electron` 的确大大降低了 web 页面直接生成单个可执行桌面程序的难度，但因其依赖于 `Chromium` 内核，糟糕的启动速度和海量内存占用一直是广大网友所诟病之处。
市面上还是有很多跨端 GUI 解决方案的，比如 `Qt` 和 `GTK` 等等，但既然是玩票嘛，就搞点新鲜的，本文就介绍一下当红炸子鸡语言 Rust 上的非主流 GUI 框架 - `Druid。`

![demo](/blog/images/druid-a-new-gui-framework/23-42-26.png)

先简单介绍下 [Druid](https://github.com/linebender/druid)，它同样是一个数据驱动的原生框架，背后是同作者开发的 [Piet](https://github.com/linebender/piet) 绘图库。在不同的系统上有着不同的实现，这里就不多提了，感兴趣的可以深入研究一下。目前 `Druid` 还处在较为早期的开发阶段（除此之外的 GUI 库也都差不多……），所以文档和示例都很不全。本文将基于 `0.7.0` 版本进行阐述，如后续有不兼容升级，以官方文档为准。

# 启动

## 安装

万事开头难，中间更难，最后最难。说实话，Rust 的包管理系统已经算是不错的了，在你装好了 Rust 环境之后，随便创建个 cargo bin 项目即可，把 `druid` 加到依赖里面，这里推荐装个 `cargo-edit` 的包，这样你就能得到以下几个 cargo 命令，后续就不需要手动改 `Cargo.toml` 文件了。

```
cargo-edit v0.7.0:
    cargo-add
    cargo-rm
    cargo-upgrade
```

## 第一个界面

[官网第一个 case](https://github.com/linebender/druid/blob/ea8ec4728d459e9ffa0b3818b5d988d6a3436e4d/README.md) 就让我们栽了跟头，这里的 `log_to_console` 和 `ui_builder` 都不太对劲，改成如下代码就可以跑出首个界面啦。

```rust
use druid::widget::{Button, Flex, Label};
use druid::{AppLauncher, LocalizedString, PlatformError, Widget, WidgetExt, WindowDesc};

fn main() -> Result<(), PlatformError> {
    let main_window = WindowDesc::new(ui_builder);
    let data = 0_u32;
    AppLauncher::with_window(main_window)
        .use_simple_logger()
        .launch(data)
}

fn ui_builder() -> impl Widget<u32> {
    // The label text will be computed dynamically based on the current locale and count
    let text =
        LocalizedString::new("hello-counter").with_arg("count", |data: &u32, _env| (*data).into());
    let label = Label::new(text).padding(5.0).center();
    let button = Button::new("increment")
        .on_click(|_ctx, data, _env| *data += 1)
        .padding(5.0);

    Flex::column().with_child(label).with_child(button)
}
```

麻雀虽小，五脏俱全，我们可以看到 `ui_builder` 就是界面相关的部分了，其中有文本和按钮，以 flex 布局，而这个函数被整个传递给了一个 `WindowDesc` 的构造函数，这就创建了一个窗口，然后这个窗口又被传递给了 `AppLauncher`，接着用 data 作为初始数据启动。整体逻辑还是比较清晰的。

# 数据

虽然前面传入的数据只是一个 `u32`，但实际应用的数据状态肯定不止如此。Druid 提供了一套简单但够用的数据定义和处理模型，其核心是通过内部获取数据的可变引用直接修改数据本身，而外部通过消息传递给代理器统一更改数据，实现了灵活多样的数据操作。

## 类型定义

首先是类型定义，`Druid` 提供了 [Data](https://docs.rs/druid/0.7.0/druid/trait.Data.html) 和 [Lens](https://docs.rs/druid/0.7.0/druid/trait.Lens.html) 两个重要的 trait，它们分别提供了如何判断数据相等和如何从一大块数据中提取所需要数据的方式。

```rust
use druid::{Data, Lens};
use tokio::sync::mpsc::{UnboundedSender}

[derive(Debug, Clone, Data, Lens)]
pub struct State {
    pub day: u32,
    #[data(ignore)]
    pub dispatch: UnboundedSender<u32>,
}
```

通常情形下，`Date` 和 `Lens` 可以被 derive 自动实现，但有些时候则需要一点小小的帮助，比如上图就需要忽略掉不可比较的 `dispatch` 字段，它只是一个消息发送器，无所谓变更，也不会变更。
像 `Lens` 的用途就更大了，比如组合属性等，详情可见 [LenExt](https://docs.rs/druid/0.7.0/druid/trait.LensExt.html)。

## 事件与代理

前面讲了事件处理的方式：

- 直接获取数据可变引用并修改
- 通过消息代理

先讲讲消息代理这种形式吧，毕竟从 React 过来的人都偏好单向数据流。

在 `AppLauncher` 真正 launch 之前可以通过 `get_external_handle` 获取一个 `ExtEventSink`，通过它可以向 Druid App 内发送消息，这玩意甚至可以跨线程传递。而接受消息同样在 `AppLauncher` 上，通过传入一个实现了 `AppDelegate` trait 的 struct 给 `delegate` 方法即可。

需要注意的是，发送的消息和接受的消息都需要以唯一的 `Selector` 识别，示例如下：

```rust
use druid::{Selector, AppDelegate};

const NEW_DAY: Selector<String> = Selector::new("new-day");
impl AppDelegate<State> for AppDelegater {
    fn command(
        &mut self,
        ctx: &mut DelegateCtx,
        _target: Target,
        cmd: &Command,
        data: &mut State,
        _env: &Env,
    ) -> Handled {
        if let Some(day) = cmd.get(NEW_DAY) {
            data.days.push_back(day.to_string());
            Handled::Yes
        }
    }
}
```

## 控制器

控制器即 [Controller](https://docs.rs/druid/0.7.0/druid/widget/trait.Controller.html)，它和 App 上的消息代理类似，但不同之处在于它往往是局部的，能提供针对某种 Event，组件生命周期和内外数据变化的精细控制。

例如，我们想要在窗口中实现一个右键菜单：每当用户操纵鼠标在窗口内右键单击时调用 `make_demo_menu` 创建一个菜单。

```rust
use druid::widget::{Controller};
use druid::{Widget, Event, ContextMenu};
use crate::components::menu::make_demo_menu;
use crate::types::{State};

pub struct WindowController;

impl <W: Widget<State>> Controller<State, W> for WindowController {
    fn event(
        &mut self,
        child: &mut W,
        ctx: &mut druid::EventCtx<'_, '_>,
        event: &druid::Event,
        data: &mut State,
        env: &druid::Env
    ) {
        match event {
            Event::MouseDown(ref mouse) if mouse.button.is_right() => {
                let context_menu = ContextMenu::new(make_demo_menu(), mouse.pos);
                ctx.show_context_menu(context_menu);
            },
            _ => child.event(ctx, event, data, env),
        }
    }
}
```

需要注意的是没有处理的 `Event` 需要显式交给 child 继续处理，这与浏览器的 DOM 事件不同，是向下“冒泡”的。
## 环境变量

这里的环境变量不是指系统的环境变量，而是 Druid App 组件相关的整体设定，例如窗口颜色和按钮尺寸等等。
环境变量分两种：一种全局，一种局部。

全局的环境变量通过 launcher 的 `configure_env` 设置。

```rust
launcher.use_simple_logger()
    .configure_env(|env, _| {
        env.set(theme::WINDOW_BACKGROUND_COLOR, Color::WHITE);
        env.set(theme::LABEL_COLOR, Color::AQUA);
        env.set(theme::BUTTON_LIGHT, Color::WHITE);
        env.set(theme::BUTTON_DARK, Color::WHITE);
        env.set(theme::BACKGROUND_DARK, Color::GRAY);
        env.set(theme::BACKGROUND_LIGHT, Color::WHITE);
    })
```

而局部的环境变量则可以通过 [EnvScope](https://docs.rs/druid/0.7.0/druid/widget/struct.EnvScope.html) 来设置，就可以做到组件样式隔离。

```rust
EnvScope::new(
    |env, data| {
        env.set(theme::LABEL_COLOR, Color::WHITE);
    },
    Label::new("White text!")
)
```

# 界面
## 组件

## 布局
## 图片

# 其他
## 菜单与快捷键
## 国际化 i18n
## 富文本渲染、编辑
## 调试
