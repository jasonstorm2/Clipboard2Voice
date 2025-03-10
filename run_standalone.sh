#!/bin/bash

echo "启动独立的TTS热键监听器（不依赖服务器）..."
echo "热键: ctrl+option+cmd+p"
echo ""
echo "注意: 首次运行会自动下载和加载模型，可能需要一些时间"
echo "注意: 您可能需要在系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能中"
echo "      授予终端或Python程序辅助功能权限"
echo ""

python standalone_tts.py "$@" 