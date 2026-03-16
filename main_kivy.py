# -*- coding: utf-8 -*-
"""
main_kivy.py
功能：V2Ray 节点提取 & 一键发布（Kivy 版）
说明：使用 Kivy 实现跨平台 UI，兼容 Android。
"""

import json
import base64
import re
import urllib.parse
import threading
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.clock import Clock

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Label:
            text: "目标网页 URL:"
            size_hint_x: None
            width: dp(100)
        TextInput:
            id: url_input
            text: root.default_url
            multiline: False

    BoxLayout:
        size_hint_y: None
        height: dp(45)
        spacing: dp(5)
        Button:
            text: "1. 开始抓取"
            background_color: 0/255, 0/255, 128/255, 1
            on_release: root.start_scraping()
        Button:
            text: "2. 复制所有节点"
            background_color: 0/255, 128/255, 0/255, 1
            on_release: root.copy_to_clipboard()
        Button:
            text: "3. 生成订阅链接"
            background_color: 255/255, 87/255, 34/255, 1
            on_release: root.publish_subscription()

    Label:
        text: "提取结果 (直接显示在这里)"
        size_hint_y: None
        height: dp(30)

    ScrollView:
        size_hint_y: 0.45
        TextInput:
            id: result_text
            text: root.result_str
            readonly: True
            background_color: 0.95, 0.95, 0.95, 1
            foreground_color: 0, 0, 0, 1
            font_size: '14sp'
            size_hint_y: None
            height: self.minimum_height
            multiline: True

    Label:
        text: "运行日志"
        size_hint_y: None
        height: dp(30)

    ScrollView:
        size_hint_y: 0.35
        TextInput:
            id: log_text
            text: root.log_str
            readonly: True
            background_color: 0.0, 0.0, 0.0, 1
            foreground_color: 0.0, 1.0, 0.0, 1
            font_size: '13sp'
            size_hint_y: None
            height: self.minimum_height
            multiline: True
'''

class V2ScraperApp(App):
    default_url = StringProperty(
        "https://v2raya.net/free-nodes/free-v2ray-node-subscriptions.html")
    result_str = StringProperty("")
    log_str = StringProperty("")
    final_node_list = ListProperty([])

    def _log(self, msg):
        def _append(dt):
            self.log_str = self.log_str + msg + "\n"
        Clock.schedule_once(_append)

    def safe_base64_decode(self, s):
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

    def get_node_name(self, link):
        try:
            if link.startswith("vmess://"):
                data = self.safe_base64_decode(link.replace("vmess://", ""))
                if data:
                    return json.loads(data).get("ps", "")
            elif "://" in link:
                return urllib.parse.unquote(
                    urllib.parse.urlparse(link).fragment)
        except Exception:
            pass
        return ""

    def is_target_country(self, name):
        if not name:
            return False
        name_l = name.lower()
        patterns = [
            r"美国|united states|\bus\b|\(us\)|\[us\]|🇺🇸",
            r"英国|united kingdom|\buk\b|\(uk\)|\[uk\]|🇬🇧",
            r"法国|france|\bfr\b|\(fr\)|\[fr\]|🇫🇷",
            r"德国|germany|\bde\b|\(de\)|\[de\]|🇩🇪",
        ]
        return any(re.search(p, name_l) for p in patterns)

    def _parse_nodes(self, text):
        decoded = self.safe_base64_decode(text.strip()) or text
        count = 0
        for line in decoded.splitlines():
            line = line.strip()
            if not line:
                continue
            name = self.get_node_name(line)
            if self.is_target_country(name):
                self.final_node_list.append(line)
                count += 1
        return count

    def start_scraping(self):
        self.result_str = ""
        self.log_str = ""
        self.final_node_list = []
        threading.Thread(target=self._scrape_thread, daemon=True).start()

    def _scrape_thread(self):
        url = self.root.ids.url_input.text.strip()
        self._log(f"🚀 开始抓取: {url}")

        headers = {
            "User-Agent":
            "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            self._log(f"❌ 网络错误: {e}")
            return

        subs = list(set(re.findall(r"https://fn[^\s\"'<]+", html)))
        backup_subs = re.findall(
            r"https?://[^\s\"'<>]+(?:sub|subscribe|node|json)[^\s\"'<>]*",
            html)
        subs = list(set(subs + backup_subs))

        if not subs:
            self._log("❌ 未发现订阅链接")
            return
        self._log(f"✅ 发现 {len(subs)} 个潜在订阅源")

        processed = set()
        for i, sub in enumerate(subs):
            if sub in processed:
                continue
            processed.add(sub)
            self._log(f"[{i+1}/{len(subs)}] 解析: {sub[:50]}...")

            try:
                if "json" in sub.lower():
                    r_json = requests.get(sub, timeout=15, headers=headers)
                    try:
                        data = r_json.json()
                        if "subscriptions" in data:
                            self._log(
                                f"   → JSON 索引，包含 {len(data['subscriptions'])} 条链接")
                            for item in data["subscriptions"]:
                                u = item.get("url")
                                if u and u not in processed:
                                    processed.add(u)
                                    r_sub = requests.get(u,
                                                         timeout=12,
                                                         headers=headers)
                                    c = self._parse_nodes(r_sub.text)
                                    if c:
                                        self._log(
                                            f"     + 子链接命中 {c} 个节点")
                            continue
                    except Exception:
                        pass

                r = requests.get(sub, timeout=12, headers=headers)
                c = self._parse_nodes(r.text)
                if c:
                    self._log(f"   → 命中 {c} 个节点")
            except Exception as e:
                self._log(f"   → 错误: {e}")

        self.final_node_list = list(set(self.final_node_list))
        self._log(f"🎉 完成，共筛选 {len(self.final_node_list)} 个节点")
        if self.final_node_list:
            self.result_str = "\n".join(self.final_node_list)

    def copy_to_clipboard(self):
        data = self.result_str.strip()
        if not data:
            self._log("⚠️ 结果为空，未复制")
            return
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(data)
        self._log("✅ 已复制到剪贴板")

    def publish_subscription(self):
        if not self.result_str.strip():
            self._log("⚠️ 结果为空，无法发布")
            return
        threading.Thread(target=self._publish_thread, daemon=True).start()

    def _publish_thread(self):
        nodes = self.result_str.strip()
        b64 = base64.b64encode(nodes.encode()).decode()
        self._log("🌐 上传至 Dpaste...")
        try:
            r = requests.post("https://dpaste.com/api/", data={
                "content": b64,
                "expiry_days": 7
            })
            if r.status_code in (200, 201):
                url = r.text.strip() + ".txt"
                self._log(f"✅ 生成链接: {url}")
                from kivy.uix.popup import Popup
                from kivy.uix.label import Label
                from kivy.uix.boxlayout import BoxLayout
                from kivy.uix.button import Button

                layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
                layout.add_widget(
                    Label(text=f"[ref=link]{url}[/ref]",
                          markup=True,
                          color=(0, 0.6, 1, 1)))
                btn = Button(text="复制链接并关闭", size_hint_y=None, height=40)
                layout.add_widget(btn)

                popup = Popup(title="订阅链接", content=layout,
                              size_hint=(0.9, 0.3))

                def copy_and_close(*_):
                    from kivy.core.clipboard import Clipboard
                    Clipboard.copy(url)
                    self._log("✅ 链接已复制")
                    popup.dismiss()

                btn.bind(on_release=copy_and_close)
                popup.open()
            else:
                self._log(f"❌ 发布失败，状态码 {r.status_code}")
        except Exception as e:
            self._log(f"❌ 发布异常: {e}")

    def build(self):
        return Builder.load_string(KV)


if __name__ == '__main__':
    V2ScraperApp().run()
