# TTS 语音合成微服务

这是一个基于Coqui TTS的语音合成微服务系统，支持英文和中文文本转语音。

## 特点

- 服务端-客户端架构，避免每次合成语音时重新加载模型
- 支持多种TTS模型，包括Tacotron2和XTTS v2
- 支持中文和英文文本转语音
- 自动模型选择 - 检测到中文时自动切换到多语言模型
- 预加载常用模型，加快响应速度

## 安装依赖

```bash
pip install flask requests TTS
```

对于Windows系统播放音频需要安装：
```bash
pip install playsound
```

## 使用方法

### 1. 启动服务端

首先，启动TTS服务端：

```bash
python tts_server.py
```

这将在本地启动一个TTS服务，监听端口5000。首次启动时，服务会下载并加载所需的TTS模型，可能需要一些时间。

### 2. 使用客户端生成语音

在另一个终端或脚本中，使用客户端生成语音：

```python
from tts_client import text_to_speech

# 英文示例
text_to_speech("Hello, this is a test.", "output_en.wav")

# 中文示例
text_to_speech("这是一个中文测试。", "output_zh.wav")
```

也可以直接运行客户端脚本查看示例：

```bash
python tts_client.py
```

## API参考

### 客户端API

`text_to_speech` 函数接受以下参数：

- `text` (str): 要转换的文本
- `output_path` (str, optional): 输出音频文件的路径，如果不指定则使用临时文件
- `model_name` (str): 要使用的TTS模型名称
- `language` (str, optional): 使用的语言，如果为None则自动检测
- `play` (bool): 是否立即播放生成的音频

### 服务端API

服务端提供以下REST API端点：

- `POST /tts`: 将文本转换为语音
  - 请求体: `{"text": "要转换的文本", "model_name": "模型名称", "language": "语言"}`
  - 响应: 音频文件 (WAV格式)

- `GET /models`: 获取已加载的模型列表
  - 响应: `{"loaded_models": ["模型1", "模型2"], "reference_audio": "参考音频路径"}`

- `GET /health`: 健康检查端点
  - 响应: `{"status": "running"}`

## 常见问题

1. **服务启动失败或模型加载错误**
   - 确保已安装所有依赖包
   - 检查网络连接是否正常，模型需要从网络下载

2. **中文语音合成失败**
   - 确保XTTS v2模型加载成功
   - 检查是否有可用的参考音频

3. **音频播放失败**
   - 对于Windows系统，确保已安装`playsound`库
   - 检查系统是否有可用的音频输出设备

## 支持的模型

以下是一些常用的TTS模型：

- 英文模型: `tts_models/en/ljspeech/tacotron2-DDC`
- 多语言模型: `tts_models/multilingual/multi-dataset/xtts_v2`

更多模型可在Coqui TTS文档中找到。 