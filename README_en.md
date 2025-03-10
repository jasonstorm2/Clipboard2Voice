# Coqui TTS Hotkey System

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

A convenient text-to-speech system built on Coqui TTS, featuring clipboard-to-speech capability with a simple hotkey.

## 🚀 Quick Start

### Standalone Mode (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the standalone application
./run_standalone.sh
```

Copy any text and press `Ctrl+Option+Cmd+P` (macOS) or `Ctrl+Alt+Win+P` (Windows) to hear it spoken aloud!

## ✨ Features

- **One-Key Text-to-Speech**: Convert clipboard text to speech with a single hotkey
- **Multiple Languages**: Automatic detection and processing of both English and Chinese text
- **Dual Architecture**: Choose between standalone mode or client-server architecture
- **Optimized for macOS**: Special accommodations for macOS environments
- **VPN Compatible**: Standalone mode works perfectly even with VPN enabled

## 📖 Documentation

- [Detailed User Guide](README_USER_GUIDE_en.md) - Complete setup and usage instructions
- [Project Structure](docs/project_structure_en.md) - Technical overview of system components
- [VPN Issue Resolution](vpn_issue_resolution_en.md) - Solutions for VPN-related connection problems

## 🛠️ System Requirements

- **Operating System**: macOS (primary), Windows (supported), Linux (limited support)
- **Python**: 3.8 or higher
- **Memory**: 2GB+ (server mode), 4GB+ (standalone mode)
- **Disk Space**: ~1GB (for model storage)

## 📦 Architecture

The system offers two operational modes:

### Microservice Architecture
The system is divided into two components:
- **TTS Server**: Handles text-to-speech conversion
- **Client Application**: Captures hotkeys and sends text to server

### Standalone Architecture
Combines both components into a single application for environments where network connections might be problematic (e.g., when using VPNs).

## 📋 Installation

### Prerequisites

```bash
# Create a virtual environment
python -m venv tts_env

# Activate the virtual environment
source tts_env/bin/activate  # Linux/macOS
tts_env\Scripts\activate     # Windows
```

### Installation Command

```bash
# Install required packages
pip install -r requirements.txt
```

## 🚀 Starting the System

### Standalone Mode

```bash
# Run the standalone application
./run_standalone.sh
```

### Client-Server Mode

Terminal 1:
```bash
# Start the TTS server
./run_server.sh
```

Terminal 2:
```bash
# Start the client application
./run_client.sh
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Coqui AI](https://github.com/coqui-ai) for their excellent TTS library
- All contributors to the open-source libraries used in this project 