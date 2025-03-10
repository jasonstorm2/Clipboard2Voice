# Project Structure and Component Description

This document provides detailed information about the code structure, component functions, and their relationships in the Text Reading Assistant project, helping developers and advanced users understand the project architecture.

## Table of Contents

- [File Structure Overview](#file-structure-overview)
- [Core Components](#core-components)
  - [Server Components](#server-components)
  - [Client Components](#client-components)
  - [Standalone Application Components](#standalone-application-components)
  - [Diagnostic and Tool Components](#diagnostic-and-tool-components)
- [Startup Scripts](#startup-scripts)
- [Data Flow Description](#data-flow-description)
- [Architecture Diagrams](#architecture-diagrams)
- [Dependencies](#dependencies)

## File Structure Overview

```
coqui_tts_system/
├── server/                  # TTS server components
│   ├── tts_server.py        # Main server application
│   ├── models/              # Pre-trained TTS models
│   ├── utils/               # Server utilities
│   └── audio_cache/         # Generated audio cache
├── client/                  # Client application components
│   ├── tts_client.py        # Main client application
│   ├── hotkey_listener.py   # Hotkey detection module
│   └── clipboard_reader.py  # Clipboard access utilities
├── standalone/              # Standalone application
│   ├── standalone_tts.py    # Combined functionality
│   └── fallback_handler.py  # Error handling mechanisms
├── scripts/                 # Startup and utility scripts
│   ├── run_server.sh        # Server startup script
│   ├── run_client.sh        # Client startup script
│   └── run_standalone.sh    # Standalone mode startup
├── docs/                    # Documentation
│   ├── project_structure.md # This document
│   └── api_reference.md     # API documentation
├── diagnostics/             # Diagnostic tools
│   ├── debug_vpn_connection.py # VPN connection diagnostic
│   ├── direct_tts_client.py    # Raw socket client
│   └── test_models.py          # Model testing utility
├── logs/                    # Log files directory
├── config.ini               # Configuration file
├── requirements.txt         # Python dependencies
└── README.md                # Project overview
```

## Core Components

The project is divided into four main component categories: server components, client components, standalone application components, and diagnostic tool components.

### Server Components

#### tts_server.py

The server component is the core of the microservice architecture, responsible for loading TTS models and handling text-to-speech requests.

**Main Features**:
- Load and manage TTS models (English and multilingual)
- Provide REST API interface for receiving text-to-speech requests
- Support health checks and model list queries
- Preload common models to improve response speed
- Patch PyTorch loading mechanism to resolve security limitations

**Key Classes**:
- `TTSServer`: Main server class that manages HTTP endpoints and TTS processing
- `ModelManager`: Loads and manages TTS models
- `AudioCache`: Caches generated audio to improve performance for repeated phrases

**API Endpoints**:
- `/tts` - POST endpoint for text-to-speech conversion
- `/health` - GET endpoint for server health checks
- `/models` - GET endpoint to list available models

### Client Components

#### tts_client.py

The client library provides interfaces for communicating with the TTS server, which can be used independently or called by other components.

**Main Features**:
- Send text to the server and receive audio responses
- Play generated audio
- Provide command-line interface for direct use

**Key Classes**:
- `TTSClient`: Main client class that connects to the server
- `HotkeyListener`: Detects and processes hotkey combinations
- `ClipboardReader`: Accesses clipboard content

#### hotkey_listener.py

Standard hotkey listener that monitors specific hotkey combinations and calls the TTS client.

**Main Features**:
- Listen for global hotkey combinations (default: `ctrl+option+cmd+p`)
- Read clipboard content
- Convert text to speech through the TTS client

**Key Classes**:
- `ClipboardTTSHotkey`: Hotkey listening and processing class

#### vpn_compatible_tts.py

VPN-compatible hotkey listener, extending the standard version to resolve connection issues in VPN environments.

**Main Features**:
- Try multiple server connection methods
- Automatic retry mechanism
- Support for directly specifying server URL
- Other hotkey listening functions same as the standard version

**Key Classes**:
- `VPNCompatibleTTSHotkey`: Enhanced hotkey listening and processing class

### Standalone Application Components

#### standalone_tts.py

The standalone application component integrates all functionality into a single independent program that does not depend on network connections.

**Main Features**:
- Load TTS models locally
- Listen for hotkey combinations
- Read clipboard content and convert to speech locally
- Provide system TTS as a fallback mechanism

**Key Classes**:
- `StandaloneTTS`: Main class that combines TTS and hotkey functionality
- `FallbackHandler`: Provides fallback mechanisms when primary TTS fails
- `LanguageDetector`: Detects text language for model selection

### Diagnostic and Tool Components

#### debug_vpn_connection.py

VPN connection diagnostic tool for troubleshooting and resolving connection issues in VPN environments.

**Main Features**:
- Collect network information
- Test different connection methods
- Distinguish between network layer and application layer issues
- Provide troubleshooting suggestions

**Key Functions**:
- `test_socket_connection`: Test basic socket connections
- `test_http_connection`: Test HTTP connections and API responses

#### direct_tts_client.py

Direct TCP connection client, attempting to bypass the HTTP layer to connect directly to the server.

**Main Features**:
- Use raw TCP sockets to connect to the server
- Send request data in JSON format
- Provide command-line interface for connection testing

**Key Functions**:
- `text_to_speech_direct`: Send TTS requests directly via TCP connection

## Startup Scripts

The project includes multiple Shell scripts to simplify the startup process for different components:

| Script | Purpose | Example Command |
|--------|---------|----------------|
| `run_server.sh` | Starts the TTS server | `./run_server.sh` |
| `run_client.sh` | Starts the client application | `./run_client.sh` |
| `run_standalone.sh` | Starts the standalone application | `./run_standalone.sh` |
| `install_dependencies.sh` | Installs required packages | `./install_dependencies.sh` |
| `test_connection.sh` | Tests server connectivity | `./test_connection.sh` |

The main purpose of these scripts is to provide a user-friendly way to start components while displaying necessary prompts before startup.

## Data Flow Description

### Microservice Architecture Data Flow

```
+----------------+        +----------------+        +----------------+
|                |        |                |        |                |
|  Hotkey Press  |------->|  Clipboard     |------->|  Client App    |
|                |        |  Content       |        |                |
+----------------+        +----------------+        +-------+--------+
                                                           |
                                                           | HTTP Request
                                                           v
+----------------+        +----------------+        +----------------+
|                |        |                |        |                |
|  Audio Output  |<-------|  Audio         |<-------|  TTS Server    |
|                |        |  Processing    |        |                |
+----------------+        +----------------+        +----------------+
```

1. User presses the configured hotkey
2. Client application reads the clipboard content
3. Client sends a request to the TTS server with the text
4. Server processes the text and generates audio
5. Audio is returned to the client and played back

### Standalone Architecture Data Flow

```
+----------------+        +----------------+        +----------------+
|                |        |                |        |                |
|  Hotkey Press  |------->|  Clipboard     |------->|  TTS           |
|                |        |  Content       |        |  Processing    |
+----------------+        +----------------+        +-------+--------+
                                                           |
                                                           | Internal Process
                                                           v
                          +----------------+        +----------------+
                          |                |        |                |
                          |  Audio Output  |<-------|  Audio         |
                          |                |        |  Generation    |
                          +----------------+        +----------------+
```

1. User presses the configured hotkey
2. Standalone application reads the clipboard content
3. Text is processed internally within the same process
4. Audio is generated and played back

## Architecture Diagrams

### Microservice Architecture

```
+------------------------------------------+
|                                          |
|  +----------------+  +----------------+  |
|  |                |  |                |  |
|  |  TTS Server    |  |  Client App    |  |
|  |                |  |                |  |
|  +-------+--------+  +-------+--------+  |
|          ^                   |           |
|          |                   |           |
|          |    HTTP API       |           |
|          +-------------------+           |
|                                          |
+------------------------------------------+
```

### VPN-Compatible Architecture

```
┌─────────────────────┐     ┌─────────────┐     ┌─────────────┐
│ VPN-Compatible      │     │ TTS Client  │     │ TTS Server  │
│ Hotkey Listener     │────▶│             │────▶│             │
│ vpn_compatible_tts.py│    │ tts_client.py│    │ tts_server.py│
└─────────────────────┘     └─────────────┘     └─────────────┘
          │                                            │
          │                                            ▼
          │                                      ┌─────────────┐
          └──────────────────────────────────┐  │ TTS Models  │
                      (Multiple Connection    │  │ (Coqui TTS) │
                       Attempts)             └─▶└─────────────┘
```

### Standalone Application Architecture

```
┌─────────────────────────────────────────┐
│ Standalone TTS App (standalone_tts.py)  │
│                                         │
│  ┌─────────────┐      ┌─────────────┐   │
│  │ Hotkey      │      │ Local TTS   │   │
│  │ Listener    │─────▶│ Model       │   │
│  │ Component   │      │ Processing  │   │
│  └─────────────┘      └─────────────┘   │
└─────────────────────────────────────────┘
```

## Dependencies

The project's main dependencies are as follows:

### External Dependencies

- **TTS**: Coqui TTS library, providing core text-to-speech functionality
- **Flask**: Web framework for creating microservice APIs
- **requests**: HTTP client library for sending requests
- **pynput/keyboard**: Hotkey listening libraries for capturing global hotkeys
- **pyperclip**: Clipboard access library for reading clipboard content
- **torch**: PyTorch deep learning library, the foundation for TTS models
- **sounddevice**: Audio playback library

### Internal Dependencies

- `hotkey_tts.py` → `tts_client.py`: Hotkey listener depends on TTS client
- `vpn_compatible_tts.py` → `tts_client.py`: VPN-compatible version depends on TTS client
- `standalone_tts.py` → `TTS API`: Standalone application directly depends on TTS library
- `direct_tts_client.py` → No internal dependencies, using socket communication directly

All components share the same hotkey listening logic and TTS parameter processing logic but employ different strategies for network connection and model loading. 