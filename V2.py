import tkinter as tk
from tkinter import messagebox, scrolledtext
import re
import requests
import base64
import json
import urllib.parse
import threading
import time

class V2RayScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("V2Ray 节点提取 & 一键发布工具 (Dpaste版)")
        self.root.geometry("750x700")

        self.final_node_list = []

        # --- 顶部控制区 ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10, fill=tk.X, padx=10)

        tk.Label(top_frame, text="目标网页 URL:").pack(anchor=tk.W)
        self.url_entry = tk.Entry(top_frame, width=80)
        self.url_entry.pack(fill=tk.X, pady=2)
        self.url_entry.insert(0, "https://v2raya.net/free-nodes/free-v2ray-node-subscriptions.html")

        # --- 按钮区 ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(
            btn_frame, text="1. 开始抓取", command=self.start_thread,
            bg="navy", fg="white", font=("Arial", 11, "bold"), width=15
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame, text="2. 复制所有节点", command=self.copy_to_clipboard,
            bg="green", fg="white", font=("Arial", 11), width=15
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            btn_frame, text="3. 生成订阅链接(分享)", command=self.publish_thread,
            bg="#FF5722", fg="white", font=("Arial", 11, "bold"), width=20
        ).grid(row=0, column=2, padx=5)

        # --- 显示区 ---
        paned_window = tk.PanedWindow(root, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        res_frame = tk.LabelFrame(paned_window, text="提取结果 (直接显示在这里)")
        paned_window.add(res_frame, height=350)

        self.result_text = scrolledtext.ScrolledText(res_frame)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_frame = tk.LabelFrame(paned_window, text="运行日志")
        paned_window.add(log_frame)

        self.log_text = scrolledtext.ScrolledText(log_frame, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def start_thread(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        self.result_text.delete(1.0, tk.END)
        self.final_node_list = []

        threading.Thread(target=self.start_scraping, daemon=True).start()

    def publish_thread(self):
        threading.Thread(target=self.publish_subscription, daemon=True).start()

    # ---------------- 工具函数 ----------------

    def safe_base64_decode(self, s):
        if not s:
            return ""
        s = s.strip()
        missing = 4 - len(s) % 4
        if missing != 4:
            s += "=" * missing
        try:
            return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
        except:
            return ""

    def get_node_name(self, link):
        try:
            if link.startswith("vmess://"):
                data = self.safe_base64_decode(link.replace("vmess://", ""))
                if data:
                    return json.loads(data).get("ps", "")
            elif "://" in link:
                return urllib.parse.unquote(urllib.parse.urlparse(link).fragment)
        except:
            pass
        return ""

    def is_target_country(self, name):
        if not name:
            return False
        name_l = name.lower()
        import re
        # 美国/US, 英国/UK, 法国/FR, 德国/DE
        patterns = [
            r"美国|united states|\bus\b|\(us\)|\[us\]|🇺🇸",
            r"英国|united kingdom|\buk\b|\(uk\)|\[uk\]|🇬🇧",
            r"法国|france|\bfr\b|\(fr\)|\[fr\]|🇫🇷",
            r"德国|germany|\bde\b|\(de\)|\[de\]|🇩🇪"
        ]
        return any(re.search(p, name_l) for p in patterns)

    def _parse_nodes(self, text):
        decoded = self.safe_base64_decode(text.strip()) or text
        count = 0
        for line in decoded.splitlines():
            line = line.strip()
            if not line: continue
            name = self.get_node_name(line)
            if self.is_target_country(name):
                self.final_node_list.append(line)
                count += 1
        return count

    # ---------------- 抓取逻辑 ----------------

    def start_scraping(self):
        url = self.url_entry.get().strip()
        self.log(f"🚀 开始抓取: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            self.log(f"❌ 网络错误: {e}")
            return

        subs = list(set(re.findall(r"https://fn[^\s\"'<]+", html)))
        backup_subs = re.findall(r"https?://[^\s\"'<>]+(?:sub|subscribe|node|json)[^\s\"'<>]*", html)
        subs = list(set(subs + backup_subs))

        if not subs:
            self.log("❌ 未发现订阅链接")
            return

        self.log(f"✅ 发现 {len(subs)} 个潜在订阅源")

        processed_urls = set()
        for i, sub in enumerate(subs):
            if sub in processed_urls: continue
            processed_urls.add(sub)
            
            self.log(f"[{i+1}/{len(subs)}] 解析: {sub[:50]}...")
            try:
                # 处理 JSON 索引
                if "json" in sub:
                    r_json = requests.get(sub, timeout=15, headers=headers)
                    try:
                        data = r_json.json()
                        if "subscriptions" in data:
                            self.log(f"   → 发现 JSON 索引，包含 {len(data['subscriptions'])} 个链接")
                            for item in data["subscriptions"]:
                                u = item.get("url")
                                if u and u not in processed_urls:
                                    processed_urls.add(u)
                                    # 自动抓取子链接
                                    r_sub = requests.get(u, timeout=12, headers=headers)
                                    c = self._parse_nodes(r_sub.text)
                                    if c: self.log(f"     + 子链接命中 {c} 个节点")
                            continue
                    except: pass

                r = requests.get(sub, timeout=12, headers=headers)
                c = self._parse_nodes(r.text)
                if c: self.log(f"   → 命中 {c} 个节点")
            except Exception as e:
                self.log(f"   → 错误: {e}")

        self.final_node_list = list(set(self.final_node_list))
        self.log(f"🎉 完成，共筛选 {len(self.final_node_list)} 个节点")

        if self.final_node_list:
            self.result_text.insert(tk.END, "\n".join(self.final_node_list))

    def copy_to_clipboard(self):
        data = self.result_text.get(1.0, tk.END).strip()
        if data:
            self.root.clipboard_clear()
            self.root.clipboard_append(data)
            messagebox.showinfo("成功", "已复制到剪贴板")
        else:
            messagebox.showwarning("空", "没有内容")

    # ---------------- 发布逻辑 ----------------

    def publish_subscription(self):
        nodes = self.result_text.get(1.0, tk.END).strip()
        if not nodes:
            messagebox.showwarning("错误", "结果为空")
            return

        b64 = base64.b64encode(nodes.encode()).decode()
        self.log("🌐 上传至 Dpaste...")

        try:
            r = requests.post("https://dpaste.com/api/", data={
                "content": b64,
                "expiry_days": 7
            })
            if r.status_code in (200, 201):
                url = r.text.strip() + ".txt"
                self.show_copy_dialog(url)
        except Exception as e:
            self.log(f"❌ 发布失败: {e}")

    def show_copy_dialog(self, url):
        top = tk.Toplevel(self.root)
        top.title("订阅链接")
        top.geometry("520x180")

        tk.Label(top, text="订阅链接生成成功").pack(pady=10)
        e = tk.Entry(top, width=65)
        e.pack()
        e.insert(0, url)
        e.config(state="readonly")

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("成功", "已复制")
            top.destroy()

        tk.Button(top, text="复制并关闭", command=copy, bg="green", fg="white").pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    V2RayScraperApp(root)
    root.mainloop()
