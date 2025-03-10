# TTS System Troubleshooting and Resolution in VPN Environments

<div align="right">
  <a href="vpn_issue_resolution.md">中文</a> | <a href="vpn_issue_resolution_en.md">English</a>
</div>

## 1. Problem Background

When developing a text-to-speech system based on Coqui TTS, we initially designed a microservice architecture that encapsulated TTS functionality as a server, accessed through a hotkey listener client. This architecture avoided the need to reload the model each time speech was generated, significantly improving response speed.

**However, when VPN was enabled, connection issues emerged**:
- The client could not connect to the local TTS server
- Error messages indicated connection refusal or timeout
- The problem persisted even when changing the server address from `localhost` to `127.0.0.1`

## 2. Diagnostic Process

### 2.1 Network Connection Check

First, we verified that the TTS server was running and listening on the port:

```bash
$ netstat -ant | grep 8090
tcp4       0      0  *.8090                 *.*                    LISTEN
```

The result confirmed that the server was indeed listening on port 8090, eliminating the possibility that the service was not running.

### 2.2 Creating Diagnostic Tools

Next, we developed a specialized diagnostic tool `debug_vpn_connection.py` to:
- Collect network information, including hostname and IP address
- Test various possible connection methods (different hostnames and IP addresses)
- Distinguish between socket connection and HTTP connection issues
- Provide detailed diagnostic output

Core code example:

```python
def test_socket_connection(host: str, port: int, timeout: int = 2) -> bool:
    """Test raw socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"  Socket connection test failed: {e}")
        return False

def test_http_connection(url: str, timeout: int = 2) -> Dict:
    """Test HTTP connection"""
    result = {
        "url": url,
        "socket_ok": False,
        "http_ok": False,
        "health_ok": False,
        "error": None,
        "status_code": None,
        "response": None,
        "time_ms": 0
    }
    
    # Extract hostname and port from URL
    try:
        host = url.replace("http://", "").replace("https://", "").split("/")[0]
        if ":" in host:
            host, port_str = host.split(":")
            port = int(port_str)
        else:
            port = 80 if url.startswith("http://") else 443
            
        # Test socket connection
        result["socket_ok"] = test_socket_connection(host, port, timeout)
        
        if not result["socket_ok"]:
            result["error"] = "Socket connection failed"
            return result
            
        # Test HTTP connection
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        result["time_ms"] = round((end_time - start_time) * 1000)
        result["status_code"] = response.status_code
        result["http_ok"] = 200 <= response.status_code < 300
        
        # Check response content
        # ...
```

### 2.3 Diagnostic Results Analysis

Running the diagnostic tool revealed the following conditions:
- **Socket connection successful**: Socket connections to `localhost:8090`, `127.0.0.1:8090`, and actual IP were all successful
- **HTTP connection failed**: All attempted HTTP connections returned `502 Bad Gateway` errors
- **IPv6 connection**: Connection to `[::1]:8090` failed completely

Output example:
```
Testing http://localhost:8090/health...
  ✓ Socket connection successful
  ✗ HTTP request failed (status code: 502)
  ✗ Health check failed

Testing http://127.0.0.1:8090/health...
  ✓ Socket connection successful
  ✗ HTTP request failed (status code: 502)
  ✗ Health check failed
```

This indicated that the network layer was working, but there was a problem at the HTTP layer, possibly due to VPN software interfering with HTTP requests or modifying HTTP proxy settings.

### 2.4 Bypassing the HTTP Layer

To confirm whether it was an HTTP layer issue, we developed `direct_tts_client.py` to attempt connecting to the server via raw TCP sockets, but this method also failed. This suggested that the VPN interference might be deeper than expected.

## 3. Attempted Solutions

We tried several solutions:

### 3.1 VPN-Compatible Client (`vpn_compatible_tts.py`)

Developed a client capable of automatically trying multiple connection methods:
- Attempting various local addresses: `localhost`, `127.0.0.1`, `0.0.0.0`, etc.
- Adding connection retry mechanisms
- Supporting direct server URL specification
- Providing more detailed error information

Example code:

```python
def _get_potential_server_urls(self) -> List[str]:
    """Get potential server URL list"""
    port = self.server_port
    urls = []
    
    # Add common local hostnames and IPs
    urls.append(f"http://localhost:{port}")
    urls.append(f"http://127.0.0.1:{port}")
    urls.append(f"http://0.0.0.0:{port}")
    
    # Add IPv6 loopback address
    urls.append(f"http://[::1]:{port}")
    
    # Try to get local machine IP address (non-loopback)
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip != "127.0.0.1":
            urls.append(f"http://{ip}:{port}")
            urls.append(f"http://{hostname}:{port}")
    except Exception as e:
        print(f"Error getting local IP address: {e}")
    
    return urls
```

### 3.2 Direct TCP Connection (`direct_tts_client.py`)

Tried to bypass the HTTP layer by directly communicating with the server using TCP sockets:
- Custom protocol format
- Sending requests in JSON format
- Manually managing connections and responses

Key code:

```python
def text_to_speech_direct(
    text: str, 
    output_path: Optional[str] = None,
    host: str = DEFAULT_HOST, 
    port: int = DEFAULT_PORT
) -> Optional[str]:
    """Convert text to speech directly via TCP connection"""
    # ...
    
    try:
        # Prepare request data
        request_data = {
            "text": text,
            "output_path": output_path,
            "model_name": "tts_models/multilingual/multi-dataset/xtts_v2" if any(u'\u4e00' <= c <= u'\u9fff' for c in text) else "tts_models/en/ljspeech/tacotron2-DDC"
        }
        
        # Serialize to JSON
        json_data = json.dumps(request_data)
        
        # Connect to server
        print(f"Connecting to server {host}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            
            # Send request
            print("Sending text...")
            sock.sendall(json_data.encode('utf-8'))
            
            # Receive response
            print("Waiting for response...")
            response = sock.recv(1024).decode('utf-8')
        
        # ...
```

### 3.3 Standalone Solution (`standalone_tts.py`)

Completely abandoned the client-server architecture, developing a local TTS solution that doesn't depend on network connections:
- Integrated TTS functionality directly into the hotkey listener
- Loaded and ran TTS models locally
- Added system TTS as a fallback mechanism

## 4. Final Solution

Ultimately, we successfully implemented a standalone TTS solution that doesn't rely on network connections:

### 4.1 Technical Architecture

The new solution adopts a single-process architecture:
- Loads TTS models directly at startup
- Monitors specified hotkey combinations
- Reads clipboard content
- Generates speech output locally
- Requires no network communication

### 4.2 Core Components

1. **Model Management**:
   - Preloads English and multilingual TTS models
   - Patches PyTorch loading mechanism to resolve security limitations
   - Prepares reference audio for multilingual models

   ```python
   def _initialize_tts(self):
       """Initialize TTS model"""
       logger.info("Initializing TTS model...")
       
       try:
           # Preload support modules
           import torch
           
           # Patch torch.load function
           original_torch_load = torch.load
           
           def patched_torch_load(f, map_location=None, pickle_module=None, **kwargs):
               try:
                   # First try with default settings
                   return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, **kwargs)
               except Exception as e:
                   logger.warning(f"Failed to load model with default settings, trying with weights_only=False: {str(e)}")
                   try:
                       # If it fails, try with weights_only=False
                       return original_torch_load(f, map_location=map_location, pickle_module=pickle_module, weights_only=False, **kwargs)
                   except Exception as e2:
                       logger.error(f"All loading methods failed: {str(e2)}")
                       raise e2
           
           # Replace torch.load function
           torch.load = patched_torch_load
           
           # Import TTS
           from TTS.api import TTS
           
           # Create English model instance
           logger.info("Loading English TTS model...")
           self.en_tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
           
           # Create multilingual model instance
           logger.info("Loading multilingual TTS model...")
           self.ml_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
           
           # Prepare reference audio
           self._prepare_reference_audio()
   ```

2. **Hotkey Listening**:
   - Uses pynput library, providing more reliable macOS hotkey handling
   - Supports complex hotkey combinations (`ctrl+option+cmd+p`)
   - Prevents concurrent processing, ensuring only one request is processed at a time

   ```python
   def _on_pynput_press(self, key):
       """pynput key press callback function"""
       try:
           # Add key to the set of currently pressed keys
           self.current_keys.add(key)
           
           # Check if all hotkey keys are pressed
           if (self.ctrl_key in self.current_keys and 
               self.option_key in self.current_keys and 
               self.cmd_key in self.current_keys and 
               self.p_key in self.current_keys):
               self._handle_hotkey()
       except Exception as e:
           logger.error(f"Error processing key press event: {e}")
   ```

3. **Text Processing**:
   - Automatically detects Chinese text
   - Selects appropriate model based on content
   - Supports custom language selection

4. **Error Handling**:
   - Multi-level fallback mechanism
   - Uses system TTS when model loading fails
   - Detailed logging

   ```python
   def _fallback_tts(self, text: str) -> None:
       """Use system TTS as fallback"""
       try:
           logger.info("Using system TTS as fallback...")
           
           if SYSTEM == "Darwin":  # macOS
               subprocess.run(["say", text])
               logger.info("System TTS playback complete")
               return True
           elif SYSTEM == "Windows":
               try:
                   import pyttsx3
                   engine = pyttsx3.init()
                   engine.say(text)
                   engine.runAndWait()
                   logger.info("System TTS playback complete")
                   return True
               except:
                   logger.error("Windows system TTS failed")
                   return False
           else:  # Linux
               try:
                   subprocess.run(["espeak", text])
                   logger.info("System TTS playback complete")
                   return True
               except:
                   logger.error("Linux system TTS failed")
                   return False
       except Exception as e:
           logger.error(f"System TTS failed: {e}")
           return False
   ```

### 4.3 Usage

Using it is very simple, just run the startup script:

```bash
./run_standalone.sh
```

Then:
1. Copy text in any application
2. Press the hotkey combination `ctrl+option+cmd+p`
3. The system will automatically read the clipboard content

## 5. Why This Solution Works

The standalone TTS solution works for these reasons:

1. **Completely avoids network** - Doesn't rely on any network connections, so VPN cannot interfere
2. **Single process** - Eliminates issues that might arise from inter-process communication
3. **Local resources** - All needed resources are local, reducing external dependencies
4. **Multi-level fallback** - Even if the primary model fails, the system can still use system TTS
5. **macOS optimization** - Specially optimized hotkey handling for macOS environment

## 6. Comparison with Original Microservice Approach

| Feature | Microservice Architecture | Standalone Solution |
|---------|--------------------------|---------------------|
| **Startup Speed** | Server starts slowly, client starts quickly | First startup slow, subsequent startups slow |
| **Response Speed** | Fast (server preloads models) | Fast (models already loaded locally) |
| **Resource Usage** | Server and client each use a portion | Single process uses more |
| **VPN Compatibility** | Poor (easily affected by VPN) | Good (not affected by VPN) |
| **Scalability** | Good (can support multiple clients) | Poor (single-user design) |
| **Fault Tolerance** | Medium (server crash affects all clients) | Good (has multi-level fallback mechanisms) |
| **Deployment Complexity** | High (needs to manage server and client) | Low (single executable file) |

## 7. Summary and Lessons Learned

### 7.1 Key Lessons

1. **VPN interaction with local network is complex** - VPN can affect local network connections that should work
2. **Layered diagnosis is important** - Distinguish between network layer, transport layer, and application layer issues
3. **Value of multiple solutions** - When one approach fails, a completely different architecture may succeed
4. **Fallback strategies are essential** - Systems should have multi-level fallback mechanisms

### 7.2 Technical Notes

1. When dealing with network issues, start testing from the lowest layer (sockets)
2. On macOS, the pynput library is more reliable for hotkey handling than the keyboard library
3. For VPN environments, consider reducing or eliminating network dependencies
4. Use threads to handle long-running tasks, avoiding blocking the main UI thread
5. Provide reference audio for TTS models to ensure multilingual models work properly

### 7.3 Final Recommendations

For applications that need to run in VPN environments, especially those involving local services:
- Prioritize single-process architecture
- If microservices must be used, provide a network-independent fallback mode
- Log network configuration and diagnostic information in detail
- Consider VPN split tunneling configuration, allowing local traffic to bypass VPN

This case demonstrates that when facing complex network issues, completely changing the architecture is sometimes more effective than trying to fix the existing architecture. 