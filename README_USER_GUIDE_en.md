# User Guide for Coqui TTS System

<div align="right">
  <a href="README_USER_GUIDE.md">中文</a> | <a href="README_USER_GUIDE_en.md">English</a>
</div>

## Table of Contents

1. [Introduction](#introduction)
2. [Project Background](#project-background)
3. [System Architecture](#system-architecture)
4. [Installation Guide](#installation-guide)
   - [Obtaining Project Files](#obtaining-project-files)
   - [Installing Dependencies](#installing-dependencies)
5. [Usage Instructions](#usage-instructions)
   - [Starting the System](#starting-the-system)
   - [Using the Hotkey Feature](#using-the-hotkey-feature)
   - [Voice Custom Settings](#voice-custom-settings)
6. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
   - [VPN-Related Issues](#vpn-related-issues)
7. [Additional Information](#additional-information)

## Introduction

This guide provides comprehensive instructions for the installation, configuration, and usage of the Coqui TTS system. This text-to-speech application is designed to convert clipboard text into speech with a simple hotkey, offering a convenient and efficient solution for text-to-speech needs.

## Project Background

This project is based on [Coqui TTS](https://github.com/coqui-ai/TTS), an open-source text-to-speech library. Our system improves upon the original by:

1. **Adding hotkey functionality**: Enables one-click conversion of clipboard text to speech
2. **Creating a standalone mode**: Provides operation without a separate server process
3. **Automatic language detection**: Automatically selects the appropriate model based on text content
4. **Incorporating fallback strategies**: Includes system TTS fallback when models fail
5. **Optimizing for macOS**: Special adaptations for macOS operation

## System Architecture

The system offers two operational modes:

### Microservice Architecture
- **TTS Server**: Handles text-to-speech conversion tasks
- **Client Application**: Captures hotkeys and sends clipboard content to the server
- **Advantage**: Faster response after initial load because the model stays loaded in the server

### Standalone Architecture
- Single application that combines hotkey functionality and TTS processing
- Recommended for environments with VPN or network restrictions
- Loads models at startup, then quickly processes requests

## Installation Guide

### Obtaining Project Files

#### Method 1: Using Git Clone

```bash
# Clone the repository
git clone https://github.com/yourusername/coqui-tts-system.git

# Navigate to the project directory
cd coqui-tts-system
```

#### Method 2: Direct Download

1. Visit the [GitHub repository](https://github.com/yourusername/coqui-tts-system)
2. Click the "Code" button
3. Select "Download ZIP"
4. Extract the downloaded ZIP file

### Installing Dependencies

#### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

#### Setting Up a Virtual Environment

```bash
# Create a virtual environment
python -m venv tts_env

# Activate the virtual environment
# On Windows
tts_env\Scripts\activate
# On macOS/Linux
source tts_env/bin/activate
```

#### Installing Required Packages

```bash
# Install dependencies
pip install -r requirements.txt
```

This will install all necessary packages, including:
- TTS (Coqui TTS library)
- pynput (for hotkey handling)
- PyAudio (for audio output)
- requests (for client-server communication)

## Usage Instructions

### Starting the System

#### Standalone Mode (Recommended)

```bash
# Make the startup script executable (macOS/Linux)
chmod +x run_standalone.sh

# Run the standalone application
./run_standalone.sh
```

#### Microservice Mode

Terminal 1 (Server):
```bash
# Make the server startup script executable (macOS/Linux)
chmod +x run_server.sh

# Start the TTS server
./run_server.sh
```

Terminal 2 (Client):
```bash
# Make the client startup script executable (macOS/Linux)
chmod +x run_client.sh

# Start the client application
./run_client.sh
```

### Using the Hotkey Feature

1. Copy text from any application
2. Press the hotkey combination `ctrl+option+cmd+p` (on macOS) or `ctrl+alt+win+p` (on Windows)
3. The system will automatically detect the language and read the text aloud

### Voice Custom Settings

You can customize voice settings in the configuration file:

```bash
# Open the configuration file
nano config.ini
```

Configurable options include:
- `voice_speed`: Adjust speech rate (default: 1.0)
- `voice_pitch`: Adjust voice pitch (default: 1.0)
- `model_selection`: Choose preferred models for different languages
- `hotkey_combination`: Customize the hotkey combination

## Troubleshooting

### Common Issues

#### Problem: System doesn't respond to hotkey

**Possible causes and solutions:**
1. **Another application is capturing the hotkey**: Try changing the hotkey combination in config.ini
2. **Application doesn't have accessibility permissions**: On macOS, grant accessibility permissions in System Preferences
3. **Virtual environment not activated**: Ensure you've activated the virtual environment before starting

#### Problem: Audio quality issues

**Possible causes and solutions:**
1. **System audio settings**: Check your system's audio output settings
2. **Model quality**: Try using a higher-quality model by changing the settings in config.ini
3. **Text format issues**: Some special characters or formatting might affect speech quality

### VPN-Related Issues

If you're experiencing connection issues while using a VPN, please refer to the separate troubleshooting document: [VPN Issue Resolution](vpn_issue_resolution_en.md).

## Additional Information

### Log Files

Log files are stored in the `logs` directory and can be helpful for diagnosing issues:
- `server.log`: Contains server process logs
- `client.log`: Contains client process logs
- `standalone.log`: Contains standalone application logs

### Model Information

The system uses these TTS models:
- **English**: `tts_models/en/ljspeech/tacotron2-DDC`
- **Multilingual**: `tts_models/multilingual/multi-dataset/xtts_v2`

Models are downloaded automatically on first use.

### Memory Requirements

- Server mode: Approximately 2GB RAM
- Standalone mode: Approximately 4GB RAM

### Updating

To update the system to the latest version:

```bash
# Pull the latest changes
git pull

# Update dependencies
pip install -r requirements.txt
```

### Support

For additional assistance, please:
- Check the [project wiki](https://github.com/yourusername/coqui-tts-system/wiki)
- Open an issue on the [GitHub Issues page](https://github.com/yourusername/coqui-tts-system/issues)
- Contact the development team at example@email.com 