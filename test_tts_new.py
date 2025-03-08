import sys
import torch
import importlib

# 尝试导入TTS并获取所需的类
try:
    from TTS.tts.configs.xtts_config import XttsConfig
    # 将XttsConfig类添加到安全全局对象列表
    torch.serialization.add_safe_globals([XttsConfig])
except ImportError:
    print("无法导入XttsConfig类")

try:
    # 导入TTS并尝试使用
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("成功加载TTS模型")
except Exception as e:
    print(f"加载TTS模型失败: {e}")
    
    # 如果失败，尝试补丁方式
    print("尝试使用weights_only=False方式加载...")
    original_torch_load = torch.load
    
    def patched_torch_load(f, map_location=None, pickle_module=None, **kwargs):
        kwargs['weights_only'] = False
        return original_torch_load(f, map_location, pickle_module, **kwargs)
    
    # 应用补丁
    torch.load = patched_torch_load
    
    try:
        # 重新导入TTS模块
        if 'TTS' in sys.modules:
            del sys.modules['TTS']
        from TTS.api import TTS
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("使用weights_only=False成功加载TTS模型")
    except Exception as e:
        print(f"所有尝试都失败了: {e}")



from TTS.api import TTS
import os
import subprocess
import time

def text_to_speech(text, output_path="output.wav", model_name="tts_models/en/ljspeech/tacotron2-DDC", play=True):
    """
    将文本转换为语音并播放
    
    参数:
    text (str): 要转换的文本
    output_path (str): 输出音频文件的路径
    model_name (str): 要使用的TTS模型名称
    play (bool): 是否立即播放生成的音频
    """
    try:
        # 初始化TTS
        print(f"正在加载模型: {model_name}")
        tts = TTS(model_name=model_name)
        
        # 设置多语言和多发言人参数
        speaker = None
        language = None
        
        if tts.is_multi_speaker:
            print(f"可用的发音人: {tts.speakers}")
            speaker = tts.speakers[0]  # 使用第一个发音人
        
        if tts.is_multi_lingual:
            print(f"可用的语言: {tts.languages}")
            # 根据文本自动选择语言
            if any(u'\u4e00' <= c <= u'\u9fff' for c in text):  # 检测中文
                language = "zh-cn"
            else:
                language = "en"
            print(f"选择的语言: {language}")
        
        # 生成语音
        print(f"正在生成语音...")
        tts.tts_to_file(
            text=text, 
            file_path=output_path,
            speaker=speaker, 
            language=language
        )
        
        # 显示成功信息
        abs_path = os.path.abspath(output_path)
        print(f"语音已生成并保存到: {abs_path}")
        
        # 播放生成的音频
        if play:
            print("正在播放音频...")
            subprocess.run(["afplay", abs_path])
            
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    # 英文示例
    english_text = "This is a test. TTS can generate natural and fluent speech."
    text_to_speech(english_text, "english_output.wav", "tts_models/en/ljspeech/tacotron2-DDC")
    
    # 留出一点间隔
    time.sleep(1)
    
    # 中文示例
    chinese_text = "这是一个测试。TTS可以生成自然流畅的语音。"
    text_to_speech(chinese_text, "chinese_output.wav", "tts_models/multilingual/multi-dataset/xtts_v2")