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

![](/blog/images/druid-a-new-gui-framework/00-34-37.png)

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

所谓界面，就是窗口中显示的那部分东西，通常来说是布局和组件的有机结合，当然也可以自定义组件的展示和行为，只需定义好所需的更新方式、事件处理、生命周期等即可，这样就带来了更多的可扩展性。
## 组件

最常见的组件莫过于文本块 [Label](https://docs.rs/druid/0.7.0/druid/widget/struct.Label.html) 和按钮 [Button](https://docs.rs/druid/0.7.0/druid/widget/struct.Button.html) 了。剩下的比如 Tab 栏、进度条、单选多选项、输入框等也是基本都有。
展示一下基本的按钮和文本块的创建方法。

```rust
let button = Button::new(button_text)
    .on_click(|_ctx, data: &mut State, _env| {
        data.count += 1;
    })
    .padding(5.0);
let label = Label::new("hello world");
```

## 布局

```
 -------non-flex----- -flex-----
|       child #1     | child #2 |


 ----flex------- ----flex-------
|    child #1   |    child #2   |

```

Druid 提供了 Flex 布局，熟悉 CSS 的同学一定很快就能理解，但类似以下这种命令式的创建方式还是让人皱眉头且怀念 CSS。

```rust
use druid::widget::{Flex, FlexParams, Label, Slider, CrossAxisAlignment};

let my_row = Flex::row()
    .cross_axis_alignment(CrossAxisAlignment::Center)
    .must_fill_main_axis(true)
    .with_child(Label::new("hello"))
    .with_default_spacer()
    .with_flex_child(Slider::new(), 1.0);
```

## 新建窗口

光靠组件和布局，仅仅是在窗口之内操作肯定是不足以创建出足够具有动态的应用的，我们还需要动态创建窗口的能力！Druid 也提供了在 `EventCtx` 或 `DelegateCtx` 上创建窗口的能力。

![](/blog/images/druid-a-new-gui-framework/00-02-55.png)

比如我们可以在全局 `AppDelegate` 上注册新窗口的 `Command`。

```rust
pub struct AppDelegater;

impl AppDelegate<State> for AppDelegater {
    fn command(
        &mut self,
        ctx: &mut DelegateCtx,
        _target: Target,
        cmd: &Command,
        data: &mut State,
        _env: &Env,
    ) -> Handled {
        if let Some(_) = cmd.get(NEW_WINDOW) {
            ctx.new_window(WindowDesc::new(new_window_builder)
                .window_size((400.0, 300.0)));
            Handled::Yes
        } else {
            Handled::No
        }
    }
}
```
## 图片

![](/blog/images/druid-a-new-gui-framework/00-34-02.png)

图片是个复杂的东东，目前看到 Druid 的处理方式是直接将图片的二进制数据编译进去，在运行时转变成像素进行渲染，需要安装 `image` 这个 crate 进行处理。后续 Druid 的版本会简化这一流程，但当前还是得这么写 …… 且图像会被变成黑白照片，不知道为啥，有知道的同学请不吝赐教。

```rust
use druid::widget::{Image, SizedBox};
use druid::{Widget, ImageBuf, WidgetExt, Color};
use druid::piet::{ImageFormat};

use crate::types::State;

pub fn make_image() -> impl Widget<State> {
  let raw_image = include_bytes!("../../resources/image/example.jpg");
  let image_data = image::load_from_memory(raw_image).map_err(|e| e).unwrap();
  let rgb_image = image_data.to_rgb8();
  let size_of_image = rgb_image.dimensions();
  let image_buf = ImageBuf::from_raw(
    rgb_image.to_vec(),
    ImageFormat::Rgb,
    size_of_image.0 as usize,
    size_of_image.1 as usize,
  );
  SizedBox::new(Image::new(image_buf))
    .fix_width(size_of_image.0 as f64 / 8.0)
    .fix_height(size_of_image.1 as f64 / 8.0)
    .border(Color::grey(0.6), 2.0).center().boxed()
}
```

# 其他

通常来说 GUI 程序拥有数据和界面就够了，这也就是典型的 MVC 架构，但实际上作为跨平台框架还需要考虑系统原生接口和国际化等问题，甚至包括富文本的处理。只有这些都面面俱到了，才能做到开发者无痛接入，一发入魂。

## 菜单与快捷键

Windows 和 macOS 的菜单不太一样，Windows 是挂在每个窗口标题栏下，而 macOS 则是挂在屏幕边缘，实际上它们都是作为窗口的一部分存在的，所以在设计时也是统一在窗口初始化时传入。

```rust
let menu = MenuDesc::new(LocalizedString::new("start"))
    .append(make_file_menu());
    .append(make_window_menu());
let main_window = WindowDesc::new(ui_builder).menu(menu);
```

## 国际化 i18n
 
Druid 的国际化是通过 `LocalizedString` 来实现的，例如在界面中有如下一段文本。

```rust
let text = LocalizedString::new("hello-counter")
    .with_arg("count", |data: &State, _env| data.count.into());
```

则可以通过创建一个 `resources/i18n/en-CN/builtin.ftl` 的文件（具体以 Druid 启动时的输出语言为准），在其中写入对应 `hello-counter`，其中的 `count` 就会被替换成实际的数据。
![DEBUG 启动时输出了 en-CN](/blog/images/druid-a-new-gui-framework/23-48-06.png)

```yaml
# resources/i18n/en-CN/builtin.ftl
hello-counter = 现在的值是 { $count }
```
![展示结果](/blog/images/druid-a-new-gui-framework/23-52-02.png)

{% img /images/druid-a-new-gui-framework/23-50-36.png 300 300 '"" "路径示意"' %}

## 富文本渲染、编辑

我们知道，经典物理学只是茫茫科学中限于低速宏观之中极小的一块研究区域，同理，一个简单的输入框也是富文本编辑的一个缩影。

[![](/blog/images/druid-a-new-gui-framework/00-13-22.png)](https://docs.rs/druid/0.7.0/druid/text/index.html)
完整的 text 模块包含了很多东西，但简单一点考虑，我们实现一个富文本编辑器只需要一个 `Editor` 和一个 `RichText` 的展示容器即可。

而 RichText 本质上是一串字符串与数个按索引设置的属性的数据集合。

```rust
pub fn generate_example_rich_data(text: &str) -> RichText {
    let attr = Attribute::TextColor(KeyOrValue::Concrete(Color::PURPLE));
    RichText::new(text.into())
        .with_attribute(6..=10, attr)
}
```

![显示效果](/blog/images/druid-a-new-gui-framework/00-25-05.png)

Druid 并不支持 `WYSIWYG` 所见即所得的编辑模式，所以编辑器和富文本内容是分离的，在数据中实际存储的应该是一段 raw 文本和数个属性的集合，在渲染时组成 `RichText` 传递给 `RawLabel` 进行渲染。

详情可见官方示例 - [markdown_preview](https://github.com/linebender/druid/blob/master/druid/examples/markdown_preview.rs)。

## 调试

在万能的 VS Code 里调试 Rust 程序是比较方便的。在创建 Rust 项目后，VS Code 就会提示按照 llvm 相关组件以便启用 DEBUG 模式。

在 `.vscode/launch.json` 中添加 `lldb` 为目标的配置后，即可在调试侧边栏一键开启调试模式。

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug executable 'gui'",
      "cargo": {
        "args": [
          "build",
          "--bin=gui",
          "--package=gui"
        ],
        "filter": {
          "name": "gui",
          "kind": "bin"
        }
      },
      "args": [],
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

![断点调试](/blog/images/druid-a-new-gui-framework/00-31-55.png)

如图所示，断点处的变量、调用栈、上下文等信息一览无余。

## 结语

本文简单介绍了 Rust GUI 框架 Druid 的基本架构和使用，通过笔者自行摸索解决了 Druid 实际运行版本和 Demo 及文档脱钩的问题，希望能对读者有所裨益。

后附笔者调试测试用的 Demo 仓库地址：https://github.com/msyfls123/rust-gui
