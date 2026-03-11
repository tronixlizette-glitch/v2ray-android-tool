# V2Ray 节点提取工具 - Android版

## 功能介绍
- 🚀 **抓取订阅源**：从目标网页自动发现 V2Ray 订阅链接
- 🔍 **智能筛选**：筛选美国、英国、法国、德国节点
- 📋 **一键复制**：将所有节点复制到剪贴板
- 🔗 **生成订阅链接**：上传至 Dpaste 生成可分享的订阅链接

## 文件说明
| 文件 | 说明 |
|------|------|
| `main.py` | Kivy 版 Android 程序（手机UI适配） |
| `V2.py` | 原始 PC 版程序（tkinter） |
| `buildozer.spec` | Android 打包配置 |
| `.github/workflows/build_apk.yml` | GitHub Actions 自动打包流程 |

## 打包方法
APK 通过 GitHub Actions 自动构建。将代码推送到 GitHub 后，
在 **Actions** → **Build Android APK** 中查看构建进度并下载 APK。
