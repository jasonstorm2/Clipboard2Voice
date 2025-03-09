import requests
import subprocess
import os
import tempfile
import time
import json
import argparse
from typing import Optional, Dict, Any

class TTSClient:
    """TTS客户端类，与TTS服务器交互生成语音"""
    
    def __init__(self, server_url: str = "http://localhost:8090"):
        """
        初始化TTS客户端
        
        参数:
        server_url (str): TTS服务器的URL地址
        """
        self.server_url = server_url
        self.session = requests.Session()
        
        # 检查服务是否可用
        try:
            self.check_server_health()
            print(f"成功连接到TTS服务器: {server_url}")
        except Exception as e:
            print(f"警告: 无法连接到TTS服务器 ({server_url}): {e}")
            print("请确保TTS服务器正在运行 (运行 python tts_server.py)")
    
    def check_server_health(self) -> bool:
        """检查服务器是否正常运行"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            raise ConnectionError(f"TTS服务器连接失败: {e}")
    
    def list_models(self) -> Dict[str, Any]:
        """获取服务器上已加载的模型列表"""
        try:
            response = self.session.get(f"{self.server_url}/models", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return {"loaded_models": [], "error": str(e)}
    
    def text_to_speech(
        self, 
        text: str, 
        output_path: Optional[str] = None,
        model_name: str = "tts_models/en/ljspeech/tacotron2-DDC", 
        language: Optional[str] = None, 
        play: bool = True
    ) -> str:
        """
        将文本转换为语音并可选择播放
        
        参数:
        text (str): 要转换的文本
        output_path (str, optional): 输出音频文件的路径，如果不指定将使用临时文件
        model_name (str): 要使用的TTS模型名称
        language (str, optional): 使用的语言，如果为None则自动检测
        play (bool): 是否立即播放生成的音频
        
        返回:
        str: 生成的音频文件路径
        """
        try:
            # 如果未指定输出路径，创建临时文件
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                output_path = temp_file.name
                temp_file.close()
            
            # 准备请求参数
            payload = {
                "text": text,
                "model_name": model_name
            }
            
            if language:
                payload["language"] = language
            
            # 向服务器发送请求
            print(f"正在请求TTS服务器生成语音...")
            start_time = time.time()
            
            response = self.session.post(
                f"{self.server_url}/tts",
                json=payload,
                timeout=60  # 大型模型可能需要更长时间
            )
            response.raise_for_status()
            
            # 保存生成的音频
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            processing_time = time.time() - start_time
            print(f"语音生成完成，耗时: {processing_time:.2f}秒")
            
            # 显示成功信息
            abs_path = os.path.abspath(output_path)
            print(f"语音已保存到: {abs_path}")
            
            # 播放生成的音频
            if play:
                self.play_audio(output_path)
            
            return output_path
        
        except Exception as e:
            print(f"生成语音失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    print(f"服务器错误详情: {json.dumps(error_details, ensure_ascii=False, indent=2)}")
                except:
                    print(f"服务器状态码: {e.response.status_code}")
                    print(f"服务器响应: {e.response.text}")
            raise
    
    def play_audio(self, audio_path: str) -> None:
        """播放音频文件"""
        print("正在播放音频...")
        try:
            # 检测操作系统并使用适当的命令播放音频
            if os.name == 'posix':  # macOS 或 Linux
                if 'darwin' in os.sys.platform:  # macOS
                    subprocess.run(["afplay", audio_path])
                else:  # Linux
                    subprocess.run(["aplay", audio_path])
            elif os.name == 'nt':  # Windows
                from playsound import playsound
                playsound(audio_path)
            else:
                print(f"无法确定如何在当前操作系统上播放音频: {os.name}")
        except Exception as e:
            print(f"播放音频失败: {e}")


def text_to_speech(text, output_path=None, model_name="tts_models/en/ljspeech/tacotron2-DDC", language=None, play=True):
    """
    便捷函数：将文本转换为语音并可选择播放
    
    参数:
    text (str): 要转换的文本
    output_path (str, optional): 输出音频文件的路径，如果不指定将使用临时文件
    model_name (str): 要使用的TTS模型名称
    language (str, optional): 使用的语言，如果为None则自动检测
    play (bool): 是否立即播放生成的音频
    
    返回:
    str: 生成的音频文件路径
    """
    client = TTSClient()
    return client.text_to_speech(
        text=text,
        output_path=output_path,
        model_name=model_name,
        language=language,
        play=play
    )


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='TTS客户端')
    parser.add_argument('--text', type=str, help='要转换为语音的文本')
    parser.add_argument('--output', type=str, help='输出音频文件的路径')
    parser.add_argument('--model', type=str, help='要使用的TTS模型名称')
    parser.add_argument('--language', type=str, help='语言代码 (例如: en, zh-cn)')
    parser.add_argument('--server', type=str, default='http://localhost:8090', help='TTS服务器URL')
    parser.add_argument('--no-play', action='store_true', help='生成后不播放音频')
    args = parser.parse_args()
    
    # 创建客户端
    client = TTSClient(server_url=args.server)
    
    # 如果提供了命令行参数，则使用它们
    if args.text:
        output_path = args.output if args.output else f"output_{int(time.time())}.wav"
        model_name = args.model if args.model else "tts_models/en/ljspeech/tacotron2-DDC"
        
        # 自动检测中文并设置模型
        if not args.model and any(u'\u4e00' <= c <= u'\u9fff' for c in args.text):
            print("检测到中文文本，使用XTTS v2模型")
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        
        client.text_to_speech(
            text=args.text,
            output_path=output_path,
            model_name=model_name,
            language=args.language,
            play=not args.no_play
        )
    else:
        # 检查已加载的模型
        models = client.list_models()
        print(f"服务器上已加载的模型: {models.get('loaded_models', [])}")
        
        # 英文示例
        english_text = "This is a test. TTS can generate natural and fluent speech."
        client.text_to_speech(english_text, "english_output.wav", "tts_models/en/ljspeech/tacotron2-DDC")
        
        # 留出一点间隔
        time.sleep(1)
        
        # 中文示例
        chinese_text = "这是一个测试。TTS可以生成自然流畅的语音。"
        client.text_to_speech(chinese_text, "chinese_output.wav", "tts_models/multilingual/multi-dataset/xtts_v2") 