#!/usr/bin/env python3
"""
独立的TTS热键监听器
当按下指定的热键组合时，读取剪贴板内容并直接使用TTS转为语音
不依赖于外部服务器
"""

import pyperclip
import time
import threading
import logging
import os
import sys
import platform
import subprocess
import tempfile
from typing import Optional, Dict, Any

# 导入pynput库（在macOS上处理热键更可靠）
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    USE_PYNPUT = True
except ImportError:
    print("警告: 未找到pynput库，尝试安装: pip install pynput")
    import keyboard
    USE_PYNPUT = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Standalone-TTS")

# 检测操作系统
SYSTEM = platform.system()

class StandaloneTTSHotkey:
    """独立的TTS热键监听器类"""
    
    def __init__(
        self, 
        hotkey: str = "ctrl+option+cmd+p",
        model_name: str = None,
        language: str = None
    ):
        """
        初始化热键监听器
        
        参数:
        hotkey (str): 触发TTS的热键组合
        model_name (str): 要使用的TTS模型名称，None表示自动选择
        language (str): 语言代码，None表示自动检测
        """
        self.hotkey = hotkey
        self.model_name = model_name
        self.language = language
        
        # 初始化其他属性
        self.last_text = ""
        self.lock = threading.Lock()
        self.is_processing = False
        self.running = False
        self.pynput_listener = None
        
        # 初始化TTS模型
        self._initialize_tts()
        
        # 如果使用pynput，设置热键组合
        if USE_PYNPUT:
            # 设置热键组合的各个键
            self.ctrl_key = Key.ctrl
            self.option_key = Key.alt  # macOS中option就是alt
            self.cmd_key = Key.cmd
            self.p_key = KeyCode.from_char('p')
            
            # 当前按下的键集合
            self.current_keys = set()
    
    def _initialize_tts(self):
        """初始化TTS模型"""
        logger.info("初始化TTS模型...")
        
        try:
            # 预加载支持模块
            import torch
            
            # 修补torch.load函数
            original_torch_load = torch.load
            
            def patched_torch_load(f, map_location=None, pickle_module=None, **kwargs):
                try:
                    # 首先尝试使用默认设置加载
                    return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, **kwargs)
                except Exception as e:
                    logger.warning(f"使用默认设置加载模型失败，尝试使用weights_only=False: {str(e)}")
                    try:
                        # 如果失败，尝试使用weights_only=False
                        return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, weights_only=False, **kwargs)
                    except Exception as e2:
                        logger.error(f"所有加载方法都失败: {str(e2)}")
                        raise e2
            
            # 替换torch.load函数
            torch.load = patched_torch_load
            
            # 添加安全的全局类
            try:
                from TTS.tts.configs.xtts_config import XttsConfig
                from TTS.tts.models.xtts import XttsAudioConfig
                safe_classes = [XttsConfig, XttsAudioConfig]
                torch.serialization.add_safe_globals(safe_classes)
                logger.info(f"已添加安全类: {[cls.__name__ for cls in safe_classes]}")
            except Exception as e:
                logger.warning(f"添加安全类失败 (这可能不是问题): {e}")
            
            # 导入TTS
            from TTS.api import TTS
            
            # 创建英文模型实例
            logger.info("加载英文TTS模型...")
            self.en_tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            
            # 创建多语言模型实例
            logger.info("加载多语言TTS模型...")
            self.ml_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            
            # 准备参考音频
            self._prepare_reference_audio()
            
            logger.info("TTS模型初始化完成")
            
        except Exception as e:
            logger.error(f"初始化TTS模型失败: {e}")
            logger.error("将尝试使用系统TTS作为后备")
            self.en_tts = None
            self.ml_tts = None
    
    def _prepare_reference_audio(self):
        """准备参考音频文件（用于XTTS模型）"""
        try:
            reference_path = "reference_audio.wav"
            if os.path.exists(reference_path):
                logger.info(f"参考音频文件已存在: {reference_path}")
                self.reference_audio = reference_path
                return
            
            # 创建参考音频
            logger.info("创建参考音频文件...")
            self.en_tts.tts_to_file(
                text="This is a reference audio for voice cloning.", 
                file_path=reference_path
            )
            
            if os.path.exists(reference_path):
                logger.info(f"参考音频文件已创建: {reference_path}")
                self.reference_audio = reference_path
            else:
                logger.error("创建参考音频失败")
                self.reference_audio = None
                
        except Exception as e:
            logger.error(f"准备参考音频失败: {e}")
            self.reference_audio = None
    
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
                is_chinese = any(u'\u4e00' <= c <= u'\u9fff' for c in text)
                if is_chinese:
                    logger.info("检测到中文文本，使用多语言模型")
                    model_name = "multilingual"
                else:
                    logger.info("使用默认英文模型")
                    model_name = "english"
            
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
    
    def _play_audio(self, audio_path: str) -> None:
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
            logger.error(f"播放音频失败: {e}")
    
    def _fallback_tts(self, text: str) -> None:
        """使用系统TTS作为后备"""
        try:
            logger.info("使用系统TTS作为后备...")
            
            if SYSTEM == "Darwin":  # macOS
                subprocess.run(["say", text])
                logger.info("系统TTS播放完成")
                return True
            elif SYSTEM == "Windows":
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.say(text)
                    engine.runAndWait()
                    logger.info("系统TTS播放完成")
                    return True
                except:
                    logger.error("Windows系统TTS失败")
                    return False
            else:  # Linux
                try:
                    subprocess.run(["espeak", text])
                    logger.info("系统TTS播放完成")
                    return True
                except:
                    logger.error("Linux系统TTS失败")
                    return False
        except Exception as e:
            logger.error(f"系统TTS失败: {e}")
            return False
    
    def _convert_to_speech(self, text: str, model_name: str):
        """将文本转换为语音"""
        try:
            logger.info(f"开始将文本转换为语音，使用模型: {model_name}")
            
            # 检查TTS模型是否已初始化
            if (model_name == "english" and self.en_tts is None) or \
               (model_name == "multilingual" and self.ml_tts is None):
                logger.warning(f"TTS模型未初始化，使用系统TTS作为后备")
                self._fallback_tts(text)
                self.is_processing = False
                return
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                output_path = temp_file.name
            
            # 使用适当的模型生成语音
            if model_name == "english":
                self.en_tts.tts_to_file(text=text, file_path=output_path)
            else:  # multilingual
                # 准备参数
                tts_params = {"text": text, "file_path": output_path}
                
                # 如果是多语言模型，判断语言
                if any(u'\u4e00' <= c <= u'\u9fff' for c in text):
                    tts_params["language"] = "zh-cn"
                else:
                    tts_params["language"] = "en"
                
                # 如果有参考音频，添加到参数
                if self.reference_audio:
                    tts_params["speaker_wav"] = self.reference_audio
                
                # 生成语音
                self.ml_tts.tts_to_file(**tts_params)
            
            # 播放生成的音频
            logger.info(f"语音已生成，播放音频: {output_path}")
            self._play_audio(output_path)
            
            logger.info("语音转换和播放完成")
            
        except Exception as e:
            logger.error(f"转换文本为语音失败: {e}")
            # 尝试使用系统TTS作为后备
            self._fallback_tts(text)
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
    parser = argparse.ArgumentParser(description='独立的TTS热键监听器（不依赖外部服务器）')
    parser.add_argument('--hotkey', type=str, default='ctrl+option+cmd+p', 
                        help='触发TTS的热键组合 (默认: ctrl+option+cmd+p)')
    parser.add_argument('--model', type=str, default=None,
                        help='指定要使用的TTS模型，未指定则自动选择')
    parser.add_argument('--language', type=str, default=None,
                        help='指定语言代码，未指定则自动检测')
    args = parser.parse_args()
    
    # 创建并启动热键监听器
    hotkey_listener = StandaloneTTSHotkey(
        hotkey=args.hotkey,
        model_name=args.model,
        language=args.language
    )
    
    # 显示启动信息
    print("\n" + "="*50)
    print(" 独立的TTS热键监听器已启动")
    print("="*50)
    print(f" 热键: {args.hotkey}")
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