 #!/usr/bin/env python3
"""
剪贴板TTS热键监听器
当按下指定的热键组合时，读取剪贴板内容并通过TTS服务转为语音
"""

import keyboard
import pyperclip
import time
import threading
import logging
import os
import sys
from typing import Optional, Dict, Any

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
logger = logging.getLogger("HotkeyTTS")

class ClipboardTTSHotkey:
    """剪贴板TTS热键监听器类"""
    
    def __init__(
        self, 
        hotkey: str = "ctrl+alt+s",
        server_url: str = "http://localhost:8090",
        model_name: str = None,
        language: str = None
    ):
        """
        初始化热键监听器
        
        参数:
        hotkey (str): 触发TTS的热键组合
        server_url (str): TTS服务器的URL
        model_name (str): 要使用的TTS模型名称，None表示自动选择
        language (str): 语言代码，None表示自动检测
        """
        self.hotkey = hotkey
        self.server_url = server_url
        self.model_name = model_name
        self.language = language
        self.client = TTSClient(server_url=server_url)
        self.last_text = ""
        self.lock = threading.Lock()
        self.is_processing = False
        self.running = False
        
        # 检查TTS服务器是否可用
        try:
            self.client.check_server_health()
            logger.info(f"成功连接到TTS服务器: {server_url}")
        except Exception as e:
            logger.error(f"无法连接到TTS服务器 ({server_url}): {e}")
            logger.error("请确保TTS服务器正在运行 (python tts_server.py)")
            sys.exit(1)
    
    def _read_clipboard(self) -> str:
        """读取剪贴板内容"""
        try:
            return pyperclip.paste().strip()
        except Exception as e:
            logger.error(f"读取剪贴板失败: {e}")
            return ""
    
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
            
            # 调用TTS客户端
            self.client.text_to_speech(
                text=text,
                model_name=model_name,
                language=self.language,
                play=True
            )
            
            logger.info("语音转换和播放完成")
            
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
            # 注册热键
            keyboard.add_hotkey(self.hotkey, self._handle_hotkey)
            
            self.running = True
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
            # 移除热键
            keyboard.remove_hotkey(self.hotkey)
            self.running = False
            logger.info("热键监听器已停止")
        except Exception as e:
            logger.error(f"停止热键监听器时出错: {e}")


def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='剪贴板TTS热键监听器')
    parser.add_argument('--hotkey', type=str, default='ctrl+alt+s', 
                        help='触发TTS的热键组合 (默认: ctrl+alt+s)')
    parser.add_argument('--server', type=str, default='http://localhost:8090',
                        help='TTS服务器的URL (默认: http://localhost:8090)')
    parser.add_argument('--model', type=str, default=None,
                        help='指定要使用的TTS模型，未指定则自动选择')
    parser.add_argument('--language', type=str, default=None,
                        help='指定语言代码，未指定则自动检测')
    args = parser.parse_args()
    
    # 创建并启动热键监听器
    hotkey_listener = ClipboardTTSHotkey(
        hotkey=args.hotkey,
        server_url=args.server,
        model_name=args.model,
        language=args.language
    )
    
    # 显示启动信息
    print("\n" + "="*50)
    print(" 剪贴板TTS热键监听器已启动")
    print("="*50)
    print(f" 热键: {args.hotkey}")
    print(f" 服务器: {args.server}")
    print(f" 模型: {'自动选择' if args.model is None else args.model}")
    print(f" 语言: {'自动检测' if args.language is None else args.language}")
    print("="*50)
    print(" 使用方法:")
    print(" 1. 复制任意文本")
    print(f" 2. 按下 {args.hotkey} 热键组合")
    print(" 3. 系统将朗读剪贴板中的内容")
    print("="*50)
    print(" 按下 Ctrl+C 退出程序")
    print("="*50 + "\n")
    
    # 启动监听
    hotkey_listener.start()


if __name__ == "__main__":
    main()