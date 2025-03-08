from TTS.api import TTS
import os
import subprocess
import time
import torch
import importlib
from functools import wraps

# 添加安全的全局类
def add_safe_globals_for_xtts():
    try:
        # 尝试导入所有需要的XTTS配置类
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import XttsAudioConfig
        
        # 添加到PyTorch安全全局列表
        safe_classes = [XttsConfig, XttsAudioConfig]
        torch.serialization.add_safe_globals(safe_classes)
        print(f"已添加XTTS相关类到安全全局列表: {[cls.__name__ for cls in safe_classes]}")
    except ImportError as e:
        print(f"无法导入XTTS相关类，可能会影响XTTS模型加载: {e}")
    except AttributeError:
        # 较旧版本的PyTorch可能没有add_safe_globals
        print("当前PyTorch版本不支持add_safe_globals，将使用替代方法")

# 修补torch.load函数
original_torch_load = torch.load

@wraps(original_torch_load)
def patched_torch_load(f, map_location=None, pickle_module=None, **kwargs):
    try:
        # 首先尝试使用默认设置加载
        return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, **kwargs)
    except Exception as e:
        print(f"使用默认设置加载模型失败，尝试使用weights_only=False: {str(e)}")
        try:
            # 如果失败，尝试使用weights_only=False
            return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, weights_only=False, **kwargs)
        except Exception as e2:
            # 如果仍然失败，打印详细错误并重新抛出
            print(f"使用weights_only=False加载模型也失败: {str(e2)}")
            # 尝试使用TTS库自己的加载方法
            try:
                from TTS.utils.io import load_checkpoint
                print("尝试使用TTS库的load_checkpoint方法...")
                return load_checkpoint(f, map_location=map_location)
            except Exception as e3:
                print(f"所有加载方法都失败: {str(e3)}")
                raise e3

# 替换torch.load函数
torch.load = patched_torch_load

# 添加安全全局类
add_safe_globals_for_xtts()

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
        
        # 安全地检查是否是多发言人模型
        if hasattr(tts, 'is_multi_speaker') and tts.is_multi_speaker:
            # 安全地检查speakers属性是否存在
            if hasattr(tts, 'speakers') and tts.speakers:
                print(f"可用的发音人: {tts.speakers}")
                speaker = tts.speakers[0]  # 使用第一个发音人
            else:
                print("模型支持多发言人，但未找到发言人列表")
        
        # 安全地检查是否是多语言模型
        if hasattr(tts, 'is_multi_lingual') and tts.is_multi_lingual:
            if hasattr(tts, 'languages') and tts.languages:
                print(f"可用的语言: {tts.languages}")
                # 根据文本自动选择语言
                if any(u'\u4e00' <= c <= u'\u9fff' for c in text):  # 检测中文
                    language = "zh-cn"
                else:
                    language = "en"
                print(f"选择的语言: {language}")
            else:
                print("模型支持多语言，但未找到语言列表")
        
        # 生成语音
        print(f"正在生成语音...")
        # 只在属性存在时传递参数
        tts_params = {"text": text, "file_path": output_path}
        if speaker is not None:
            tts_params["speaker"] = speaker
        if language is not None:
            tts_params["language"] = language
            
        tts.tts_to_file(**tts_params)
        
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