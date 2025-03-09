from flask import Flask, request, send_file, jsonify
import os
import torch
import importlib
from functools import wraps
import urllib.request
import tempfile
from threading import Lock
from TTS.api import TTS
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TTS-Server")

# 添加安全的全局类
def add_safe_globals_for_xtts():
    try:
        # 尝试导入所有需要的XTTS配置类
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import XttsAudioConfig
        
        # 添加到PyTorch安全全局列表
        safe_classes = [XttsConfig, XttsAudioConfig]
        torch.serialization.add_safe_globals(safe_classes)
        logger.info(f"已添加XTTS相关类到安全全局列表: {[cls.__name__ for cls in safe_classes]}")
    except ImportError as e:
        logger.error(f"无法导入XTTS相关类，可能会影响XTTS模型加载: {e}")
    except AttributeError:
        # 较旧版本的PyTorch可能没有add_safe_globals
        logger.warning("当前PyTorch版本不支持add_safe_globals，将使用替代方法")

# 修补torch.load函数
original_torch_load = torch.load

@wraps(original_torch_load)
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
            # 如果仍然失败，打印详细错误并重新抛出
            logger.error(f"使用weights_only=False加载模型也失败: {str(e2)}")
            # 尝试使用TTS库自己的加载方法
            try:
                from TTS.utils.io import load_checkpoint
                logger.info("尝试使用TTS库的load_checkpoint方法...")
                return load_checkpoint(f, map_location=map_location)
            except Exception as e3:
                logger.error(f"所有加载方法都失败: {str(e3)}")
                raise e3

# 替换torch.load函数
torch.load = patched_torch_load

# 下载或创建参考音频文件
def ensure_reference_audio(reference_path="reference_audio.wav"):
    """确保参考音频文件存在，如果不存在则下载或创建一个"""
    if os.path.exists(reference_path):
        logger.info(f"参考音频文件已存在: {reference_path}")
        return reference_path
    
    # 尝试从网络下载一个示例参考音频
    try:
        logger.info("参考音频文件不存在，尝试下载...")
        # 使用一个公开的示例音频URL
        url = "https://github.com/coqui-ai/TTS/raw/dev/tests/inputs/audio/ljspeech_1.wav"
        urllib.request.urlretrieve(url, reference_path)
        logger.info(f"成功下载参考音频到: {reference_path}")
        return reference_path
    except Exception as e:
        logger.error(f"下载参考音频失败: {e}")
        
        # 如果下载失败，尝试使用简单的TTS模型创建一个
        try:
            logger.info("尝试使用简单TTS模型创建参考音频...")
            simple_tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            simple_tts.tts_to_file(
                text="This is a reference audio for voice cloning.", 
                file_path=reference_path
            )
            logger.info(f"成功创建参考音频: {reference_path}")
            return reference_path
        except Exception as e2:
            logger.error(f"创建参考音频失败: {e2}")
            return None

# TTS模型管理类 - 单例模式
class TTSModelManager:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TTSModelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # 加载安全类
            add_safe_globals_for_xtts()
            
            # 初始化模型字典
            self.models = {}
            self.reference_audio = ensure_reference_audio("reference_audio.wav")
            self._initialized = True
            logger.info("TTS模型管理器初始化完成")
    
    def get_model(self, model_name):
        """获取指定的TTS模型，如果模型未加载则先加载"""
        if model_name not in self.models:
            logger.info(f"加载TTS模型: {model_name}")
            start_time = time.time()
            try:
                model = TTS(model_name=model_name)
                load_time = time.time() - start_time
                logger.info(f"模型加载完成，耗时: {load_time:.2f}秒")
                self.models[model_name] = model
            except Exception as e:
                logger.error(f"加载模型失败: {e}")
                raise
        return self.models[model_name]
    
    def text_to_speech(self, text, model_name, language=None):
        """将文本转换为语音，返回音频文件路径"""
        try:
            # 获取模型
            tts = self.get_model(model_name)
            
            # 创建临时文件保存音频
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                output_path = temp_file.name
            
            # 设置参数
            speaker = None
            speaker_wav = None
            is_xtts_v2 = "xtts_v2" in model_name
            
            # 处理多发言人模型
            if hasattr(tts, 'is_multi_speaker') and tts.is_multi_speaker:
                if hasattr(tts, 'speakers') and tts.speakers:
                    logger.info(f"使用发音人: {tts.speakers[0]}")
                    speaker = tts.speakers[0]
                elif is_xtts_v2 and self.reference_audio:
                    logger.info(f"使用参考音频: {self.reference_audio}")
                    speaker_wav = self.reference_audio
            
            # 处理多语言模型
            if language is None and hasattr(tts, 'is_multi_lingual') and tts.is_multi_lingual:
                if hasattr(tts, 'languages') and tts.languages:
                    # 根据文本自动选择语言
                    if any(u'\u4e00' <= c <= u'\u9fff' for c in text):  # 检测中文
                        language = "zh-cn"
                    else:
                        language = "en"
                    logger.info(f"自动选择语言: {language}")
            
            # 生成语音
            logger.info(f"正在生成语音...")
            start_time = time.time()
            
            # 准备参数
            tts_params = {"text": text, "file_path": output_path}
            if speaker is not None:
                tts_params["speaker"] = speaker
            if language is not None:
                tts_params["language"] = language
            if speaker_wav is not None:
                tts_params["speaker_wav"] = speaker_wav
                
            # 生成音频
            tts.tts_to_file(**tts_params)
            
            generation_time = time.time() - start_time
            logger.info(f"语音生成完成，耗时: {generation_time:.2f}秒")
            
            return output_path
            
        except Exception as e:
            logger.error(f"生成语音失败: {e}")
            raise

# 创建Flask应用
app = Flask(__name__)
model_manager = TTSModelManager()

@app.route('/tts', methods=['POST'])
def generate_speech():
    """API端点：接收文本并返回生成的语音文件"""
    try:
        # 获取请求参数
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "缺少必需的参数: text"}), 400
            
        text = data.get('text')
        model_name = data.get('model_name', 'tts_models/en/ljspeech/tacotron2-DDC')
        language = data.get('language')
        
        # 根据是否包含中文自动选择模型
        if not language and any(u'\u4e00' <= c <= u'\u9fff' for c in text):
            if "xtts" not in model_name.lower():
                logger.info("检测到中文，自动切换到XTTS模型")
                model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        
        # 生成语音
        output_path = model_manager.text_to_speech(text, model_name, language)
        
        # 返回音频文件
        return send_file(output_path, mimetype='audio/wav', as_attachment=True, 
                         download_name='tts_output.wav')
    
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """API端点：列出已加载的模型"""
    try:
        return jsonify({
            "loaded_models": list(model_manager.models.keys()),
            "reference_audio": model_manager.reference_audio
        })
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "running"})

if __name__ == '__main__':
    # 预加载常用模型
    try:
        # 检查是否跳过预加载
        skip_preload = os.environ.get('SKIP_PRELOAD', '0').lower() in ('1', 'true', 'yes')
        
        if not skip_preload:
            logger.info("预加载常用TTS模型...")
            # 预加载英文模型
            model_manager.get_model("tts_models/en/ljspeech/tacotron2-DDC")
            # 预加载多语言模型
            model_manager.get_model("tts_models/multilingual/multi-dataset/xtts_v2")
            logger.info("模型预加载完成")
        else:
            logger.info("跳过模型预加载（SKIP_PRELOAD=1）")
    except Exception as e:
        logger.error(f"预加载模型失败: {e}")
    
    # 启动服务
    port = int(os.environ.get('PORT', 8090))
    logger.info(f"启动TTS服务，监听端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 