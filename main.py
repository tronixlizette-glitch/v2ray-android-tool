# -*- coding: utf-8 -*-
"""
V2Ray 节点提取 & 一键发布工具 - Android版
使用 Kivy 框架，适配手机分辨率
"""

import re
import base64
import json
import urllib.parse
import threading
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard


# ── 颜色主题 ──────────────────────────────────────────
BG_DARK       = get_color_from_hex("#0D1117")
BG_CARD       = get_color_from_hex("#161B22")
BG_INPUT      = get_color_from_hex("#21262D")
ACCENT_BLUE   = get_color_from_hex("#1F6FEB")
ACCENT_GREEN  = get_color_from_hex("#238636")
ACCENT_ORANGE = get_color_from_hex("#E85314")
TEXT_PRIMARY  = get_color_from_hex("#E6EDF3")
TEXT_MUTED    = get_color_from_hex("#8B949E")
BORDER_COLOR  = get_color_from_hex("#30363D")


# ── 工具函数 ─────────────────────────────────────────
def safe_base64_decode(s):
    if not s:
        return ""
    s = s.strip()
    missing = 4 - len(s) % 4
    if missing != 4:
        s += "=" * missing
    try:
        return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def get_node_name(link):
    try:
        if link.startswith("vmess://"):
            data = safe_base64_decode(link.replace("vmess://", ""))
            if data:
                return json.loads(data).get("ps", "")
        elif "://" in link:
            return urllib.parse.unquote(urllib.parse.urlparse(link).fragment)
    except Exception:
        pass
    return ""


def is_target_country(name):
    if not name:
        return False
    name_l = name.lower()
    # 更加智能的词界匹配，防止 "rus" 匹配 "us"
    import re
    # 美国/US, 英国/UK, 法国/FR, 德国/DE
    patterns = [
        r"美国|united states|\bus\b|\(us\)|\[us\]|🇺🇸",
        r"英国|united kingdom|\buk\b|\(uk\)|\[uk\]|🇬🇧",
        r"法国|france|\bfr\b|\(fr\)|\[fr\]|🇫🇷",
        r"德国|germany|\bde\b|\(de\)|\[de\]|🇩🇪"
    ]
    return any(re.search(p, name_l) for p in patterns)


# ── 自定义控件 ────────────────────────────────────────
class RoundedButton(Button):
    """带圆角背景色的按钮"""
    def __init__(self, bg_color=ACCENT_BLUE, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = bg_color
        self.color = TEXT_PRIMARY
        self.font_size = sp(14)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(48)


# ── 主界面 ────────────────────────────────────────────
class V2RayLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.padding = [dp(12), dp(12), dp(12), dp(12)]
        self.spacing = dp(10)

        self.final_node_list = []

        # 背景色
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(*BG_DARK)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self._build_header()
        self._build_url_input()
        self._build_buttons()
        self._build_result_area()
        self._build_log_area()

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _section_label(self, text):
        return Label(
            text=text,
            color=TEXT_MUTED,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(20),
            halign="left",
            text_size=(Window.width - dp(24), None),
        )

    def _build_header(self):
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
        )
        title = Label(
            text="🚀 V2Ray 节点提取工具",
            font_size=sp(18),
            bold=True,
            color=TEXT_PRIMARY,
            halign="left",
        )
        title.bind(size=title.setter("text_size"))
        header.add_widget(title)
        self.add_widget(header)

    def _build_url_input(self):
        self.add_widget(self._section_label("目标网页 URL"))
        self.url_input = TextInput(
            text="https://v2raya.net/free-nodes/free-v2ray-node-subscriptions.html",
            multiline=False,
            background_color=BG_INPUT,
            foreground_color=TEXT_PRIMARY,
            cursor_color=TEXT_PRIMARY,
            font_size=sp(12),
            padding=[dp(10), dp(10)],
            size_hint_y=None,
            height=dp(48),
        )
        self.add_widget(self.url_input)

    def _build_buttons(self):
        grid = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
        )
        grid.bind(minimum_height=grid.setter("height"))

        self.btn_scrape = RoundedButton(
            text="① 开始抓取节点",
            bg_color=ACCENT_BLUE,
        )
        self.btn_scrape.bind(on_press=self.start_scraping)

        self.btn_copy = RoundedButton(
            text="② 复制所有节点",
            bg_color=ACCENT_GREEN,
        )
        self.btn_copy.bind(on_press=self.copy_to_clipboard)

        self.btn_publish = RoundedButton(
            text="③ 生成订阅链接（分享）",
            bg_color=ACCENT_ORANGE,
        )
        self.btn_publish.bind(on_press=self.publish_subscription)

        grid.add_widget(self.btn_scrape)
        grid.add_widget(self.btn_copy)
        grid.add_widget(self.btn_publish)
        self.add_widget(grid)

    def _build_result_area(self):
        self.add_widget(self._section_label("📋 提取结果"))
        scroll = ScrollView(size_hint=(1, 0.35))
        self.result_text = TextInput(
            hint_text="节点将显示在这里...",
            multiline=True,
            background_color=BG_INPUT,
            foreground_color=TEXT_PRIMARY,
            hint_text_color=TEXT_MUTED,
            font_size=sp(11),
            padding=[dp(10), dp(10)],
            size_hint=(1, None),
        )
        self.result_text.bind(minimum_height=self.result_text.setter("height"))
        scroll.add_widget(self.result_text)
        self.add_widget(scroll)

    def _build_log_area(self):
        self.add_widget(self._section_label("📝 运行日志"))
        scroll = ScrollView(size_hint=(1, 1))
        self.log_text = TextInput(
            hint_text="日志将显示在这里...",
            multiline=True,
            readonly=True,
            background_color=BG_CARD,
            foreground_color=TEXT_MUTED,
            hint_text_color=BORDER_COLOR,
            font_size=sp(11),
            padding=[dp(10), dp(10)],
            size_hint=(1, None),
        )
        self.log_text.bind(minimum_height=self.log_text.setter("height"))
        scroll.add_widget(self.log_text)
        self.add_widget(scroll)

    # ── 工具方法 ─────────────────────────────────────
    def _log(self, msg):
        def _do(dt):
            self.log_text.text += msg + "\n"
        Clock.schedule_once(_do, 0)

    def _set_btn_state(self, enabled):
        def _do(dt):
            self.btn_scrape.disabled = not enabled
            self.btn_publish.disabled = not enabled
        Clock.schedule_once(_do, 0)

    # ── 抓取逻辑 ─────────────────────────────────────
    def start_scraping(self, *args):
        Clock.schedule_once(lambda dt: self._clear_ui(), 0)
        threading.Thread(target=self._do_scrape, daemon=True).start()

    def _clear_ui(self):
        self.log_text.text = ""
        self.result_text.text = ""
        self.final_node_list = []

    def _do_scrape(self):
        self._set_btn_state(False)
        url = self.url_input.text.strip()
        self._log(f"🚀 开始访问: {url}")

        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Mobile Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            self._log(f"❌ 网络错误: {e}")
            self._set_btn_state(True)
            return

        # 提取订阅链接 (支持常规正则和 JSON 发现)
        subs = list(set(re.findall(r"https://fn[^\s\"'<]+", html)))
        
        # 备用：抓取所有可能包含订阅的链接 (包含 JSON 数据源)
        backup_subs = re.findall(r"https?://[^\s\"'<>]+(?:sub|subscribe|node|json)[^\s\"'<>]*", html)
        subs = list(set(subs + backup_subs))

        if not subs:
            self._log("❌ 未发现有效订阅链接，请检查 URL")
            self._set_btn_state(True)
            return

        self._log(f"✅ 发现 {len(subs)} 个潜在订阅源")

        final_subs = []
        processed_urls = set()
        
        # 遍历订阅源
        for i, sub in enumerate(subs):
            if sub in processed_urls: continue
            processed_urls.add(sub)
            
            self._log(f"[{i+1}/{len(subs)}] 解析: {sub[:50]}...")
            try:
                # 针对 JSON 格式索引的特殊处理
                if sub.endswith(".json") or "json" in sub:
                     r = requests.get(sub, timeout=15, headers=headers)
                     try:
                         data = r.json()
                         if isinstance(data, dict) and "subscriptions" in data:
                             self._log(f"   → 发现 JSON 索引，包含 {len(data['subscriptions'])} 个链接")
                             for item in data["subscriptions"]:
                                 u = item.get("url")
                                 if u and u not in processed_urls:
                                     self._log(f"     + 发现链接: {u[:40]}...")
                                     # 立即解析新发现的链接
                                     r_sub = requests.get(u, timeout=15, headers=headers)
                                     self._parse_nodes(r_sub.text)
                             continue
                     except:
                         pass

                # 常规解析
                r = requests.get(sub, timeout=15, headers=headers)
                self._parse_nodes(r.text)
            except Exception as e:
                self._log(f"   → 错误: {e}")

        self.final_node_list = list(set(self.final_node_list))
        self._log(f"🎉 完成！共筛选 {len(self.final_node_list)} 个节点")

        if self.final_node_list:
            result = "\n".join(self.final_node_list)
            Clock.schedule_once(lambda dt: setattr(self.result_text, "text", result), 0)

        self._set_btn_state(True)

    def _parse_nodes(self, text):
        """解析并提取目标国家节点"""
        decoded_text = safe_base64_decode(text.strip()) or text
        count = 0
        for line in decoded_text.splitlines():
            line = line.strip()
            if not line:
                continue
            name = get_node_name(line)
            if is_target_country(name):
                self.final_node_list.append(line)
                count += 1
        if count > 0:
            self._log(f"   → 命中 {count} 个节点")

    # ── 复制逻辑 ─────────────────────────────────────
    def copy_to_clipboard(self, *args):
        data = self.result_text.text.strip()
        if data:
            Clipboard.copy(data)
            self._show_popup("✅ 成功", "已复制到剪贴板")
        else:
            self._show_popup("⚠️ 提示", "结果为空，请先抓取节点")

    # ── 发布逻辑 ─────────────────────────────────────
    def publish_subscription(self, *args):
        nodes = self.result_text.text.strip()
        if not nodes:
            self._show_popup("⚠️ 错误", "结果为空，请先抓取节点")
            return
        threading.Thread(target=self._do_publish, args=(nodes,), daemon=True).start()

    def _do_publish(self, nodes):
        self._log("🌐 正在上传至 Dpaste...")
        b64 = base64.b64encode(nodes.encode()).decode()
        try:
            r = requests.post(
                "https://dpaste.com/api/",
                data={"content": b64, "expiry_days": 7},
                timeout=20,
            )
            if r.status_code in (200, 201):
                url = r.text.strip() + ".txt"
                self._log(f"✅ 订阅链接: {url}")
                Clock.schedule_once(lambda dt: self._show_url_popup(url), 0)
            else:
                self._log(f"❌ 上传失败: HTTP {r.status_code}")
        except Exception as e:
            self._log(f"❌ 发布失败: {e}")

    # ── 弹窗 ─────────────────────────────────────────
    def _show_popup(self, title, message):
        def _do(dt):
            content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
            content.add_widget(Label(
                text=message,
                color=TEXT_PRIMARY,
                font_size=sp(14),
                text_size=(dp(250), None),
                halign="center",
            ))
            btn = RoundedButton(text="确定", bg_color=ACCENT_BLUE)
            content.add_widget(btn)
            popup = Popup(
                title=title,
                content=content,
                size_hint=(0.85, None),
                height=dp(200),
                background_color=BG_CARD,
                title_color=TEXT_PRIMARY,
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        Clock.schedule_once(_do, 0)

    def _show_url_popup(self, url):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="订阅链接生成成功！",
            color=TEXT_PRIMARY,
            font_size=sp(14),
            size_hint_y=None,
            height=dp(30),
        ))
        url_input = TextInput(
            text=url,
            readonly=True,
            font_size=sp(11),
            background_color=BG_INPUT,
            foreground_color=TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(60),
        )
        content.add_widget(url_input)

        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))

        popup = Popup(
            title="✅ 订阅链接",
            content=content,
            size_hint=(0.92, None),
            height=dp(280),
            background_color=BG_CARD,
            title_color=TEXT_PRIMARY,
        )

        def do_copy(instance):
            Clipboard.copy(url)
            popup.dismiss()
            self._show_popup("✅ 成功", "链接已复制到剪贴板")

        btn_copy = RoundedButton(text="复制链接", bg_color=ACCENT_GREEN)
        btn_copy.bind(on_press=do_copy)
        btn_close = RoundedButton(text="关闭", bg_color=BG_INPUT)
        btn_close.bind(on_press=popup.dismiss)

        btns.add_widget(btn_copy)
        btns.add_widget(btn_close)
        content.add_widget(btns)
        popup.open()


# ── 应用入口 ──────────────────────────────────────────
class V2RayApp(App):
    def build(self):
        self.title = "V2Ray 节点提取工具"
        # 设置窗口背景
        Window.clearcolor = BG_DARK
        return V2RayLayout()


if __name__ == "__main__":
    V2RayApp().run()
