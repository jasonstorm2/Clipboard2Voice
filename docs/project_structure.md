# 项目结构与组件说明

<div align="right">
  <a href="project_structure.md">中文</a> | <a href="project_structure_en.md">English</a>
</div>

本文档详细介绍了文本朗读助手项目的代码结构、组件功能及其相互关系，帮助开发者和高级用户理解项目架构。

## 目录

- [文件结构概览](#文件结构概览)
- [核心组件](#核心组件)
  - [服务器组件](#服务器组件)
  - [客户端组件](#客户端组件)
  - [独立应用组件](#独立应用组件)
  - [诊断与工具组件](#诊断与工具组件)
- [启动脚本](#启动脚本)
- [数据流说明](#数据流说明)
- [架构图](#架构图)
- [依赖关系](#依赖关系)

## 文件结构概览

```
项目根目录/
│
├── tts_server.py            # TTS服务器主程序
├── tts_client.py            # TTS客户端库与示例程序
├── hotkey_tts.py            # 热键监听器（标准版）
├── vpn_compatible_tts.py    # VPN兼容版热键监听器
├── standalone_tts.py        # 独立版TTS应用
├── debug_vpn_connection.py  # VPN连接诊断工具
├── direct_tts_client.py     # 直接TCP连接客户端
│
├── run_server.sh            # 启动服务器脚本
├── run_client.sh            # 运行客户端示例脚本
├── run_hotkey_mac.sh        # 启动macOS热键监听脚本
├── run_standalone.sh        # 启动独立应用脚本  
├── run_vpn_tts.sh           # 启动VPN兼容版脚本
│
├── reference_audio.wav      # 多语言模型参考音频
│
├── README.md                # 主项目说明文件
├── README_USER_GUIDE.md     # 详细用户指南
├── vpn_issue_resolution.md  # VPN问题解决文档
│
└── docs/                    # 文档目录
    └── project_structure.md # 本文档
```

## 核心组件

项目分为四个主要组件类别：服务器组件、客户端组件、独立应用组件和诊断工具组件。

### 服务器组件

#### tts_server.py

服务器组件是微服务架构的核心，负责加载TTS模型并处理文本转语音请求。

**主要功能**:
- 加载和管理TTS模型（英文和多语言）
- 提供REST API接口接收文本转语音请求
- 支持健康检查和模型列表查询
- 预加载常用模型以提高响应速度
- 修补PyTorch加载机制以解决安全性限制

**关键类**:
- `TTSModelManager`: 单例模式实现的模型管理器，负责懒加载和缓存TTS模型
- `Flask应用`: 基于Flask框架的Web服务器，提供REST API端点

**API端点**:
- `POST /tts`: 接收文本转语音请求
- `GET /models`: 获取已加载模型列表
- `GET /health`: 健康检查端点

### 客户端组件

#### tts_client.py

客户端库提供了与TTS服务器通信的接口，可以单独使用也可以被其他组件调用。

**主要功能**:
- 发送文本到服务器并接收语音响应
- 播放生成的音频
- 提供命令行接口用于直接使用

**关键类**:
- `TTSClient`: 封装与服务器通信的客户端类
- 便捷函数 `text_to_speech`: 简化使用的高级API

#### hotkey_tts.py

标准版热键监听器，监听特定热键组合并调用TTS客户端。

**主要功能**:
- 监听全局热键组合（默认为`ctrl+option+cmd+p`）
- 读取剪贴板内容
- 通过TTS客户端将文本转换为语音

**关键类**:
- `ClipboardTTSHotkey`: 热键监听与处理类

#### vpn_compatible_tts.py

VPN兼容版热键监听器，扩展了标准版以解决VPN环境下的连接问题。

**主要功能**:
- 尝试多种服务器连接方式
- 自动重试机制
- 支持直接指定服务器URL
- 其他与标准版相同的热键监听功能

**关键类**:
- `VPNCompatibleTTSHotkey`: 增强的热键监听与处理类

### 独立应用组件

#### standalone_tts.py

独立应用组件将所有功能集成到一个独立程序中，不依赖于网络连接。

**主要功能**:
- 本地加载TTS模型
- 监听热键组合
- 读取剪贴板内容并本地转换为语音
- 提供系统TTS作为后备机制

**关键类**:
- `StandaloneTTSHotkey`: 集成了TTS功能的热键监听类
- 内置的模型加载与初始化函数

### 诊断与工具组件

#### debug_vpn_connection.py

VPN连接诊断工具，用于排查和解决VPN环境下的连接问题。

**主要功能**:
- 收集网络信息
- 测试不同的连接方式
- 区分网络层和应用层问题
- 提供故障排除建议

**关键函数**:
- `test_socket_connection`: 测试基础套接字连接
- `test_http_connection`: 测试HTTP连接和API响应

#### direct_tts_client.py

直接TCP连接客户端，尝试绕过HTTP层直接连接服务器。

**主要功能**:
- 使用原始TCP套接字连接服务器
- 发送JSON格式的请求数据
- 提供命令行接口用于测试连接

**关键函数**:
- `text_to_speech_direct`: 直接通过TCP连接发送TTS请求

## 启动脚本

项目包含多个Shell脚本，用于简化不同组件的启动过程：

| 脚本名称 | 功能描述 | 主要命令 |
|---------|--------|--------|
| `run_server.sh` | 启动TTS服务器 | `python tts_server.py` |
| `run_client.sh` | 运行TTS客户端示例 | `python tts_client.py` |
| `run_hotkey_mac.sh` | 启动macOS专用热键监听器 | `python hotkey_tts.py` |
| `run_standalone.sh` | 启动独立TTS应用 | `python standalone_tts.py` |
| `run_vpn_tts.sh` | 启动VPN兼容版热键监听器 | `python vpn_compatible_tts.py` |

这些脚本的主要目的是提供用户友好的启动方式，同时在启动前显示必要的提示信息。

## 数据流说明

### 微服务架构数据流

```
用户操作 → 热键监听器 → 剪贴板读取 → TTS客户端 → HTTP请求 → 
TTS服务器 → 模型处理 → 生成音频 → 返回客户端 → 播放音频
```

1. 用户复制文本并按下热键组合
2. 热键监听器捕获热键事件并读取剪贴板内容
3. TTS客户端将文本和参数打包为HTTP请求
4. TTS服务器接收请求并选择适当的模型
5. 服务器生成音频并返回客户端
6. 客户端接收音频并播放

### 独立应用数据流

```
用户操作 → 热键监听器 → 剪贴板读取 → 
本地模型处理 → 生成音频 → 播放音频
```

1. 用户复制文本并按下热键组合
2. 热键监听器捕获热键事件并读取剪贴板内容
3. 本地TTS模型处理文本并生成音频
4. 应用直接播放生成的音频

## 架构图

### 微服务架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 热键监听器   │     │ TTS客户端    │     │ TTS服务器    │
│ hotkey_tts.py│────▶│ tts_client.py│────▶│ tts_server.py│
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │ TTS模型      │
                                        │ (Coqui TTS) │
                                        └─────────────┘
```

### VPN兼容架构

```
┌───────────────────┐     ┌─────────────┐     ┌─────────────┐
│ VPN兼容热键监听器   │     │ TTS客户端    │     │ TTS服务器    │
│ vpn_compatible_tts.py│──▶│ tts_client.py│────▶│ tts_server.py│
└───────────────────┘     └─────────────┘     └─────────────┘
       │                                             │
       │                                             ▼
       │                                       ┌─────────────┐
       └───────────────────────────────────┐  │ TTS模型      │
                          (多种连接尝试)     │  │ (Coqui TTS) │
                                           └─▶└─────────────┘
```

### 独立应用架构

```
┌─────────────────────────────────────────┐
│ 独立TTS应用 (standalone_tts.py)           │
│                                         │
│  ┌─────────────┐      ┌─────────────┐   │
│  │ 热键监听器    │      │ 本地TTS模型  │   │
│  │ 组件         │─────▶│ 处理组件     │   │
│  └─────────────┘      └─────────────┘   │
└─────────────────────────────────────────┘
```

## 依赖关系

项目的主要依赖关系如下：

### 外部依赖

- **TTS**: Coqui TTS库，提供文本转语音核心功能
- **Flask**: Web框架，用于创建微服务API
- **requests**: HTTP客户端库，用于发送请求
- **pynput/keyboard**: 热键监听库，用于捕获全局热键
- **pyperclip**: 剪贴板访问库，用于读取剪贴板内容
- **torch**: PyTorch深度学习库，TTS模型的基础

### 内部依赖关系

- `hotkey_tts.py` → `tts_client.py`: 热键监听器依赖TTS客户端
- `vpn_compatible_tts.py` → `tts_client.py`: VPN兼容版依赖TTS客户端
- `standalone_tts.py` → `TTS API`: 独立应用直接依赖TTS库
- `direct_tts_client.py` → 无内部依赖，直接使用套接字通信

所有组件都共享相同的热键监听逻辑和TTS参数处理逻辑，但在网络连接和模型加载方面采用不同的策略。 