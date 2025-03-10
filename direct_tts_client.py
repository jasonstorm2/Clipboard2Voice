#!/usr/bin/env python3
"""
直接TTS客户端
直接使用原始TCP套接字连接TTS服务器，绕过HTTP层
"""

import socket
import json
import sys
import os
import subprocess
import tempfile
import time
import platform
import pyperclip
from typing import Optional, Dict, Any

# 默认服务器设置
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090

# 检测操作系统
SYSTEM = platform.system()

def check_server_socket(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: int = 2) -> bool:
    """测试是否可以通过套接字连接到服务器"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"套接字连接错误: {e}")
        return False

def play_audio(audio_path: str) -> None:
    """播放音频文件"""
    try:
        if SYSTEM == "Darwin":  # macOS
            subprocess.run(["afplay", audio_path])
        elif SYSTEM == "Windows":
            from playsound import playsound
            playsound(audio_path)
        else:  # Linux
            subprocess.run(["aplay", audio_path])
    except Exception as e:
        print(f"播放音频失败: {e}")

def text_to_speech_direct(
    text: str, 
    output_path: Optional[str] = None,
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT
) -> Optional[str]:
    """
    直接通过TCP连接将文本转换为语音
    
    参数:
    text (str): 要转换的文本
    output_path (str, optional): 输出音频文件路径，如不指定则使用临时文件
    host (str): TTS服务器主机名/IP
    port (int): TTS服务器端口
    
    返回:
    str: 生成的音频文件路径，失败时返回None
    """
    # 检查文本是否为空
    if not text or not text.strip():
        print("错误: 文本为空")
        return None
    
    # 检查服务器连接
    if not check_server_socket(host, port):
        print(f"错误: 无法连接到服务器 {host}:{port}")
        return None
    
    # 如果未指定输出路径，创建临时文件
    if output_path is None:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        output_path = temp_file.name
        temp_file.close()
    
    # 创建到服务器的连接
    try:
        # 准备请求数据
        request_data = {
            "text": text,
            "output_path": output_path,
            "model_name": "tts_models/multilingual/multi-dataset/xtts_v2" if any(u'\u4e00' <= c <= u'\u9fff' for c in text) else "tts_models/en/ljspeech/tacotron2-DDC"
        }
        
        # 序列化为JSON
        json_data = json.dumps(request_data)
        
        # 连接服务器
        print(f"连接到服务器 {host}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            
            # 发送请求
            print("发送文本...")
            sock.sendall(json_data.encode('utf-8'))
            
            # 接收响应
            print("等待响应...")
            response = sock.recv(1024).decode('utf-8')
            
        print(f"服务器响应: {response}")
        
        # 检查文件是否已生成
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"音频已生成: {output_path}")
            return output_path
        else:
            print(f"音频文件未生成或为空")
            return None
            
    except Exception as e:
        print(f"生成语音时出错: {e}")
        return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='直接通过TCP连接的TTS客户端')
    parser.add_argument('--text', type=str, help='要转换为语音的文本')
    parser.add_argument('--output', type=str, help='输出音频文件路径')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help=f'TTS服务器主机 (默认: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'TTS服务器端口 (默认: {DEFAULT_PORT})')
    parser.add_argument('--clipboard', action='store_true', help='使用剪贴板中的文本')
    parser.add_argument('--play', action='store_true', help='生成后自动播放音频')
    
    args = parser.parse_args()
    
    # 获取文本
    text = None
    if args.clipboard:
        text = pyperclip.paste()
        print(f"从剪贴板读取文本: {text[:50]}..." if len(text) > 50 else text)
    elif args.text:
        text = args.text
    else:
        print("错误: 未提供文本。请使用--text参数或--clipboard选项")
        sys.exit(1)
    
    # 生成语音
    output_path = text_to_speech_direct(
        text=text,
        output_path=args.output,
        host=args.host,
        port=args.port
    )
    
    # 播放音频
    if output_path and args.play:
        print("播放音频...")
        play_audio(output_path)
    
    print("完成")

if __name__ == "__main__":
    main() 