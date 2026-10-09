# -*- coding: utf-8 -*-
"""
书与笔 · Windows 桌面记事本
复刻 Minecraft 原版「书与笔」的观感。

界面（同一个窗口内切换）：
  · 书架  —— 顶栏 + 木牌书列
  · 书页  —— 木质书框内左右跨页，每页顶部页码，
             右下角四个图标（上一页 / 新建页 / 删除页 / 下一页），左下角笔，右下角卷角
  · 署名  —— 棕色书皮面板「输入书名 / 作者 / 注意…」+ 署名并关闭 / 取消
  · 设置  —— 语言切换（中文 / English）

· 页数无上限
· 署名只是起名字，不锁内容，随时可改
· 单文件、零第三方依赖
"""

import ctypes
import json
import math
import os
import sys
import time
import uuid
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

# ---------------------------------------------------------------- DPI 感知
# 必须在创建任何窗口之前声明，否则 150% 缩放下像素字会被位图拉伸，糊成一团。
try:
    ctypes.windll.shcore.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# 打包成 exe 后：程序资源跟着 exe 走（onefile 解压到 _MEIPASS，onedir 就是 _internal），
# 用户数据另存他处，两边不能混 —— 见下面的 DATA_DIR。
FROZEN = bool(getattr(sys, "frozen", False))
ASSET_DIR = (getattr(sys, "_MEIPASS", None) or APP_DIR) if FROZEN else APP_DIR
# 正文/界面字体。Monocraft 只有拉丁字形，中文会掉到系统字体上 —— 一个像素字一个平滑字，
# 放一起很打架。所以换成「缝合像素字体」：它本身就是照 MC 做的像素风，且带完整中文。
# 要退回 Monocraft 就把下面这行换成 Monocraft.ttc / "Monocraft"。
FONT_PATH = os.path.join(ASSET_DIR, "assets", "fonts", "FusionPixel12-zh_hans.ttf")
FONT_NAME = "Fusion Pixel 12px Mono zh-Hans"
FONT_DESIGN_PX = 12        # 上面这套字体的设计像素高（名字里的 12px）
DEFAULT_LINE_GAP = 5       # 默认行距（逻辑像素）；设置里可调
TEXT_TOP = 34              # 正文距纸面上沿（逻辑像素）。收紧一点，好让 3 倍字号也放得下 13 行
INK_COLORS = ("#2b2216", "#141414", "#2e3d5c", "#2c4a30", "#7a2a22", "#4a2a5a")
MONOCRAFT_PATH = os.path.join(ASSET_DIR, "assets", "fonts", "Monocraft.ttc")
ICON_PNG = os.path.join(ASSET_DIR, "assets", "img", "icon.png")


def _user_data_dir():
    """书放哪儿：统一 %LOCALAPPDATA%\\MC Notepad，源码版和 exe 版共用一份。
    **不能**放 exe 旁边 —— PyInstaller 每次重新构建会 rmtree 掉整个产物目录，书会跟着没。
    **也不能**源码版用项目旁 books/、exe 版用别处 —— 那就两份数据各写各的，
    哪天用另一种方式打开会以为书丢了。
    """
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or APP_DIR
    return os.path.join(base, "MC Notepad")


# 设了 MCBUKU_DATA 环境变量就用它 —— 测试/调试时指到临时目录，
# 免得自动化脚本把用户自己的书删掉。
DATA_DIR = os.environ.get("MCBUKU_DATA") or _user_data_dir()
LIB_PATH = os.path.join(DATA_DIR, "library.json")
SET_PATH = os.path.join(DATA_DIR, "settings.json")

# ---------------------------------------------------------------- 多语言
STRINGS = {
    "zh": {
        "app_title": "书与笔",
        "new_book": "新建书籍",
        "settings": "设置",
        "empty_hint": "还没有书。点左上角「新建书籍」写第一本。",
        "pages_fmt": "页数 : {n}",
        "author_fmt": "署名 : {a}",
        "edited_fmt": "编辑 : {d}",
        "never_edited": "尚未写过",
        "date_fmt": "%Y/%m/%d",
        "sort_desc": "日期 ↓ 新在前",
        "sort_asc": "日期 ↑ 旧在前",
        "unknown_author": "未署名",
        "untitled": "未命名",
        "new_book_name": "新书",
        "page_of": "第{a}页 / 共{b}页",
        "sign": "署名",
        "cover": "封面",
        "resign": "修改署名",
        "sign_title_label": "输入书名:",
        "author_label": "署名",
        "sign_warn": "注意!署名后仍可随时修改内容。",
        "sign_and_close": "署名并关闭",
        "cancel": "取消",
        "ok": "确定",
        "rename_title": "书名",
        "language": "语言",
        "rules_label": "页内横线",
        "gap_label": "行距",
        "size_label": "字体大小",
        "color_label": "字体颜色",
        "close": "关闭",
        "del_book_title": "删除书籍",
        "del_book_msg": "删掉《{t}》？",
        "del_pages_title": "删除",
        "del_pages_msg": "删掉当前这一页？",
        "cant_del": "删不了",
        "at_least_one": "至少要留两页，书才有得翻。",
        "export_ok": "导出成功",
        "export_ok_msg": "已导出到：\n{p}",
        "export_fail": "导出失败",
        "hint_pages": "上一页 / 新建页 / 删除页 / 下一页",
    },
    "en": {
        "app_title": "MC Notepad",
        "new_book": "New Book",
        "settings": "Settings",
        "empty_hint": "No books yet. Click \"New Book\" at the top left to start one.",
        "pages_fmt": "Pages : {n}",
        "author_fmt": "By : {a}",
        "edited_fmt": "Edited : {d}",
        "never_edited": "never edited",
        "date_fmt": "%d/%m/%Y",
        "sort_desc": "Date ↓ newest",
        "sort_asc": "Date ↑ oldest",
        "unknown_author": "Unknown",
        "untitled": "Untitled",
        "new_book_name": "New Book",
        "page_of": "Page {a} of {b}",
        "sign": "Sign",
        "cover": "Cover",
        "resign": "Edit name",
        "sign_title_label": "Enter a title:",
        "author_label": "Signed by",
        "sign_warn": "Note: you can still edit this book after naming it.",
        "sign_and_close": "Sign & Close",
        "cancel": "Cancel",
        "ok": "OK",
        "rename_title": "Title",
        "language": "Language",
        "rules_label": "Ruled lines",
        "gap_label": "Line spacing",
        "size_label": "Text size",
        "color_label": "Ink color",
        "close": "Close",
        "del_book_title": "Delete book",
        "del_book_msg": "Delete \"{t}\"?",
        "del_pages_title": "Delete",
        "del_pages_msg": "Delete this page?",
        "cant_del": "Can't delete",
        "at_least_one": "A book needs at least two pages.",
        "export_ok": "Export complete",
        "export_ok_msg": "Exported to:\n{p}",
        "export_fail": "Export failed",
        "hint_pages": "prev / new page / delete page / next",
    },
}

# ---------------------------------------------------------------- 调色板
C_COVER = "#9c6539"        # 书皮主色
C_COVER_L = "#b9855a"
C_COVER_D = "#6b3f21"
C_COVER_EDGE = "#4a2a13"
C_SPINE = "#8a5530"

C_PAPER = "#f7efdd"
C_PAPER_EDGE = "#dccaa6"
C_PAGE_NUM = "#a89b85"
C_ICON = "#c9ac7e"
C_ICON_D = "#9b7f56"
C_INK = "#2b2216"

C_WOOD = "#3a2410"
C_WOOD_SEAM = "#24140a"
C_WOOD_LINE = "#4a3018"

C_PLANK = "#b98a55"
C_PLANK_L = "#d0a473"
C_PLANK_D = "#8a6134"
C_PLANK_SEAM = "#6e4a26"

C_BTN = "#8b8b8b"
C_BTN_HI = "#c6c6c6"
C_BTN_LO = "#373737"

MAX_LINES = 13             # 单页行数（同原版书与笔）

# 布局（逻辑像素，按 DPI 缩放）
PAGE_W = 300
PAGE_H = 400
COVER = 16
BOOK_W = PAGE_W * 2 + COVER * 2
BOOK_H = PAGE_H + COVER * 2
WIN_W = 760
WIN_H = 600
SHELF_W = 760
SHELF_H = 600
ROW_H = 54
ROW_GAP = 8
PLANK_W = 150


def load_font():
    """挑一个"真的画得出来"的像素字体，按顺序试，都不行就退回等宽字体。

    坑：AddFontResourceExW 返回非 0 **不代表 GDI 能用这个字体**。
    实测「缝合像素字体」的 .ms.bitmap.ttf 变体注册成功，但一个字都画不出来
    （tkfont.measure() 全返回 0，metrics() 的 descent 是个垃圾大数）。
    所以这里注册完还要用 tkfont 实测一下才敢用。
    """
    for path, name in ((FONT_PATH, FONT_NAME), (MONOCRAFT_PATH, "Monocraft")):
        if not os.path.exists(path):
            continue
        try:
            if not ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0):
                continue
        except Exception:
            continue
        try:
            probe = tkfont.Font(family=name, size=12)
            m = probe.metrics()
            if (m.get("linespace") or 0) > 1000:      # 度量溢出 = GDI 不认
                continue
            if probe.measure("中A") <= 0:             # 量不出宽度 = 画不出来
                continue
        except Exception:
            continue
        return name
    return "Courier New"


# ---------------------------------------------------------------- 数据层
class Library:
    """所有书存在一个 library.json 里，整份原子写盘。"""

    def __init__(self, path=LIB_PATH):
        self.path = path
        self.books = []
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.books = [b for b in d.get("books", []) if isinstance(b, dict)]
                for b in self.books:
                    b.setdefault("id", uuid.uuid4().hex[:12])
                    b.setdefault("title", "")
                    b.setdefault("author", "")
                    b.setdefault("signed", False)
                    b.setdefault("pages", [[], []])
                    b.setdefault("updated", 0)
                return
            except Exception:
                pass
        self.books = []

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"books": self.books}, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def add(self, title):
        b = {"id": uuid.uuid4().hex[:12], "title": title, "author": "",
             "signed": False, "pages": [[], []], "updated": time.time()}
        self.books.append(b)
        return b

    def remove(self, bid):
        self.books = [b for b in self.books if b["id"] != bid]

    def get(self, bid):
        for b in self.books:
            if b["id"] == bid:
                return b
        return None


def load_settings():
    if os.path.exists(SET_PATH):
        try:
            with open(SET_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("lang") in STRINGS:
                d.setdefault("sort_desc", True)
                d.setdefault("show_rules", False)
                d.setdefault("line_gap", DEFAULT_LINE_GAP)
                return d
        except Exception:
            pass
    return {"lang": "zh", "sort_desc": True, "show_rules": False,
            "line_gap": DEFAULT_LINE_GAP}


def save_settings(d):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(SET_PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------- 主程序
class App:
    def __init__(self, root):
        self.root = root
        self.lib = Library()
        self.settings = load_settings()
        self.lang = self.settings["lang"]
        self.sort_desc = bool(self.settings.get("sort_desc", True))
        self.show_rules = bool(self.settings.get("show_rules", False))
        self.line_gap = int(self.settings.get("line_gap", DEFAULT_LINE_GAP))
        self.font_scale = int(self.settings.get("font_scale", 2))
        self.ink = self.settings.get("ink_color", C_INK)
        if self.ink not in INK_COLORS:
            self.ink = C_INK
        self.font_family = load_font()
        self.scale = self._dpi_scale()
        self.screen = None
        self.current = None
        self.spread = 0               # 跨页号：0 =「封面|第1页」，s≥1 =「第2s页|第2s+1页」
        self.focus_side = "r"
        self.search = ""
        self.anim_dx = 0
        self._animating = False
        self._bg_img = None
        self._rename_bid = None
        self._hotspots = []
        self._float_widgets = []
        self._page_entries = []
        self._entry_wins = []

        self._setup_window()
        self._measure_font()
        self.show_shelf()

    # ------------------------------------------------------------ 基础
    def t(self, key, **kw):
        s = STRINGS.get(self.lang, STRINGS["zh"]).get(key, key)
        return s.format(**kw) if kw else s

    def fmt_time(self, ts):
        """最后编辑时间。日期格式随语言走：中文 yyyy/mm/dd，英文 dd/mm/yyyy。"""
        if not ts:
            return self.t("never_edited")
        try:
            lt = time.localtime(ts)
            return time.strftime(self.t("date_fmt"), lt) + " " + time.strftime("%H:%M", lt)
        except Exception:
            return self.t("never_edited")

    def set_lang(self, lang):
        if lang not in STRINGS:
            return
        self.lang = lang
        self.settings["lang"] = lang
        save_settings(self.settings)
        self.root.title(self.t("app_title"))
        self._measure_font()
        # 每个界面都要跟着重建。漏一个，那个界面就会停在旧语言上
        # （语言按钮自己就在设置界面里，漏了它等于点了没反应）。
        if self.screen == "shelf":
            self.show_shelf()
        elif self.screen == "book":
            self.show_book()
        elif self.screen == "sign":
            self.show_sign()
        elif self.screen == "settings":
            self.show_settings()
        elif self.screen == "rename" and self._rename_bid:
            self.show_rename(self._rename_bid)

    @staticmethod
    def _dpi_scale():
        try:
            return ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            return 1.0

    def S(self, v):
        return int(round(v * self.scale))

    def _font(self, size, weight="normal"):
        return tkfont.Font(family=self.font_family,
                           size=max(6, int(round(size * self.scale))), weight=weight)

    def _font_px(self, px, weight="normal"):
        """要一个"渲染出来正好 px 像素高"的字体。
        Tk 的 size 参数是点(pt)：px = pt * dpi/72，dpi = 96*scale。"""
        pt = px * 72.0 / (96.0 * self.scale)
        return tkfont.Font(family=self.font_family, size=max(4, int(round(pt))),
                           weight=weight)

    def _px_to_size(self, px):
        """把像素高换算成 _font() 习惯用的那个"size"值（给它乘 scale 后变点）。"""
        return max(4, int(round(px * 3.0 / (4.0 * self.scale * self.scale))))

    def _setup_window(self):
        self.root.title(self.t("app_title"))
        self.root.configure(bg=C_WOOD_SEAM)
        self.root.resizable(False, False)
        try:
            self.icon_img = tk.PhotoImage(file=ICON_PNG)
            self.root.iconphoto(True, self.icon_img)
        except Exception:
            self.icon_img = None
        self.canvas = tk.Canvas(self.root, bg=C_WOOD_SEAM, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_click)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-s>", lambda e: (self.save_now(), "break")[1])
        self.root.bind("<Control-e>", lambda e: (self.export_txt(), "break")[1])

    def _measure_font(self):
        """定正文（纸面上的字）字号。底部要留出图标行和折角，别让输入框盖住它们。"""
        S = self.S
        avail = (S(PAGE_H) - S(TEXT_TOP) - S(52)) / MAX_LINES
        if self.font_family == FONT_NAME:
            # 像素字体只有按设计尺寸的**整数倍**渲染才清晰：
            # 非整数倍时一个设计像素会被拉成 1.5 格、2.5 格，边就糊了。
            # 所以不去"按高度能塞多大就多大"，而是在整数倍里挑最大的那个能放下的。
            picked = None
            want = max(1, min(3, int(self.font_scale)))
            # 先按用户选的倍数；万一 13 行放不下就往下退
            for k in (want, 3, 2, 1):
                f = self._font_px(FONT_DESIGN_PX * k)
                if f.metrics("linespace") <= avail:
                    picked = (k, f)
                    break
            if picked is None:
                picked = (1, self._font_px(FONT_DESIGN_PX))
            self.font_scale = picked[0]
            self.body_px = FONT_DESIGN_PX * picked[0]
            self.body_font = picked[1]
            self.body_size = self._px_to_size(self.body_px)
        else:
            size = 12
            while size > 5:
                f = self._font(size)
                if f.metrics("linespace") <= avail:
                    break
                size -= 1
            # 按高度反推出来的是"最大能塞下"的字号，中文偏挤，再降一档才舒服。
            size = max(5, size - 1)
            self.body_size = size
            self.body_font = self._font(size)
            self.body_px = 0
        # 行距：正文行高 = 字体行高 + 行距。设置里可调（横线间距就是它）。
        # 输入框那边要靠 spacing3 加同样的空隙，否则画布文字和输入框会错行。
        self.font_linespace = self.body_font.metrics("linespace")
        self.line_gap = max(0, min(self.line_gap, self.max_line_gap()))
        self.LINE_GAP = S(self.line_gap)
        self.LINE_H = self.font_linespace + self.LINE_GAP
        self.text_w = S(PAGE_W) - S(30) * 2

    def max_line_gap(self):
        """行距上限：13 行必须还塞得进纸面。返回逻辑像素。"""
        S = self.S
        avail = S(PAGE_H) - S(TEXT_TOP) - S(52)
        room = avail - getattr(self, "font_linespace", S(24)) * MAX_LINES
        return max(0, int(room / MAX_LINES / self.scale))

    def set_line_gap(self, v):
        """设置界面里拖滑块时调用：改行距、存档、重画预览。不重建界面（否则滑块会被销毁）。"""
        try:
            v = int(round(float(v)))
        except Exception:
            return
        v = max(0, min(self.max_line_gap(), v))
        self.line_gap = v
        self.settings["line_gap"] = v
        save_settings(self.settings)
        # 立刻按新行距重算行高，预览才是准的
        self.LINE_GAP = self.S(v)
        self.LINE_H = self.font_linespace + self.LINE_GAP
        try:
            self.canvas.itemconfigure(self._gap_val_id, text=str(v))
        except Exception:
            pass
        if hasattr(self, "_preview_box"):
            self.canvas.delete("preview")
            self._draw_gap_preview(*self._preview_box)

    def _draw_gap_preview(self, x, y, w, h):
        """行距预览：几道横线 + 一行样字，边拖边看。"""
        S = self.S
        c = self.canvas
        c.create_rectangle(x, y, x + w, y + h, fill=C_PAPER,
                           outline=C_COVER_EDGE, width=max(1, S(1)), tags="preview")
        top = y + S(12)
        for i in range(4):
            yy = top + (i + 1) * self.LINE_H
            if yy > y + h - S(6):
                break
            c.create_line(x + S(10), yy, x + w - S(10), yy,
                          fill="#ddd0b0", tags="preview")
        for i in range(2):
            yy = top + i * self.LINE_H
            if yy + self.LINE_H > y + h:
                break
            c.create_text(x + S(10), yy + S(4), anchor="nw",
                          text="今天下午没课" if i == 0 else "去操场跑了三圈",
                          fill=self.ink, font=self.body_font, tags="preview")

    def _resize(self, w, h):
        S = self.S
        W, H = S(w), S(h)
        self.canvas.config(width=W, height=H)
        self.root.geometry(f"{W}x{H}")
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{max(0, (sw - W) // 2)}+{max(0, (sh - H) // 2 - S(30))}")
        self.win_w, self.win_h = W, H

    def _clear_widgets(self):
        for w in list(self._float_widgets) + list(self._page_entries):
            try:
                w.destroy()
            except Exception:
                pass
        self._float_widgets = []
        self._page_entries = []
        self._entry_wins = []
        self._rule_bars = []
        self.anim_dx = 0
        self._animating = False

    def _new_screen(self, name):
        self._clear_widgets()
        self.canvas.delete("all")
        self._hotspots = []
        self.screen = name

    # ------------------------------------------------------------ 绘制工具
    def _stone_button(self, text, cmd):
        S = self.S
        b = tk.Button(self.canvas, text=text, command=cmd,
                      bg=C_BTN, fg="#ffffff", activebackground=C_BTN_HI,
                      activeforeground="#ffffff", font=self._font(10),
                      relief="solid", bd=S(1), highlightthickness=S(2),
                      highlightbackground=C_BTN_LO, padx=S(6), pady=S(2),
                      cursor="hand2", disabledforeground="#a8a8a8")
        self._float_widgets.append(b)
        return b

    def _draw_world(self):
        """背景：优先用 MC 壁纸，没有就退回程序化木地板。画一次（tag=world）。"""
        S = self.S
        c = self.canvas
        before = set(c.find_all())
        W, H = self.win_w, self.win_h

        img = None
        bg = os.path.join(ASSET_DIR, "assets", "img", f"bg_{W}x{H}.png")
        if os.path.exists(bg):
            try:
                img = tk.PhotoImage(file=bg)
                if img.width() < W or img.height() < H:
                    img = None
            except Exception:
                img = None
        self._bg_img = img

        if img is not None:
            # 压暗与暗角已经烘焙进图里了，这里直接铺，不再叠半透明网点（会有抖动噪点）
            c.create_image(0, 0, image=img, anchor="nw")
        else:
            c.create_rectangle(0, 0, W, H, fill=C_WOOD, outline="")
            ph = S(17)
            shades = ("#4a3018", "#452c15", "#503419", "#422a14", "#4d3217")
            row, y = 0, 0
            while y < H:
                c.create_rectangle(0, y, W, y + ph, fill=shades[row % len(shades)], outline="")
                c.create_line(0, y + 1, W, y + 1, fill="#5c3e20", width=1)
                c.create_line(0, y + ph - 1, W, y + ph - 1, fill="#2a1809", width=1)
                x = (row * S(97)) % S(232) - S(232)
                while x < W:
                    c.create_line(x, y + 1, x, y + ph - 1, fill="#3a2410", width=1)
                    x += S(232)
                y += ph
                row += 1
            # 没有背景图时才自己画暗角
            for a, b, st in ((0, S(10), "gray50"), (S(10), S(26), "gray25"), (S(26), S(48), "gray12")):
                if b <= a:
                    continue
                c.create_rectangle(a, a, W - a, b, fill="#000000", outline="", stipple=st)
                c.create_rectangle(a, H - b, W - a, H - a, fill="#000000", outline="", stipple=st)
                c.create_rectangle(a, b, b, H - b, fill="#000000", outline="", stipple=st)
                c.create_rectangle(W - b, b, W - a, H - b, fill="#000000", outline="", stipple=st)
        for it in set(c.find_all()) - before:
            c.addtag_withtag("world", it)

    def _draw_plank(self, x, y, w, h):
        """MC 橡木木板：横向木条 + 错缝 + 高光/阴影。"""
        S = self.S
        c = self.canvas
        c.create_rectangle(x, y, x + w, y + h, fill=C_PLANK_D, outline="")
        rows = 4
        rh = h / rows
        for i in range(rows):
            yy = y + rh * i
            c.create_rectangle(x + 1, yy + 1, x + w - 1, yy + rh - 1, fill=C_PLANK, outline="")
            c.create_line(x + 1, yy + 1, x + w - 1, yy + 1, fill=C_PLANK_L)
            c.create_line(x + 1, yy + rh - 2, x + w - 1, yy + rh - 2, fill=C_PLANK_D)
            seam = x + ((i * 61) % max(1, int(w - 24))) + 12
            c.create_line(seam, yy + 1, seam, yy + rh - 1, fill=C_PLANK_SEAM)
        c.create_rectangle(x, y, x + w, y + h, fill="", outline=C_PLANK_SEAM, width=max(1, S(1)))

    def _draw_cover_art(self, x, y, w, h, tag=None):
        """封面：画成书皮那个样子，填满左半边。"""
        S = self.S
        c = self.canvas
        kw = {"tags": tag} if tag else {}
        c.create_rectangle(x, y, x + w, y + h, fill=C_COVER_EDGE, outline="", **kw)
        c.create_rectangle(x + S(2), y + S(2), x + w - S(2), y + h - S(2),
                           fill=C_COVER, outline="", **kw)
        c.create_rectangle(x + S(2), y + S(2), x + S(20), y + h - S(2),
                           fill=C_SPINE, outline="", **kw)
        c.create_line(x + S(20), y + S(3), x + S(20), y + h - S(3),
                      fill=C_COVER_D, **kw)
        c.create_line(x + S(3), y + S(3), x + w - S(4), y + S(3), fill=C_COVER_L, **kw)
        c.create_line(x + S(3), y + S(3), x + S(3), y + h - S(4), fill=C_COVER_L, **kw)
        c.create_line(x + S(3), y + h - S(3), x + w - S(4), y + h - S(3),
                      fill=C_COVER_D, **kw)
        tx = x + w / 2 + S(8)
        c.create_text(tx, y + h * 0.42,
                      text=(self.current.get("title") or "").strip() or self.t("untitled"),
                      fill="#f3ead6", font=self._font(12),
                      width=w - S(80), justify="center", **kw)
        c.create_text(tx, y + h * 0.42 + S(62),
                      text=self.t("author_fmt",
                                  a=((self.current.get("author") or "").strip()
                                     or self.t("unknown_author"))),
                      fill="#dfd0b2", font=self._font(9), **kw)

    def _draw_paper_stack(self, px, py, pw, ph, side):
        """纸张堆叠：外缘竖着码一列长短不一的小方块，做出一沓纸的侧边感。
        颜色要比纸面明显深一档，否则整片糊在一起看不出来。
        用 (i*53)%17 这种确定性伪随机，保证每次重画花纹都一样、不会闪。"""
        S = self.S
        c = self.canvas
        w1 = S(11)
        w2 = S(6)
        i = 0
        yy = py
        while yy < py + ph:
            hh = min(S(9 + (i * 53) % 19), py + ph - yy)
            if hh <= 0:
                break
            base = "#e8d6ae" if i % 3 else "#cfb98c"
            if side == "l":
                c.create_rectangle(px, yy, px + w1, yy + hh, fill=base, outline="")
                c.create_line(px, yy, px + w1, yy, fill="#b9a273")          # 每张纸的分界
                if i % 4 == 1:
                    c.create_rectangle(px + w1, yy + S(2), px + w1 + w2, yy + hh - S(2),
                                       fill="#c2ab7d", outline="")
            else:
                c.create_rectangle(px + pw - w1, yy, px + pw, yy + hh, fill=base, outline="")
                c.create_line(px + pw - w1, yy, px + pw, yy, fill="#b9a273")
                if i % 4 == 1:
                    c.create_rectangle(px + pw - w1 - w2, yy + S(2), px + pw - w1,
                                       yy + hh - S(2), fill="#c2ab7d", outline="")
            yy += hh
            i += 1

    def _draw_page(self, x, y, w, h, page_no, total, side):
        """一页纸：纸面 + 外缘纸张堆叠 + 可选横线 + 下角折角 + 顶部页码。"""
        S = self.S
        c = self.canvas
        c.create_rectangle(x, y, x + w, y + h, fill=C_PAPER, outline="")
        self._draw_paper_stack(x, y, w, h, side)

        # 页内横线（设置里可开关），每行一条，位置跟书写行对齐
        if getattr(self, "show_rules", False):
            rx0 = x + S(30)
            rx1 = rx0 + self.text_w
            for i in range(MAX_LINES):
                yy = y + S(TEXT_TOP) + (i + 1) * self.LINE_H - S(4)
                if yy > y + h - S(10):
                    break
                c.create_line(rx0, yy, rx1, yy, fill="#ddd0b0")

        # 下角折角（左右严格对称的狗耳朵）：
        # 先把角"掀掉"露出书皮，再画出翻折过来的那一小块纸背，最后压一道折痕
        cs = S(24)
        if side == "r":
            px, pz = x + w, y + h
            c.create_polygon(px - cs, pz, px, pz, px, pz - cs,
                             fill=C_COVER, outline="")
            c.create_polygon(px - cs, pz, px, pz - cs, px - cs, pz - cs,
                             fill="#eadfc4", outline=C_ICON_D)
            c.create_line(px - cs, pz, px, pz - cs, fill=C_ICON_D)
        else:
            px, pz = x, y + h
            c.create_polygon(px + cs, pz, px, pz, px, pz - cs,
                             fill=C_COVER, outline="")
            c.create_polygon(px + cs, pz, px, pz - cs, px + cs, pz - cs,
                             fill="#eadfc4", outline=C_ICON_D)
            c.create_line(px + cs, pz, px, pz - cs, fill=C_ICON_D)

        c.create_text(x + w / 2, y + S(20),
                      text=self.t("page_of", a=page_no, b=total),
                      fill=C_PAGE_NUM, font=self._font(9))

    def _draw_icon_new(self, x, y, s):
        S = self.S
        c = self.canvas
        c.create_rectangle(x, y, x + s * 0.7, y + s, outline=C_ICON, width=max(1, S(2)))
        c.create_line(x + s * 0.14, y + s * 0.28, x + s * 0.56, y + s * 0.28, fill=C_ICON)
        c.create_line(x + s * 0.14, y + s * 0.52, x + s * 0.56, y + s * 0.52, fill=C_ICON)
        c.create_line(x + s * 0.14, y + s * 0.76, x + s * 0.38, y + s * 0.76, fill=C_ICON)
        cx = x + s * 0.88
        c.create_line(cx, y + s * 0.42, cx, y + s, fill=C_ICON, width=max(1, S(2)))
        c.create_line(cx - s * 0.28, y + s * 0.71, cx + s * 0.28, y + s * 0.71,
                      fill=C_ICON, width=max(1, S(2)))

    def _draw_icon_trash(self, x, y, s):
        S = self.S
        c = self.canvas
        w1 = max(1, S(2))
        c.create_line(x + s * 0.08, y + s * 0.2, x + s * 0.92, y + s * 0.2, fill=C_ICON, width=w1)
        c.create_line(x + s * 0.36, y + s * 0.08, x + s * 0.64, y + s * 0.08,
                      fill=C_ICON, width=w1)
        c.create_polygon(x + s * 0.16, y + s * 0.28, x + s * 0.84, y + s * 0.28,
                         x + s * 0.72, y + s, x + s * 0.28, y + s,
                         fill="", outline=C_ICON, width=w1)
        c.create_line(x + s * 0.4, y + s * 0.42, x + s * 0.4, y + s * 0.86, fill=C_ICON)
        c.create_line(x + s * 0.6, y + s * 0.42, x + s * 0.6, y + s * 0.86, fill=C_ICON)

    def _draw_pencil(self, x, y, s):
        S = self.S
        c = self.canvas
        c.create_polygon(x, y + s, x + s * 0.26, y + s * 0.74, x + s * 0.74, y + s * 0.26,
                         x + s, y + s * 0.5, x + s * 0.5, y + s,
                         fill=C_PAPER_EDGE, outline="#efe6d4", width=max(1, S(1)))

    def _draw_gear(self, x, y, s):
        """设置齿轮。"""
        S = self.S
        c = self.canvas
        cx, cy, r = x + s / 2, y + s / 2, s * 0.34
        for i in range(8):
            a = i * math.pi / 4
            c.create_line(cx + math.cos(a) * r, cy + math.sin(a) * r,
                          cx + math.cos(a) * (r + s * 0.2),
                          cy + math.sin(a) * (r + s * 0.2),
                          fill="#e8dcc0", width=max(2, S(3)))
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#e8dcc0",
                      width=max(1, S(2)))
        c.create_oval(cx - r * 0.34, cy - r * 0.34, cx + r * 0.34, cy + r * 0.34,
                      fill="#e8dcc0", outline="")

    def _draw_book_frame(self, x, y, w, h):
        S = self.S
        c = self.canvas
        c.create_rectangle(x, y, x + w, y + h, fill=C_COVER_EDGE, outline="")
        c.create_rectangle(x + S(2), y + S(2), x + w - S(2), y + h - S(2),
                           fill=C_COVER, outline="")
        c.create_line(x + S(3), y + S(3), x + w - S(4), y + S(3), fill=C_COVER_L)
        c.create_line(x + S(3), y + S(3), x + S(3), y + h - S(4), fill=C_COVER_L)
        c.create_line(x + S(3), y + h - S(3), x + w - S(4), y + h - S(3), fill=C_COVER_D)
        c.create_line(x + w - S(3), y + S(3), x + w - S(3), y + h - S(4), fill=C_COVER_D)

    def _draw_panel(self, cx, cy, cw, ch):
        """棕色书皮面板（署名 / 重命名 / 设置共用）。"""
        S = self.S
        c = self.canvas
        c.create_rectangle(cx, cy, cx + cw, cy + ch, fill=C_COVER_EDGE, outline="")
        c.create_rectangle(cx + S(2), cy + S(2), cx + cw - S(2), cy + ch - S(2),
                           fill=C_COVER, outline="")
        c.create_rectangle(cx + S(2), cy + S(2), cx + S(24), cy + ch - S(2),
                           fill=C_SPINE, outline="")
        c.create_line(cx + S(24), cy + S(3), cx + S(24), cy + ch - S(3), fill=C_COVER_D)
        c.create_line(cx + S(3), cy + S(3), cx + cw - S(4), cy + S(3), fill=C_COVER_L)
        c.create_line(cx + S(3), cy + S(3), cx + S(3), cy + ch - S(4), fill=C_COVER_L)
        c.create_line(cx + S(3), cy + ch - S(3), cx + cw - S(4), cy + ch - S(3), fill=C_COVER_D)
        x2, y2 = cx + cw - S(26), cy + S(24)
        c.create_line(x2 - S(7), y2 - S(7), x2 + S(7), y2 + S(7), fill="#3a2612",
                      width=max(1, S(2)))
        c.create_line(x2 + S(7), y2 - S(7), x2 - S(7), y2 + S(7), fill="#3a2612",
                      width=max(1, S(2)))
        c.create_rectangle(x2 - S(15), y2 - S(15), x2 + S(15), y2 + S(15),
                           fill="", outline="", tags="sign:cancel")

    # ============================================================ 书架界面
    def show_shelf(self):
        self.save_now()
        self._new_screen("shelf")
        self._resize(SHELF_W, SHELF_H)
        self._hotspots = []
        self._draw_world()
        self._draw_shelf_top()
        self._draw_shelf_rows()

    def _draw_shelf_top(self):
        S = self.S
        c = self.canvas
        W = self.win_w
        bar = S(50)
        c.create_rectangle(0, 0, W, bar, fill="#2e1c0d", outline="")
        c.create_line(0, bar - S(2), W, bar - S(2), fill="#1a0f05", width=max(1, S(2)))
        c.create_line(0, S(1), W, S(1), fill="#4a3018")

        b = self._stone_button(self.t("new_book"), self.new_book)
        c.create_window(S(14), S(8), window=b, anchor="nw", width=S(120), height=S(34))

        # 排序按钮宽度按文字实测，中英文都不会被截断
        self._sort_btn = self._stone_button(self.sort_label(), self.toggle_sort)
        sb_w = self._font(10).measure(self.sort_label()) + S(26)
        sb_x = S(144)
        c.create_window(sb_x, S(8), window=self._sort_btn, anchor="nw",
                        width=sb_w, height=S(34))

        self.search_var = tk.StringVar(value=self.search)
        e = tk.Entry(self.canvas, textvariable=self.search_var, font=self._font(10),
                     bg="#0d0d0d", fg="#e6e6e6", insertbackground="#e6e6e6",
                     relief="solid", bd=S(1), highlightthickness=S(1),
                     highlightbackground="#8a8a8a", justify="left")
        e.bind("<KeyRelease>", lambda ev: self._on_search())
        self._float_widgets.append(e)
        sx = sb_x + sb_w + S(18)
        sw = max(S(180), (W - S(112) - S(20)) - sx)
        c.create_window(sx, S(9), window=e, anchor="nw", width=sw, height=S(32))

        # 设置齿轮
        gx, gy, gs = W - S(112), S(13), S(24)
        self._draw_gear(gx, gy, gs)
        self._hot(gx - S(6), gy - S(6), gx + gs + S(6), gy + gs + S(6), "settings")

        ax, ay, r = W - S(40), S(25), S(13)
        c.create_oval(ax - r, ay - r, ax + r, ay + r, fill="#f2f2f2", outline="#b0b0b0")

    def _draw_shelf_rows(self):
        S = self.S
        c = self.canvas
        W = self.win_w
        y = S(66)
        shown = 0
        books = sorted(self.lib.books,
                       key=lambda b: b.get("updated") or 0,
                       reverse=self.sort_desc)
        for b in books:
            title = b.get("title") or self.t("untitled")
            if self.search and self.search.lower() not in title.lower():
                continue
            if y + S(ROW_H) > self.win_h - S(10):
                break
            self._draw_plank(S(20), y, S(PLANK_W), S(ROW_H))
            c.create_text(S(20) + S(PLANK_W) / 2, y + S(ROW_H) / 2,
                          text=title[:14], fill="#3b2a15", font=self._font(10))

            tx = S(20) + S(PLANK_W) + S(26)
            c.create_text(tx, y + S(16), anchor="w",
                          text=(self.t("pages_fmt", n=len(b.get("pages") or [])) +
                                "     " + self.t("author_fmt",
                                                 a=(b.get("author") or self.t("unknown_author")))),
                          fill="#e8dcc0", font=self._font(8))
            # 最后编辑时间独立一行，按语言格式化（中文 yyyy/mm/dd，英文 dd/mm/yyyy）
            c.create_text(tx, y + S(TEXT_TOP), anchor="w",
                          text=self.t("edited_fmt", d=self.fmt_time(b.get("updated"))),
                          fill="#c9b795", font=self._font(8))

            ic = S(18)
            self._draw_pencil(W - S(96), y + S(18), ic)
            self._hot(W - S(100), y + S(6), W - S(96) + ic + S(4), y + S(10) + ic + S(8),
                      f"edit:{b['id']}")
            self._draw_icon_trash(W - S(54), y + S(18), ic)
            self._hot(W - S(58), y + S(6), W - S(54) + ic + S(4), y + S(10) + ic + S(8),
                      f"del:{b['id']}")
            self._hot(S(10), y - S(3), W - S(130), y + S(ROW_H) + S(3), f"row:{b['id']}")
            y += S(ROW_H) + S(ROW_GAP)
            shown += 1
        if shown == 0:
            c.create_text(W / 2, S(200), text=self.t("empty_hint"),
                          fill="#c9b795", font=self._font(11))

    def _on_search(self):
        self.search = self.search_var.get().strip()
        self.canvas.delete("all")
        self._hotspots = []
        self._draw_world()
        self._draw_shelf_top()
        self._draw_shelf_rows()

    def sort_label(self):
        return self.t("sort_desc") if self.sort_desc else self.t("sort_asc")

    def toggle_sort(self):
        self.sort_desc = not self.sort_desc
        self.settings["sort_desc"] = self.sort_desc
        save_settings(self.settings)
        self.show_shelf()

    def new_book(self):
        b = self.lib.add(self.t("new_book_name"))
        self.lib.save()
        self.open_book(b["id"])

    def open_book(self, bid):
        b = self.lib.get(bid)
        if not b:
            return
        b["pages"] = b.get("pages") or [[], []]
        while len(b["pages"]) < 2:
            b["pages"].append([])          # 至少两页才能形成跨页
        self.current = b
        self.spread = 0                    # 0 =「封面 | 第1页」
        self.focus_side = "r"
        self.show_book(animate=True)

    # ============================================================ 书页界面
    def show_book(self, animate=False):
        """完整重建（首次进入 / 切语言 / 改窗口尺寸时用）。"""
        self._new_screen("book")
        self._resize(WIN_W, WIN_H)
        self.anim_dx = 0
        self._animating = False
        self._draw_world()
        self._draw_book_art()
        self._make_page_entries()
        self._make_sign_button()
        self._focus(self.focus_side)
        if animate:
            self._animate_cover(opening=True)

    def _refresh_book(self):
        """原地刷新：只重画书页图元 + 换输入框文字，不销毁控件，所以不会闪。"""
        self.canvas.delete("bookart")
        self._draw_book_art()
        self._load_entry_texts()
        self._update_sign_button()
        self._focus(self.focus_side)

    def _book_origin(self, anim=True):
        S = self.S
        dx = getattr(self, "anim_dx", 0) if anim else 0
        return ((self.win_w - S(BOOK_W)) // 2 + dx,
                (self.win_h - S(BOOK_H)) // 2 - S(28))

    def _page_rect(self, side):
        S = self.S
        bx, by = self._book_origin()
        x = bx + S(COVER) + (0 if side == "l" else S(PAGE_W))
        y = by + S(COVER)
        return x, y

    # ---- 跨页换算（照真书：封面单独占一次翻开，之后每次翻两页）----
    #   spread 0   → 封面 | 第1页   （下标 -1 | 0）
    #   spread s≥1 → 第2s页 | 第2s+1页（下标 2s-1 | 2s）
    def _left_idx(self):
        return -1 if self.spread == 0 else 2 * self.spread - 1

    def _right_idx(self):
        return 2 * self.spread

    def _side_idx(self, i):
        """i=0 左半边、i=1 右半边，返回它在 pages 里的下标（-1 = 封面）。"""
        return self._left_idx() if i == 0 else self._right_idx()

    @staticmethod
    def _spread_of(idx):
        """页下标 → 它落在哪个跨页里。"""
        return 0 if idx <= 0 else (idx + 1) // 2

    def _page_lines(self, i):
        """i=0 取左半边，i=1 取右半边。返回 [] 表示那半边不是可写的页（比如封面）。"""
        idx = self._side_idx(i)
        if 0 <= idx < len(self.current["pages"]):
            return self.current["pages"][idx]
        return []

    def _make_page_entries(self):
        """左右半边各建一个输入框（只在完整重建时调用）。
        半边是封面（页号 < 0）时不建输入框，列表里放 None 占位，保持下标好对。"""
        for w in self._page_entries:
            if w is None:
                continue
            try:
                w.destroy()
            except Exception:
                pass
        self._page_entries = []
        self._entry_wins = []
        S = self.S
        w, h = self.text_w, self.LINE_H * MAX_LINES
        for i, side in enumerate(("l", "r")):
            if self._side_idx(i) < 0:      # 封面那半边不可写
                self._page_entries.append(None)
                self._entry_wins.append(None)
                continue
            e = tk.Text(self.canvas, wrap="char", bd=0, highlightthickness=0,
                        bg=C_PAPER, fg=self.ink, insertbackground=self.ink,
                        font=self.body_font, undo=True, height=MAX_LINES,
                        selectbackground="#c9b795", selectforeground=self.ink,
                        padx=0, pady=0, spacing1=0, spacing2=0,
                        spacing3=self.LINE_GAP)
            e.bind("<KeyRelease>", lambda ev, s=side: self._on_type(s))
            e.bind("<Button-1>", lambda ev, s=side: self._focus(s))
            item = self.canvas.create_window(0, 0, window=e, anchor="nw",
                                             width=w, height=h, tags="entry")
            self._page_entries.append(e)
            self._entry_wins.append(item)
        self._load_entry_texts()
        self._place_entries()
        self._make_rules()

    def _make_rules(self):
        """页内横线。

        Tk 的输入框是真正的子窗口，永远盖在画布图元之上 —— 画在 canvas 上的线它挡得住。
        所以反过来：把横线做成输入框自己的子控件，用 place 贴上去，就画在文字之上了。
        """
        for f in getattr(self, "_rule_bars", []):
            try:
                f.destroy()
            except Exception:
                pass
        self._rule_bars = []
        if not self.show_rules:
            return
        S = self.S
        h = max(1, S(1))
        total = self.LINE_H * MAX_LINES
        for e in self._page_entries:
            if e is None:
                continue
            for i in range(MAX_LINES):
                yy = (i + 1) * self.LINE_H - S(4)
                if yy > total - S(2):
                    break
                f = tk.Frame(e, height=h, bg="#dcc9a4", bd=0, highlightthickness=0)
                f.place(x=0, y=yy, relwidth=1)
                self._rule_bars.append(f)

    def _entries_match_spread(self):
        """输入框结构是否和当前跨页匹配（左半边是不是封面，有讲究）。"""
        if len(self._page_entries) != 2:
            return False
        return (self._page_entries[0] is None) == (self.spread == 0)

    def _load_entry_texts(self):
        for i in range(len(self._page_entries)):
            e = self._page_entries[i]
            if e is None:
                continue
            e.delete("1.0", "end")
            e.insert("1.0", "\n".join(self._page_lines(i)))

    def _place_entries(self):
        S = self.S
        for i, side in enumerate(("l", "r")):
            if i >= len(self._entry_wins) or self._entry_wins[i] is None:
                continue
            px, py = self._page_rect(side)
            self.canvas.coords(self._entry_wins[i], px + S(30), py + S(TEXT_TOP))

    def _focus(self, side):
        i = 0 if side == "l" else 1
        if i < len(self._page_entries) and self._page_entries[i] is not None:
            self.focus_side = side
            self._page_entries[i].focus_set()
        else:
            # 这一半不是可写的页（封面），焦点落到另一半
            other = 1 - i
            if other < len(self._page_entries) and self._page_entries[other] is not None:
                self.focus_side = "l" if other == 0 else "r"
                self._page_entries[other].focus_set()

    # ------------------------------------------------------------ 动画
    def _anim_busy(self):
        return getattr(self, "_animating", False)

    def _animate_flip(self, d):
        """真·翻页：一整张纸绕书脊旋转过去。

        d=+1 右页翻到左边；d=-1 左页翻回右边。
        θ 从 0 → π，纸面在屏幕上的投影宽度 = PW·|cosθ|：
          前半程贴在起始侧，内容从外侧被"削"短（纸在转，透视压缩）；
          后半程落到另一侧，内容随纸展开，正好接上落地那一页。
        """
        if self._anim_busy():
            return
        self._animating = True
        # 页码、折角这些是画在 canvas 上的图元，翻页时必须跟着重画，
        # 否则会一直停在上一页画的那组数字上。
        self.canvas.delete("bookart")
        self._draw_book_art()
        self._place_entries()
        front_idx, back_idx = self._flip_pages(d)

        # 输入框是真正的子窗口，永远浮在画布图元上面，翻动的纸盖不住它。
        # 所以翻页期间把输入框藏起来，改用画布文字，动画结束再换回来。
        self._set_entries_visible(False)
        if d > 0:
            # 底下的左半边还是「翻之前那一页」，右半边已经是新跨页的右页
            self._draw_booktext(2 * self.spread - 3, 2 * self.spread)
        else:
            self._draw_booktext(2 * self.spread - 1, 2 * self.spread + 2)

        steps = 18

        def step(i=0):
            t = i / steps
            # 纸是有重量的：起手慢、中间快、落定再稳一下
            self._draw_flip_frame(d, self._lines_at(front_idx), self._lines_at(back_idx),
                                  t * t * (3 - 2 * t), last=(i >= steps))
            if i < steps:
                self.root.after(14, lambda: step(i + 1))
            else:
                self.canvas.delete("flip")
                self.canvas.delete("booktext")
                self._animating = False
                if self._entries_match_spread():
                    self._set_entries_visible(True)
                    self._load_entry_texts()
                    self._place_entries()
                else:
                    # 跨过了封面边界（左半边从封面变成正文，或反过来），
                    # 输入框结构变了，必须重建
                    self._make_page_entries()
                self._focus(self.focus_side)

        step()

    def _lines_at(self, idx):
        """取某一页折行后的显示行。页号 <0（封面）返回空。"""
        if not (0 <= idx < len(self.current["pages"])):
            return []
        out = []
        for ln in self.current["pages"][idx]:
            out.extend(self._wrap(ln))
        return out[:MAX_LINES]

    def _set_entries_visible(self, vis):
        for it in getattr(self, "_entry_wins", []):
            if it is None:
                continue
            try:
                self.canvas.itemconfigure(it, state=("normal" if vis else "hidden"))
            except Exception:
                pass

    def _draw_booktext(self, left_idx, right_idx):
        """把跨页内容画到画布上（翻页/开合书期间替身）。页号 <0 表示那半边是封面。"""
        S = self.S
        self.canvas.delete("booktext")
        for side, idx in (("l", left_idx), ("r", right_idx)):
            px, py = self._page_rect(side)
            if idx < 0:
                self._draw_cover_art(px, py, S(PAGE_W), S(PAGE_H), tag="booktext")
                continue
            for i, line in enumerate(self._lines_at(idx)):
                if not line:
                    continue
                self.canvas.create_text(px + S(30), py + S(TEXT_TOP) + i * self.LINE_H,
                                        text=line, fill=self.ink, font=self.body_font,
                                        anchor="nw", tags="booktext")
        self.canvas.tag_raise("booktext")

    def _flip_pages(self, d):
        """翻动的那张纸的两面（页下标）：(起始侧看到的正面, 落到另一侧后的背面)。

        真书里一张纸正反两页：往前翻时正面是"翻之前右页"，翻过去背面就是"新的左页"。
        """
        if d > 0:
            return 2 * self.spread - 2, 2 * self.spread - 1
        return 2 * self.spread + 1, 2 * self.spread

    def _draw_flip_frame(self, d, front_lines, back_lines, t, last=False):
        """画翻页动画在进度 t∈[0,1] 时的那一帧。
        纸有正反两面：起始侧看到的是正面，翻过去之后是背面。"""
        S = self.S
        bx, by = self._book_origin(anim=False)
        PW, PH = S(PAGE_W), S(PAGE_H)
        lx = bx + S(COVER)
        mid = lx + PW
        py = by + S(COVER)
        pad = S(30)
        top = py + S(TEXT_TOP)

        cos = math.cos(math.pi * t)
        w = PW * abs(cos)
        on_start_side = (cos >= 0) if d > 0 else (cos < 0)

        self.canvas.delete("flip")
        if w < 3 and not last:
            return

        if (d > 0) == on_start_side:
            x0, x1 = (mid, mid + w) if d > 0 else (mid - w, mid)
        else:
            x0, x1 = (mid - w, mid) if d > 0 else (mid, mid + w)

        back = not on_start_side
        paper = "#efe5cf" if back else C_PAPER

        sh = S(7)
        self.canvas.create_rectangle(x0 - sh, py, x1 + sh, py + PH,
                                     fill="#6b5a3c", outline="", stipple="gray12",
                                     tags="flip")
        self.canvas.create_rectangle(x0, py, x1, py + PH, fill=paper, outline="",
                                     tags="flip")
        # 注意：这里**不要**画横向纸纹。试过，那排横线跟正文行看着一模一样，
        # 用户会以为"翻页时凭空冒出了横线"。纸背只用略深一点的底色区分就够了。
        # 页内横线：翻动的那张纸也是"一页纸"，横线要跟着画，
        # 否则翻页时会出现"两半一边有线一边没线"的割裂感。
        # 位置和 _draw_page 里那套严格一致。
        if getattr(self, "show_rules", False) and x1 - x0 > S(20):
            for i in range(MAX_LINES):
                yy = py + S(TEXT_TOP) + (i + 1) * self.LINE_H - S(4)
                if yy > py + PH - S(8):
                    break
                self.canvas.create_line(x0, yy, x1, yy, fill="#ddd0b0", tags="flip")

        hinge_w = min(S(16), w * 0.5)
        if hinge_w > 1:
            hx0 = mid - hinge_w if x1 <= mid + 1 else mid
            self.canvas.create_rectangle(hx0, py, hx0 + hinge_w, py + PH,
                                         fill="#c9b693", outline="", stipple="gray50",
                                         tags="flip")
        self.canvas.create_line(x0, py, x0, py + PH, fill=C_PAPER_EDGE, tags="flip")
        self.canvas.create_line(x1, py, x1, py + PH, fill=C_PAPER_EDGE, tags="flip")

        if w > pad:
            if on_start_side:
                tx = (mid + pad) if d > 0 else (lx + pad)
            else:
                tx = (x0 + pad) if d > 0 else (mid + pad)
            face = back_lines if back else front_lines
            for i, line in enumerate(face):
                if not line:
                    continue
                self._draw_clipped(line, tx, top + i * self.LINE_H,
                                   x0 + S(2), x1 - S(2), self.ink)

        self.canvas.tag_raise("flip")
        self.canvas.tag_raise("ui")

    def _draw_clipped(self, text, x, y, x0, x1, color):
        """只画 [x0, x1] 区间里的那段文字——canvas 没有裁剪，只能自己截。"""
        f = self.body_font
        w_all = f.measure(text)
        if x >= x1 or x + w_all <= x0:
            return
        if x >= x0 and x + w_all <= x1:
            self.canvas.create_text(x, y, text=text, fill=color, font=f,
                                    anchor="nw", tags="flip")
            return
        start = 0
        if x < x0:
            lo, hi = 0, len(text)
            while lo < hi:
                m = (lo + hi) // 2
                if x + f.measure(text[:m]) < x0:
                    lo = m + 1
                else:
                    hi = m
            start = lo
        end = start
        while end < len(text) and x + f.measure(text[:end + 1]) <= x1:
            end += 1
        piece = text[start:end]
        if not piece:
            return
        self.canvas.create_text(x + f.measure(text[:start]), y, text=piece,
                                fill=color, font=f, anchor="nw", tags="flip")

    def _animate_cover(self, opening, after=None):
        """开书 / 合书：棕色书皮从中间向两侧分开（或合拢）。"""
        if self._anim_busy():
            if after:
                after()
            return
        S = self.S
        self._animating = True

        # 输入框是真正的子窗口，永远浮在画布图元上面 —— 书皮盖不住它，
        # 所以会出现"书还没打开、字已经全露出来"。开合期间改成画布画字。
        self._set_entries_visible(False)
        self._draw_booktext(self._left_idx(), self._right_idx())

        bx, by = self._book_origin(anim=False)
        bw, bh = S(BOOK_W), S(BOOK_H)
        mid = bx + bw // 2
        half = bw // 2 + S(2)
        left = self.canvas.create_rectangle(bx, by, mid, by + bh,
                                            fill=C_COVER_EDGE, outline="", tags="coveranim")
        right = self.canvas.create_rectangle(mid, by, bx + bw, by + bh,
                                             fill=C_COVER_EDGE, outline="", tags="coveranim")
        self.canvas.tag_raise("coveranim")
        # 实测本机 Tk 的 after 精度足够（5ms 就是 5.1ms），所以可以放心把帧数堆上去。
        # 26 帧 × 8ms ≈ 208ms，每帧位移从原来的 53px 降到 18px，肉眼看就是连续的了。
        steps = 26
        interval = 8

        def step(i=0):
            t = i / steps
            e = t * t * (3 - 2 * t)          # smoothstep：起手和落定都缓
            if opening:
                dx = int(half * e)           # 往两侧推开
            else:
                dx = int(half * (1 - e))     # 从两侧合拢
            self.canvas.coords(left, bx - dx, by, mid - dx, by + bh)
            self.canvas.coords(right, mid + dx, by, bx + bw + dx, by + bh)
            if i < steps:
                self.root.after(interval, lambda: step(i + 1))
            else:
                self.canvas.delete("coveranim")
                self.canvas.delete("booktext")
                self._set_entries_visible(True)
                self._animating = False
                self._focus(self.focus_side)
                if after:
                    after()

        step()

    def _draw_book_art(self):
        S = self.S
        c = self.canvas
        before = set(c.find_all())
        self._hotspots = []
        bx, by = self._book_origin()
        self._draw_book_frame(bx, by, S(BOOK_W), S(BOOK_H))

        total = len(self.current["pages"])
        lx = bx + S(COVER)
        rx = bx + S(COVER) + S(PAGE_W)
        py = by + S(COVER)

        # 中缝：由浅到深叠几层窄带做出渐变，中间压一道深色书脊线（照参考图）。
        # 必须画在左右两页之后，不然会被页面盖掉。
        if self.spread == 0:
            self._draw_cover_art(lx, py, S(PAGE_W), S(PAGE_H))   # 封面占左半边
        else:
            self._draw_page(lx, py, S(PAGE_W), S(PAGE_H), self._left_idx() + 1, total, "l")
        self._draw_page(rx, py, S(PAGE_W), S(PAGE_H), self._right_idx() + 1, total, "r")

        if self.spread == 0:
            # 左边是封面：中缝只做在右页的内侧（封面上不该有纸的渐变）
            for hw, col in ((S(30), "#f2e9d4"), (S(22), "#ebdfc4"),
                            (S(14), "#ddcba8"), (S(8), "#c9b48c")):
                c.create_rectangle(rx, py, rx + hw, py + S(PAGE_H), fill=col, outline="")
            c.create_rectangle(rx - S(3), py, rx + S(2), py + S(PAGE_H),
                               fill="#7d4d28", outline="")
        else:
            for hw, col in ((S(30), "#f2e9d4"), (S(22), "#ebdfc4"),
                            (S(14), "#ddcba8"), (S(8), "#c9b48c")):
                c.create_rectangle(rx - hw, py, rx + hw, py + S(PAGE_H), fill=col, outline="")
            c.create_rectangle(rx - S(2), py, rx + S(2), py + S(PAGE_H),
                               fill="#a9906b", outline="")

        # 左右下角的折角就是翻页：左角回翻、右角后翻（热区左右严格镜像）
        cs = S(24)
        m = S(4)
        self._hot(lx - m, py + S(PAGE_H) - cs - S(6), lx + cs + S(6), py + S(PAGE_H) + m,
                  "nav:prev")
        self._hot(rx + S(PAGE_W) - cs - S(6), py + S(PAGE_H) - cs - S(6),
                  rx + S(PAGE_W) + m, py + S(PAGE_H) + m, "nav:next")

        # 页面图标：新建页 / 删除页（上一页、下一页交给折角了）
        ic = S(20)
        gap = S(22)
        total_w = ic * 2 + gap
        ix = rx + S(PAGE_W) - S(58) - total_w
        iy = py + S(PAGE_H) - S(44)
        self._draw_icon_new(ix, iy, ic)
        self._hot(ix, iy, ix + ic, iy + ic, "nav:new")
        self._draw_icon_trash(ix + ic + gap, iy, ic)
        self._hot(ix + ic + gap, iy, ix + ic * 2 + gap, iy + ic, "nav:del")

        cx, cy = bx + S(BOOK_W) - S(26), by + S(22)
        c.create_line(cx - S(7), cy - S(7), cx + S(7), cy + S(7),
                      fill="#2b2216", width=max(1, S(2)))
        c.create_line(cx + S(7), cy - S(7), cx - S(7), cy + S(7),
                      fill="#2b2216", width=max(1, S(2)))
        self._hot(cx - S(16), cy - S(16), cx + S(16), cy + S(16), "close")

        for it in set(c.find_all()) - before:
            c.addtag_withtag("bookart", it)
        c.tag_raise("entry")
        c.tag_raise("ui")

    def _make_sign_button(self):
        """书页底部两个按钮：封面 / 署名，并排居中。"""
        S = self.S
        bx, by = self._book_origin()
        bw, bh = S(150), S(46)
        gap = S(20)
        total = bw * 2 + gap
        x0 = (self.win_w - total) // 2
        y = by + S(BOOK_H) + S(24)

        self._cover_btn = self._stone_button(self.t("cover"), self.goto_cover)
        self.canvas.create_window(x0, y, window=self._cover_btn, anchor="nw",
                                  width=bw, height=bh, tags="ui")

        self._sign_btn = self._stone_button(self._sign_label(), self.show_sign)
        self.canvas.create_window(x0 + bw + gap, y, window=self._sign_btn, anchor="nw",
                                  width=bw, height=bh, tags="ui")

    def _sign_label(self):
        return self.t("resign") if self.current.get("signed") else self.t("sign")

    def _update_sign_button(self):
        try:
            self._sign_btn.config(text=self._sign_label())
        except Exception:
            pass

    def _wrap(self, text):
        """按像素宽度折行——中文比拉丁宽，按字数折必然溢出。"""
        f = self.body_font
        limit = self.text_w
        if not text:
            return [""]
        out, cur = [], ""
        for ch in text:
            if not cur or f.measure(cur + ch) <= limit:
                cur += ch
            else:
                out.append(cur)
                cur = ch
        out.append(cur)
        return out

    def _wrap_all(self, raw):
        lines = []
        for ln in raw.split("\n"):
            lines.extend(self._wrap(ln))
        return lines

    def _set_page(self, idx, lines):
        while len(self.current["pages"]) <= idx:
            self.current["pages"].append([])
        self.current["pages"][idx] = lines[:MAX_LINES]

    def _push_overflow(self, idx, lines):
        """把装不下的行顺到后面的页；后面也满了就继续往后顺。返回最后落点的页号。"""
        while lines:
            while len(self.current["pages"]) <= idx:
                self.current["pages"].append([])
            merged = list(lines) + list(self.current["pages"][idx])
            if len(merged) <= MAX_LINES:
                self.current["pages"][idx] = merged
                return idx
            self.current["pages"][idx] = merged[:MAX_LINES]
            lines = merged[MAX_LINES:]
            idx += 1
        return max(0, idx - 1)

    def _cursor_to_end(self, side):
        i = 0 if side == "l" else 1
        if i < len(self._page_entries) and self._page_entries[i] is not None:
            try:
                self._page_entries[i].mark_set("insert", "end-1c")
                self._page_entries[i].see("insert")
            except Exception:
                pass

    def _reload_view(self, focus_side):
        """不重开界面，只把内容刷新到模型当前状态，并定好焦点。"""
        if not self._entries_match_spread():
            self._make_page_entries()
            self._focus(focus_side)
            return
        self._load_entry_texts()
        self._update_sign_button()
        self.canvas.delete("bookart")
        self._draw_book_art()
        self._place_entries()
        self._focus(focus_side)
        self._cursor_to_end(focus_side)

    def _goto_page(self, t):
        """把视图切到第 t 页（0 基），焦点落在它身上，光标到末尾。"""
        new_s = self._spread_of(t)
        if new_s != self.spread:
            self.spread = new_s
            self._reload_view("l" if t == self._left_idx() else "r")
        else:
            # 目标就在当前跨页里：不用换跨页，但两个输入框都得按模型刷新一遍
            side = "l" if t == self._left_idx() else "r"
            self._load_entry_texts()
            self._update_sign_button()
            self._focus(side)
            self._cursor_to_end(side)

    def _on_type(self, side):
        i = 0 if side == "l" else 1
        idx = self._side_idx(i)
        if i >= len(self._page_entries):
            return
        e = self._page_entries[i]
        if e is None or idx < 0:          # 封面那半边不是可写的页
            return
        lines = self._wrap_all(e.get("1.0", "end-1c"))
        if len(lines) > MAX_LINES:
            # 一页写满：多出来的行顺到下一页去（不截断、也不让输入框内部往下滚）
            keep, overflow = lines[:MAX_LINES], lines[MAX_LINES:]
            e.delete("1.0", "end")
            e.insert("1.0", "\n".join(keep))
            e.see("end-1c")
            self._set_page(idx, keep)
            target = self._push_overflow(idx + 1, overflow)
            self._goto_page(target)
        else:
            self._set_page(idx, lines)
        self.current["updated"] = time.time()

    def _commit(self):
        if self.current is None:
            return
        for i in range(min(2, len(self._page_entries))):
            idx = self._side_idx(i)
            if idx < 0 or self._page_entries[i] is None:
                continue
            lines = self._wrap_all(self._page_entries[i].get("1.0", "end-1c"))
            while len(self.current["pages"]) <= idx:
                self.current["pages"].append([])
            self.current["pages"][idx] = lines[:MAX_LINES]

    # ---- 翻页 / 增删（一次翻一页，和真书一样）
    def turn(self, d):
        if self._anim_busy():
            return
        self._commit()
        target = self.spread + d
        if target < 0:                     # 0 是「封面|第1页」，再往前没有了
            return
        while len(self.current["pages"]) <= 2 * target:
            self.current["pages"].append([])       # 页数无上限
        self.spread = target
        self._update_sign_button()
        self._animate_flip(d)

    def add_pages(self):
        if self._anim_busy():
            return
        self._commit()
        self.current["pages"].append([])
        self.spread = self._spread_of(len(self.current["pages"]) - 1)   # 跳到新页那一跨
        self._update_sign_button()
        self._animate_flip(+1)

    def del_pages(self):
        if self._anim_busy():
            return
        self._commit()
        if len(self.current["pages"]) <= 2:
            messagebox.showinfo(self.t("cant_del"), self.t("at_least_one"))
            return
        if not messagebox.askyesno(self.t("del_pages_title"), self.t("del_pages_msg")):
            return
        i = 0 if self.focus_side == "l" else 1
        idx = self._side_idx(i)
        if idx < 0:                        # 焦点在封面上，没页可删
            messagebox.showinfo(self.t("cant_del"), self.t("at_least_one"))
            return
        del self.current["pages"][idx]
        self.spread = max(0, min(self.spread,
                                 self._spread_of(len(self.current["pages"]) - 1)))
        self._update_sign_button()
        self._animate_flip(-1)

    def goto_cover(self):
        """跳到第一跨页：封面 | 第1页。"""
        if self._anim_busy():
            return
        self._commit()
        if self.spread == 0:
            return
        self.spread = 0
        self.show_book()

    # ============================================================ 署名界面
    def show_sign(self):
        self._commit()
        self._new_screen("sign")
        self._resize(WIN_W, WIN_H)
        self._draw_world()

        S = self.S
        c = self.canvas
        cw, ch = S(322), S(440)
        cx = (self.win_w - cw) // 2
        cy = (self.win_h - ch) // 2 - S(20)
        self._draw_panel(cx, cy, cw, ch)

        c.create_text(cx + cw / 2, cy + S(76), text=self.t("sign_title_label"),
                      fill="#efe6d4", font=self._font(11))

        e_title = tk.Entry(self.canvas, font=self._font(10), bg=C_COVER, fg="#efe6d4",
                           insertbackground="#efe6d4", relief="flat", justify="center",
                           highlightthickness=0)
        e_title.insert(0, self.current.get("title") or "")
        self._float_widgets.append(e_title)
        c.create_window(cx + S(34), cy + S(100), window=e_title, anchor="nw",
                        width=cw - S(68), height=S(30))
        self._sign_title = e_title

        # 标签宽度按文字实测，中英文都不会和输入框打架
        lbl = self.t("author_label")
        lw = self._font(10).measure(lbl)
        c.create_text(cx + S(48), cy + S(160), anchor="w", text=lbl,
                      fill="#efe6d4", font=self._font(10))
        ax = cx + S(48) + lw + S(16)
        e_author = tk.Entry(self.canvas, font=self._font(10), bg=C_COVER, fg="#e6d9c2",
                            insertbackground="#efe6d4", relief="flat", justify="left",
                            highlightthickness=0)
        e_author.insert(0, self.current.get("author") or self.t("unknown_author"))
        self._float_widgets.append(e_author)
        c.create_window(ax, cy + S(148), window=e_author, anchor="nw",
                        width=max(S(90), cx + cw - S(34) - ax), height=S(26))
        self._sign_author = e_author

        warn = self.t("sign_warn")
        half = max(8, len(warn) // 2)
        c.create_text(cx + S(48), cy + S(214), anchor="nw", text=warn[:half],
                      fill="#efe6d4", font=self._font(10))
        c.create_text(cx + S(48), cy + S(242), anchor="nw", text=warn[half:],
                      fill="#efe6d4", font=self._font(10))

        bw, bh = S(206), S(44)
        gap = S(20)
        y = cy + ch + S(24)
        left = cx + (cw - bw * 2 - gap) // 2
        b1 = self._stone_button(self.t("sign_and_close"), self.do_sign)
        c.create_window(left, y, window=b1, anchor="nw", width=bw, height=bh)
        b2 = self._stone_button(self.t("cancel"), self.show_book)
        c.create_window(left + bw + gap, y, window=b2, anchor="nw", width=bw, height=bh)
        e_title.focus_set()

    def do_sign(self):
        self.current["title"] = self._sign_title.get().strip() or self.t("untitled")
        self.current["author"] = self._sign_author.get().strip() or self.t("unknown_author")
        self.current["signed"] = True
        self.current["updated"] = time.time()
        self.save_now()
        self.show_shelf()

    # ============================================================ 重命名
    def show_rename(self, bid):
        b = self.lib.get(bid)
        if not b:
            return
        self._rename_bid = bid
        self._new_screen("rename")
        self._resize(WIN_W, WIN_H)
        self._draw_world()
        S = self.S
        c = self.canvas
        cw, ch = S(360), S(210)
        cx = (self.win_w - cw) // 2
        cy = (self.win_h - ch) // 2
        self._draw_panel(cx, cy, cw, ch)
        c.create_text(cx + cw / 2, cy + S(42), text=self.t("rename_title"),
                      fill="#efe6d4", font=self._font(11))
        e = tk.Entry(self.canvas, font=self._font(10), bg=C_COVER, fg="#efe6d4",
                     insertbackground="#efe6d4", relief="flat", justify="center",
                     highlightthickness=0)
        e.insert(0, b.get("title") or "")
        self._float_widgets.append(e)
        c.create_window(cx + S(34), cy + S(66), window=e, anchor="nw",
                        width=cw - S(68), height=S(30))

        def ok(_=None):
            b["title"] = e.get().strip() or self.t("untitled")
            self.lib.save()
            self.show_shelf()

        bw, bh = S(126), S(40)
        y = cy + ch - S(58)
        bb = self._stone_button(self.t("ok"), ok)
        self.canvas.create_window(cx + S(38), y, window=bb, anchor="nw", width=bw, height=bh)
        bc = self._stone_button(self.t("cancel"), self.show_shelf)
        self.canvas.create_window(cx + cw - S(38) - bw, y, window=bc, anchor="nw",
                                  width=bw, height=bh)
        e.bind("<Return>", ok)
        e.focus_set()

    # ============================================================ 设置
    def show_settings(self):
        self._new_screen("settings")
        self._resize(WIN_W, WIN_H)
        self._draw_world()
        S = self.S
        c = self.canvas
        cw, ch = S(470), S(530)
        cx = (self.win_w - cw) // 2
        cy = (self.win_h - ch) // 2
        self._draw_panel(cx, cy, cw, ch)
        lx = cx + S(44)                      # 左侧文字列
        rx = cx + cw - S(44)                 # 右侧控件右边界

        c.create_text(cx + cw / 2, cy + S(34), text=self.t("settings"),
                      fill="#efe6d4", font=self._font(12))

        # —— 语言 ——
        c.create_text(cx + cw / 2, cy + S(76), text=self.t("language"),
                      fill="#efe6d4", font=self._font(10))
        bw, bh, gap = S(130), S(34), S(14)
        total = bw * 2 + gap
        bx0 = cx + (cw - total) // 2
        for i, (code, label) in enumerate((("zh", "中文"), ("en", "English"))):
            act = (code == self.lang)
            b = tk.Button(self.canvas, text=label,
                          command=lambda cd=code: self.set_lang(cd),
                          bg=("#c6c6c6" if act else C_BTN),
                          fg=("#1a1a1a" if act else "#ffffff"),
                          activebackground=C_BTN_HI, font=self._font(10),
                          relief="solid", bd=S(1), highlightthickness=S(2),
                          highlightbackground=C_BTN_LO, padx=S(6), pady=S(1),
                          cursor="hand2")
            self._float_widgets.append(b)
            c.create_window(bx0 + i * (bw + gap), cy + S(94), window=b, anchor="nw",
                            width=bw, height=bh)

        # —— 页内横线（方框打勾）——
        c.create_text(lx, cy + S(162), anchor="w", text=self.t("rules_label"),
                      fill="#efe6d4", font=self._font(10))
        bs = S(30)
        bx = rx - bs
        by = cy + S(147)
        c.create_rectangle(bx, by, bx + bs, by + bs, fill="#f4ecd8",
                           outline="#3a2612", width=max(1, S(2)))
        if self.show_rules:
            c.create_line(bx + S(5), by + S(16), bx + S(12), by + S(24),
                          bx + bs - S(5), by + S(6),
                          fill="#2b2216", width=max(2, S(3)), capstyle="round")
        self._hot(lx - S(6), by - S(10), bx + bs + S(10), by + bs + S(10), "toggle:rules")

        # —— 行距（滑块 + 数值）——
        c.create_text(lx, cy + S(210), anchor="w", text=self.t("gap_label"),
                      fill="#efe6d4", font=self._font(10))
        # 数值放标签右侧（放右边会被滑块控件盖住）
        self._gap_val_id = c.create_text(lx + S(62), cy + S(210), anchor="w",
                                         text=str(self.line_gap),
                                         fill="#d8c8a8", font=self._font(10))
        sc = tk.Scale(self.canvas, from_=0, to=max(1, self.max_line_gap()),
                      orient="horizontal", showvalue=0, length=S(260), width=S(14),
                      bg=C_COVER, fg="#efe6d4", troughcolor="#5e3719",
                      activebackground="#c6c6c6", highlightthickness=0, bd=0,
                      sliderrelief="raised", font=self._font(8),
                      command=self.set_line_gap)
        sc.set(self.line_gap)
        self._float_widgets.append(sc)
        c.create_window(lx + S(96), cy + S(192), window=sc, anchor="nw",
                        width=rx - (lx + S(96)), height=S(36))

        # —— 字体大小（像素字体只能整数倍，所以给 1×/2×/3×）——
        c.create_text(lx, cy + S(264), anchor="w", text=self.t("size_label"),
                      fill="#efe6d4", font=self._font(10))
        sbw, sbh, sgap = S(64), S(32), S(10)
        sx0 = rx - sbw * 3 - sgap * 2
        for i, k in enumerate((1, 2, 3)):
            act = (k == self.font_scale)
            b = tk.Button(self.canvas, text="%d×" % k,
                          command=lambda kk=k: self.set_font_scale(kk),
                          bg=("#c6c6c6" if act else C_BTN),
                          fg=("#1a1a1a" if act else "#ffffff"),
                          activebackground=C_BTN_HI, font=self._font(9),
                          relief="solid", bd=S(1), highlightthickness=S(2),
                          highlightbackground=C_BTN_LO, padx=S(2), pady=S(1),
                          cursor="hand2")
            self._float_widgets.append(b)
            c.create_window(sx0 + i * (sbw + sgap), cy + S(248), window=b, anchor="nw",
                            width=sbw, height=sbh)

        # —— 字体颜色（色块）——
        c.create_text(lx, cy + S(318), anchor="w", text=self.t("color_label"),
                      fill="#efe6d4", font=self._font(10))
        sw, sgap2 = S(30), S(12)
        wx0 = rx - sw * len(INK_COLORS) - sgap2 * (len(INK_COLORS) - 1)
        for i, col in enumerate(INK_COLORS):
            wx = wx0 + i * (sw + sgap2)
            wy = cy + S(303)
            c.create_rectangle(wx, wy, wx + sw, wy + sw, fill=col,
                               outline=("#f4ecd8" if col == self.ink else "#3a2612"),
                               width=max(2, S(3)) if col == self.ink else max(1, S(1)))
            self._hot(wx - S(4), wy - S(4), wx + sw + S(4), wy + sw + S(4), "ink:" + col)

        # —— 预览：行距 / 字号 / 墨色都是一眼可见的 ——
        pw = cw - S(88)
        ph = S(120)
        self._preview_box = (cx + S(44), cy + S(352), pw, ph)
        self._draw_gap_preview(*self._preview_box)

        cb = self._stone_button(self.t("close"), self.show_shelf)
        c.create_window(cx + (cw - S(160)) // 2, cy + ch - S(58), window=cb, anchor="nw",
                        width=S(160), height=S(42))

    def set_font_scale(self, k):
        k = max(1, min(3, int(k)))
        if k == self.font_scale:
            return
        self.settings["font_scale"] = k
        self.font_scale = k
        save_settings(self.settings)
        self._measure_font()          # 行高会变，行距上限也跟着变
        self.show_settings()

    def set_ink(self, color):
        if color not in INK_COLORS or color == self.ink:
            return
        self.ink = color
        self.settings["ink_color"] = color
        save_settings(self.settings)
        self.show_settings()

    # ============================================================ 事件
    def _hot(self, x0, y0, x1, y1, tag):
        """登记一个点击热区。比靠 canvas 图元标签命中更可靠。"""
        self._hotspots.append((x0, y0, x1, y1, tag))

    def _on_click(self, ev):
        x, y = ev.x, ev.y
        for (x0, y0, x1, y1, tag) in reversed(self._hotspots):
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._fire(tag)
                return
        # 兜底：某些图元自带标签
        tags = set()
        for it in self.canvas.find_overlapping(x, y, x, y):
            tags |= set(self.canvas.gettags(it))
        for t in tags:
            if (t.startswith(("nav:", "row:", "edit:", "del:"))
                    or t in ("close", "settings", "sign:cancel")):
                self._fire(t)
                return

    def _fire(self, t):
        if t.startswith("nav:"):
            k = t.split(":", 1)[1]
            if k == "prev":
                self.turn(-1)
            elif k == "next":
                self.turn(1)
            elif k == "new":
                self.add_pages()
            elif k == "del":
                self.del_pages()
            return
        if t == "close":
            self._animate_cover(opening=False, after=self.show_shelf)
            return
        if t == "settings":
            self.show_settings()
            return
        if t.startswith("ink:"):
            self.set_ink(t.split(":", 1)[1])
            return
        if t == "toggle:rules":
            self.show_rules = not self.show_rules
            self.settings["show_rules"] = self.show_rules
            save_settings(self.settings)
            self.show_settings()
            return
        if t == "sign:cancel":
            self.show_shelf() if self.screen == "settings" else self.show_book()
            return
        if t.startswith("row:"):
            self.open_book(t.split(":", 1)[1])
            return
        if t.startswith("edit:"):
            self.show_rename(t.split(":", 1)[1])
            return
        if t.startswith("del:"):
            bid = t.split(":", 1)[1]
            b = self.lib.get(bid)
            if b and messagebox.askyesno(
                    self.t("del_book_title"),
                    self.t("del_book_msg", t=(b.get("title") or self.t("untitled")))):
                self.lib.remove(bid)
                self.lib.save()
                self.show_shelf()
            return

    # ============================================================ 存取
    def save_now(self):
        self._commit()
        try:
            self.lib.save()
        except Exception:
            pass

    def on_close(self):
        self.save_now()
        save_settings(self.settings)
        self.root.destroy()

    def export_txt(self):
        if not self.current:
            return
        self._commit()
        name = (self.current.get("title") or self.t("untitled")).strip() or self.t("untitled")
        out = os.path.join(DATA_DIR, name + ".txt")
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(f"{name}\n")
                if self.current.get("author"):
                    f.write(f"{self.current['author']}\n")
                f.write("=" * 30 + "\n\n")
                for i, lines in enumerate(self.current["pages"], 1):
                    f.write(f"--- {i} ---\n")
                    f.write("\n".join(lines) + "\n\n")
            messagebox.showinfo(self.t("export_ok"), self.t("export_ok_msg", p=out))
        except Exception as e:
            messagebox.showerror(self.t("export_fail"), str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
