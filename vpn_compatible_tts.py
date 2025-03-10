#!/usr/bin/env python3
"""
VPN兼容的剪贴板TTS热键监听器
当按下指定的热键组合时，读取剪贴板内容并通过TTS服务转为语音
特别优化以在VPN环境下工作
"""

import pyperclip
import time
import threading
import logging
import os
import sys
import platform
import socket
from typing import Optional, Dict, Any, List

# 导入pynput库（在macOS上处理热键更可靠）
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    USE_PYNPUT = True
except ImportError:
    print("警告: 未找到pynput库，尝试安装: pip install pynput")
    import keyboard
    USE_PYNPUT = False

# 导入TTS客户端
try:
    from tts_client import TTSClient
except ImportError:
    print("错误: 找不到tts_client模块，请确保tts_client.py在同一目录下")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VPN-HotkeyTTS")

# 检测操作系统
SYSTEM = platform.system()

class VPNCompatibleTTSHotkey:
    """VPN兼容的剪贴板TTS热键监听器类"""
    
    def __init__(
        self, 
        hotkey: str = "ctrl+option+cmd+p",
        server_port: int = 8090,
        model_name: str = None,
        language: str = None,
        max_retries: int = 3
    ):
        """
        初始化热键监听器
        
        参数:
        hotkey (str): 触发TTS的热键组合
        server_port (int): TTS服务器的端口
        model_name (str): 要使用的TTS模型名称，None表示自动选择
        language (str): 语言代码，None表示自动检测
        max_retries (int): 最大重试次数
        """
        self.hotkey = hotkey
        self.server_port = server_port
        self.model_name = model_name
        self.language = language
        self.max_retries = max_retries
        
        # 初始化其他属性
        self.last_text = ""
        self.lock = threading.Lock()
        self.is_processing = False
        self.running = False
        self.pynput_listener = None
        self.client = None
        
        # 连接服务器（尝试不同的地址）
        self._connect_to_server()
        
        # 如果使用pynput，设置热键组合
        if USE_PYNPUT:
            # 设置热键组合的各个键
            self.ctrl_key = Key.ctrl
            self.option_key = Key.alt  # macOS中option就是alt
            self.cmd_key = Key.cmd
            self.p_key = KeyCode.from_char('p')
            
            # 当前按下的键集合
            self.current_keys = set()
    
    def _get_potential_server_urls(self) -> List[str]:
        """获取可能的服务器URL列表"""
        port = self.server_port
        urls = []
        
        # 添加常用的本地主机名和IP
        urls.append(f"http://localhost:{port}")
        urls.append(f"http://127.0.0.1:{port}")
        urls.append(f"http://0.0.0.0:{port}")
        
        # 添加IPv6回环地址
        urls.append(f"http://[::1]:{port}")
        
        # 尝试获取本机IP地址（非回环）
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip != "127.0.0.1":
                urls.append(f"http://{ip}:{port}")
                urls.append(f"http://{hostname}:{port}")
        except:
            pass
        
        logger.info(f"尝试以下服务器URLs: {urls}")
        return urls
    
    def _connect_to_server(self):
        """尝试不同的地址连接到服务器"""
        urls = self._get_potential_server_urls()
        
        for url in urls:
            try:
                logger.info(f"尝试连接到: {url}")
                client = TTSClient(server_url=url)
                client.check_server_health()
                self.client = client
                logger.info(f"成功连接到TTS服务器: {url}")
                return
            except Exception as e:
                logger.warning(f"无法连接到 {url}: {e}")
        
        # 所有URL都失败
        logger.error("无法连接到TTS服务器。请确保服务器正在运行。")
        logger.error("如果您正在使用VPN，请尝试:")
        logger.error("1. 在启动VPN之前先启动TTS服务器")
        logger.error("2. 使用不同的端口")
        logger.error("3. 在VPN设置中允许本地网络连接")
        sys.exit(1)
    
    def _read_clipboard(self) -> str:
        """读取剪贴板内容"""
        try:
            return pyperclip.paste().strip()
        except Exception as e:
            logger.error(f"读取剪贴板失败: {e}")
            return ""
    
    def _on_pynput_press(self, key):
        """pynput按键按下回调函数"""
        try:
            # 将按键添加到当前按下的键集合中
            self.current_keys.add(key)
            
            # 检查热键组合是否全部按下
            if (self.ctrl_key in self.current_keys and 
                self.option_key in self.current_keys and 
                self.cmd_key in self.current_keys and 
                self.p_key in self.current_keys):
                self._handle_hotkey()
        except Exception as e:
            logger.error(f"处理按键按下事件时出错: {e}")
    
    def _on_pynput_release(self, key):
        """pynput按键释放回调函数"""
        try:
            if key in self.current_keys:
                self.current_keys.remove(key)
        except Exception as e:
            logger.error(f"处理按键释放事件时出错: {e}")
        
        # 如果按下了Esc键，停止监听
        if key == Key.esc and self.running:
            logger.info("检测到Esc键，停止监听")
            return False
    
    def _handle_hotkey(self):
        """热键触发时的处理函数"""
        # 使用锁防止多次并发处理
        if self.is_processing:
            logger.info("已有转换进行中，忽略此次触发")
            return
            
        with self.lock:
            self.is_processing = True
            
        try:
            logger.info(f"检测到热键 {self.hotkey}")
            
            # 读取剪贴板内容
            text = self._read_clipboard()
            
            # 检查内容是否为空或与上次相同
            if not text:
                logger.warning("剪贴板内容为空，取消处理")
                self.is_processing = False
                return
                
            if text == self.last_text:
                logger.info("剪贴板内容与上次相同，仍继续处理")
            
            # 显示要处理的文本
            preview = text[:50] + "..." if len(text) > 50 else text
            logger.info(f"处理文本: {preview}")
            
            # 选择合适的模型
            model_name = self.model_name
            if not model_name:
                # 自动选择模型
                if any(u'\u4e00' <= c <= u'\u9fff' for c in text):
                    logger.info("检测到中文文本，使用XTTS模型")
                    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
                else:
                    logger.info("使用默认英文模型")
                    model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            
            # 转换为语音（在新线程中处理以不阻塞热键监听）
            threading.Thread(
                target=self._convert_to_speech, 
                args=(text, model_name)
            ).start()
            
            # 更新上次处理的文本
            self.last_text = text
            
        except Exception as e:
            logger.error(f"处理热键事件时出错: {e}")
            self.is_processing = False
    
    def _convert_to_speech(self, text: str, model_name: str):
        """将文本转换为语音"""
        try:
            logger.info(f"开始将文本转换为语音，使用模型: {model_name}")
            
            # 添加重试机制
            for attempt in range(self.max_retries):
                try:
                    # 调用TTS客户端
                    self.client.text_to_speech(
                        text=text,
                        model_name=model_name,
                        language=self.language,
                        play=True
                    )
                    logger.info("语音转换和播放完成")
                    break
                except Exception as e:
                    logger.warning(f"尝试 {attempt+1}/{self.max_retries} 失败: {e}")
                    if attempt < self.max_retries - 1:
                        logger.info("正在重新连接服务器...")
                        self._connect_to_server()
                        time.sleep(1)  # 等待一秒再重试
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"转换文本为语音失败: {e}")
        finally:
            self.is_processing = False
    
    def start(self):
        """启动热键监听"""
        if self.running:
            logger.warning("热键监听器已经在运行")
            return
            
        try:
            self.running = True
            
            if USE_PYNPUT:
                # 使用pynput监听热键 (推荐用于macOS)
                logger.info(f"使用pynput启动热键监听器，按下 {self.hotkey} 将朗读剪贴板内容")
                
                # 创建并启动键盘监听器
                self.pynput_listener = keyboard.Listener(
                    on_press=self._on_pynput_press,
                    on_release=self._on_pynput_release
                )
                self.pynput_listener.start()
                
                # 等待监听器停止
                try:
                    while self.running and self.pynput_listener.is_alive():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    logger.info("接收到Ctrl+C信号，停止监听")
                    self.stop()
            else:
                # 使用keyboard库监听热键
                keyboard.add_hotkey(self.hotkey, self._handle_hotkey)
                
                logger.info(f"热键监听器已启动，按下 {self.hotkey} 将朗读剪贴板内容")
                logger.info("按下 Ctrl+C 退出程序")
                
                # 保持程序运行
                while self.running:
                    time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("接收到退出信号")
        except Exception as e:
            logger.error(f"热键监听器出错: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止热键监听"""
        if not self.running:
            return
            
        try:
            self.running = False
            
            if USE_PYNPUT and self.pynput_listener:
                # 停止pynput监听器
                self.pynput_listener.stop()
            elif not USE_PYNPUT:
                # 移除keyboard热键
                keyboard.remove_hotkey(self.hotkey)
                
            logger.info("热键监听器已停止")
        except Exception as e:
            logger.error(f"停止热键监听器时出错: {e}")


def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='VPN兼容的剪贴板TTS热键监听器')
    parser.add_argument('--hotkey', type=str, default='ctrl+option+cmd+p', 
                        help='触发TTS的热键组合 (默认: ctrl+option+cmd+p)')
    parser.add_argument('--port', type=int, default=8090,
                        help='TTS服务器的端口 (默认: 8090)')
    parser.add_argument('--server-url', type=str, default=None,
                        help='完整的TTS服务器URL (例如: http://127.0.0.1:8090), 优先级高于端口设置')
    parser.add_argument('--model', type=str, default=None,
                        help='指定要使用的TTS模型，未指定则自动选择')
    parser.add_argument('--language', type=str, default=None,
                        help='指定语言代码，未指定则自动检测')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='连接失败时的最大重试次数 (默认: 3)')
    args = parser.parse_args()
    
    # 创建并启动热键监听器
    if args.server_url:
        # 如果提供了完整URL，解析端口
        try:
            server_port = int(args.server_url.split(':')[-1].split('/')[0])
        except:
            server_port = args.port
        
        print(f"使用指定的服务器URL: {args.server_url}")
        
        # 使用自定义的TTSClient访问服务器
        from tts_client import TTSClient
        # 测试连接
        try:
            client = TTSClient(server_url=args.server_url)
            client.check_server_health()
            print(f"✓ 成功连接到服务器: {args.server_url}")
        except Exception as e:
            print(f"✗ 无法连接到指定的服务器URL: {args.server_url}")
            print(f"错误: {e}")
            print("请运行 python debug_vpn_connection.py 诊断连接问题")
            sys.exit(1)
            
        hotkey_listener = VPNCompatibleTTSHotkey(
            hotkey=args.hotkey,
            server_port=server_port,  # 仍然保存端口信息
            model_name=args.model,
            language=args.language,
            max_retries=args.max_retries
        )
        
        # 覆盖客户端
        hotkey_listener.client = client
    else:
        hotkey_listener = VPNCompatibleTTSHotkey(
            hotkey=args.hotkey,
            server_port=args.port,
            model_name=args.model,
            language=args.language,
            max_retries=args.max_retries
        )
    
    # 显示启动信息
    print("\n" + "="*50)
    print(" VPN兼容的剪贴板TTS热键监听器已启动")
    print("="*50)
    print(f" 热键: {args.hotkey}")
    
    if args.server_url:
        print(f" 服务器URL: {args.server_url}")
    else:
        print(f" 服务器端口: {args.port}")
        if hasattr(hotkey_listener, 'client') and hotkey_listener.client:
            print(f" 已连接到: {hotkey_listener.client.server_url}")
    
    print(f" 模型: {'自动选择' if args.model is None else args.model}")
    print(f" 语言: {'自动检测' if args.language is None else args.language}")
    print("="*50)
    print(" 使用方法:")
    print(" 1. 复制任意文本")
    print(f" 2. 按下 {args.hotkey} 热键组合")
    print(" 3. 系统将朗读剪贴板中的内容")
    print("="*50)
    
    if SYSTEM == "Darwin":  # macOS
        print(" macOS注意事项:")
        print(" - 您可能需要在系统偏好设置>安全性与隐私>隐私>辅助功能中")
        print("   授予终端或Python程序辅助功能权限")
        print("="*50)
    
    print(" 按下 Esc 键或 Ctrl+C 退出程序")
    print("="*50 + "\n")
    
    # 启动监听
    hotkey_listener.start()


if __name__ == "__main__":
    main() 