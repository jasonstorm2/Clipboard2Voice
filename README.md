# 文本朗读助手

一个便捷的工具，可以将剪贴板中的文本自动转换为语音并朗读出来。支持中英文，自动检测语言，一键朗读。

![版本](https://img.shields.io/badge/版本-1.0.0-blue)
![Python版本](https://img.shields.io/badge/Python-3.7%2B-brightgreen)
![许可证](https://img.shields.io/badge/许可证-MIT-green)

## 核心功能

- 🔊 **一键朗读**：复制文本后按下快捷键即可朗读
- 🌐 **多语言支持**：自动检测中文和英文，选择合适的语音模型
- 💻 **多环境适配**：提供微服务版、VPN兼容版和独立版
- 🎯 **简单易用**：无需编程知识，适合所有用户

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/用户名/项目名.git
cd 项目名

# 安装依赖
pip install TTS flask requests pynput keyboard pyperclip

# 在Windows系统上额外安装
# pip install playsound

# 设置权限（macOS/Linux）
chmod +x run_server.sh run_client.sh run_hotkey_mac.sh run_standalone.sh run_vpn_tts.sh
```

### 使用（三种方案）

**1. 标准微服务方案**（普通网络环境）：
```bash
# 终端1：启动服务器
./run_server.sh

# 终端2：启动热键监听器
./run_hotkey_mac.sh

# 现在，复制任意文本并按下 ctrl+option+cmd+p 即可朗读
```

**2. 独立方案**（VPN环境或不稳定网络）：
```bash
# 只需启动独立应用
./run_standalone.sh

# 复制文本并按下 ctrl+option+cmd+p
```

**3. VPN兼容方案**（轻度VPN干扰）：
```bash
# 终端1：启动服务器
./run_server.sh

# 终端2：启动VPN兼容版
./run_vpn_tts.sh

# 复制文本并按下 ctrl+option+cmd+p
```

## 系统要求

- Python 3.7或更高版本
- macOS、Windows或Linux系统
- 约2GB可用内存（用于语音模型）
- 互联网连接（首次下载模型时需要）

## 详细文档

- [用户指南](README_USER_GUIDE.md) - 详细的安装和使用说明
- [VPN问题解决](vpn_issue_resolution.md) - VPN环境下的故障排除指南
- [项目结构](docs/project_structure.md) - 项目代码结构和组件说明（如有）

## 许可证

本项目基于MIT许可证开源。

## 致谢

- [Coqui TTS](https://github.com/coqui-ai/TTS) - 提供高质量的文本转语音功能
- [Flask](https://flask.palletsprojects.com/) - 用于构建微服务API
- [pynput](https://github.com/moses-palmer/pynput) - 提供可靠的全局热键监听

---

欢迎提出问题、反馈和贡献！ 