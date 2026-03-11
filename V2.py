import tkinter as tk
from tkinter import messagebox, scrolledtext
import re
import requests
import base64
import json
import urllib.parse
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
        if missing:
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

    # 🔥【核心修改点】新增 法国 + 德国
    def is_target_country(self, name):
        if not name:
            return False

        keywords = [
            # 美国
            "美国", "united states", " us ", "(us)", "[us]", "🇺🇸",
            # 英国
            "英国", "united kingdom", " uk ", "(uk)", "[uk]", "🇬🇧",
            # 法国
            "法国", "france", " fr ", "(fr)", "[fr]", "🇫🇷",
            # 德国
            "德国", "germany", " de ", "(de)", "[de]", "🇩🇪"
        ]

        name_l = name.lower()
        return any(k in name_l for k in keywords)

    # ---------------- 抓取逻辑 ----------------

    def start_scraping(self):
        url = self.url_entry.get().strip()
        self.log(f"🚀 开始访问: {url}")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--log-level=3")

        try:
            driver = webdriver.Chrome(service=Service(), options=chrome_options)
            driver.get(url)
            time.sleep(5)
            html = driver.page_source
            driver.quit()
        except Exception as e:
            self.log(f"❌ Selenium 错误: {e}")
            return

        subs = list(set(re.findall(r"https://fn[^\s\"'<]+", html)))
        if not subs:
            self.log("❌ 未发现订阅链接")
            return

        self.log(f"✅ 发现 {len(subs)} 个订阅源")

        for i, sub in enumerate(subs):
            self.log(f"[{i+1}/{len(subs)}] 解析 {sub}")
            try:
                r = requests.get(sub, timeout=10)
                text = self.safe_base64_decode(r.text.strip()) or r.text
                count = 0
                for line in text.splitlines():
                    name = self.get_node_name(line)
                    if self.is_target_country(name):
                        self.final_node_list.append(line)
                        count += 1
                self.log(f"   -> 命中 {count} 个节点")
            except Exception as e:
                self.log(f"   -> 错误: {e}")

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
        self.log("🌐 上传至 Dpaste")

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
