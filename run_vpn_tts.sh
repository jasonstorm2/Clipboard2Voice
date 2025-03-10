#!/bin/bash

echo "启动VPN兼容的剪贴板TTS热键监听器..."
echo "热键: ctrl+option+cmd+p"
echo "服务器端口: 8090"
echo ""
echo "注意: 首次运行可能需要在系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能中"
echo "授予终端或Python程序辅助功能权限"
echo ""

python vpn_compatible_tts.py "$@" 