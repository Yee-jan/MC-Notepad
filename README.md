# 书与笔 / MC Notepad

在电脑上复刻 Minecraft 里那本「书与笔」。Python + tkinter，单文件，不用装任何第三方库。

![书架界面](docs/screenshot-shelf.png)

中文名叫「书与笔」，英文和路径都叫 MC Notepad，窗口标题跟着界面语言走。

代码拿去随便改。改了之后愿意的话，提一句原作地址就行。

## 为什么做这个

游戏里那本书只能在世界里打开，想随手记点东西就得开着 MC。
我就想有一个能随时掏出来的桌面版——书架上放几本，点开就能写。

## 界面

四个界面共用一个 760×600 的窗口，切换时不会跳尺寸。

| 界面 | 长什么样 |
|---|---|
| 书架 | 顶栏是新建 / 排序 / 搜索 / 设置，下面一列木牌，每块写书名、页数、作者、最后编辑时间 |
| 书页 | 木质书框里左右两页，一次翻一页，页顶有页码，翻页靠左右下角的折角 |
| 署名 | 棕皮书皮面板，填书名和署名 |
| 设置 | 中英文切换、横线、行距、字号（1× / 2× / 3×）、墨水颜色，都带预览 |

## 几个自己比较满意的地方

**翻页是真的翻。** 纸有正反两面，翻过去的时候宽度按 cos θ 收窄，带缓动。
不是把书页横向挪一下糊弄过去的。

**中文和英文用同一套像素字体。** 一开始用的是 Monocraft，它只有拉丁字形，
中文会掉到系统字体上——结果就是一堆像素字里混几个平滑字，看着特别难受。
后来换成缝合像素字体，中英文都是 12px 像素风，才对得上。

**写满一页自动进下一页。** 页数没上限，不滚动也不截断，往下写就到了。

**署名之后照样能改。** 原版那套签完名就锁死，我觉得不好用，改成签完只是个名字。

## 跟系统记事本差在哪

|  | 记事本 | 这个 |
|---|---|---|
| 界面 | 白底黑字 | 木框 + 像素中文 |
| 多本书 | 开一堆窗口 | 一个书架 |
| 保存 | 得记着按 Ctrl+S | 切页、切界面、关窗的时候自动写 |
| 搜索 | 全文找 | 按书名过滤书架 |

不是说记事本不好——随手记两句用记事本更快。
这个是给想正经写点东西、而且喜欢那个书页的人用的。

## 跑起来

需要 Python 3.10 以上，而且得带 tkinter：

```bat
pythonw "MC Notepad.py"
```

或者双击 `启动 MC Notepad.vbs`，不弹黑窗。

几个容易踩的：

- **用 `pythonw` 不是 `python`。** 后者会在后台挂一个黑窗，要关掉程序才消失。
- **确认有 tkinter**：`python -c "import tkinter"` 不报错就是有。安装时漏了组件，
  或者用的是 Microsoft Store 版（在 `WindowsApps` 里，权限受限）都会没这个模块。

clone 下来直接跑，第三方库一个都不用装。

### 出了问题怎么办

| 现象 | 多半是 |
|---|---|
| 双击没反应 | 缺 tkinter，或者中文路径下 `pythonw.exe` 权限被拦。命令行跑一遍看报错最直接 |
| 字糊成马赛克 | 缩放比例跟像素字体的整数倍对不上。Win11 设置 → 系统 → 显示 → 缩放，试试 100% / 125% / 150% |
| 设置乱了 | `%LOCALAPPDATA%\MC Notepad` 整个删掉就恢复默认 |

## 打包成 exe

用 PyInstaller，**必须 onedir，别用 onefile**（原因在下面）：

```bat
python -m venv .buildenv
.buildenv\Scripts\pip install pyinstaller
.buildenv\Scripts\python -m PyInstaller --noconfirm --onedir --windowed ^
  --name "MC Notepad" --icon assets/img/icon.ico ^
  --add-data "assets/fonts/FusionPixel12-zh_hans.ttf;assets/fonts" ^
  --add-data "assets/img/icon.png;assets/img" ^
  --distpath dist --workpath build2 "MC Notepad.py"
```

成品在 `dist\MC Notepad\MC Notepad.exe`。

重新打包之前先把 `dist\MC Notepad` 改名挪走再构建。PyInstaller 构建时会 rmtree
整个产物目录，一删就是一千多个文件。书不在那儿（见下），没必要让它删。

### 为什么不用 onefile

量过。onefile 每次启动要解压 13MB，冷启动 6 秒；关窗之后父进程还会卡 30 秒以上
退不出来——临时目录里的 `_tkinter.pyd`、`_tk_data`、`_tcl_data` 在子进程刚退出、
句柄还没释放的时候删不掉。内存从 11MB 涨到 66MB，`%TEMP%` 里留一堆 `_MEI*` 目录。

onedir 冷启动 1.2 秒，关窗 0.25 秒，退出码 0，什么都不剩。

## 数据在哪

```
%LOCALAPPDATA%\MC Notepad\
    library.json     所有书
    settings.json    语言、排序、横线、行距、字号、墨色
```

故意不放 exe 旁边。PyInstaller 每次重建都会把产物目录删掉重建，书放那儿
等于每次打包格式化一次书架。

备份或者换机器，直接把这个文件夹拷走。

调试的时候可以用 `MCBUKU_DATA` 环境变量把数据指到别处，这样测试脚本不会碰到真数据。

## 素材和许可

| 内容 | 许可 / 归属 |
|---|---|
| 代码 | MIT，见 `LICENSE` |
| 字体 `FusionPixel12-zh_hans.ttf` | 缝合像素字体，SIL OFL 1.1，见 `assets/fonts/FusionPixel-OFL.txt` |
| 图标 `icon.png` / `icon.ico` | 从一张 Minecraft「书与笔」图标图里抠出来的（去掉灰底，留红皮书和白羽毛）。Minecraft 相关的东西版权归 Mojang AB，这里只作致敬和学习用，非商业用途。有问题请联系删除 |
| 背景壁纸 | 没放进仓库（来自 Wallpaper Engine，作者和授权都还没确认） |

没有背景图程序会退回程序化木地板，功能一点不受影响。想要壁纸版的话，
自己放 `bg_760x600.png` 和 `bg_1140x900.png` 到 `assets/img/`，
尺寸就是窗口逻辑尺寸乘 DPI 缩放。

## 已知问题

- 像素字体得按整数倍渲染才不糊，所以字号只有 1× / 2× / 3× 三档。
- 高 DPI 下字号是从纸面高度反推的，折行按像素宽度算，不是按字数。
- 只做了 Windows。DPI 感知、字体注册、打包都依赖 Win32 API。
- 代码里有 21 个 `except Exception` 兜底。想法是"界面绝对不能崩"，代价是
  出错了不会告诉你。最要命的是 `save_now()`——写盘失败会被静静吞掉，
  你以为存了其实没存。排查问题的时候先把这些改成 `print` 看看具体是什么异常。
  这是这个项目最该改的地方。
- 书没加密，也没云同步。明文 JSON 放在本地，谁拿到你电脑谁就能看。

## 想改点东西

代码大致分层是这样，找东西不用从头读：

| 想改 | 去哪儿 |
|---|---|
| 界面长什么样 | `self._draw_*`，18 个，全是 Canvas 手绘坐标 |
| 中英文文案 | `STRINGS` 字典 + `self.t(key)` |
| 读写数据 | `load_settings()` / `save_settings()` 在模块顶层；`self.save_now()` 管书，原子写盘（`os.replace`） |
| 翻页动画 | `_flip_pages()` 管状态，`_animate_flip()` 驱动帧，`_draw_flip_frame()` 画过渡 |
| 配色、尺寸 | 文件开头的常量区，`SHELF_W` / `SHELF_H` / `PLANK_W` 之类 |

有个坑先提一下：**点击热区走 `_hotspots` 矩形表**（`_hot()` 登记），别依赖 canvas
图元的标签命中——自绘的图形经常点不中。
