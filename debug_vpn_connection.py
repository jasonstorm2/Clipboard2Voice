#!/usr/bin/env python3
"""
TTS服务器连接诊断工具
用于诊断VPN环境下TTS服务器连接问题
"""

import socket
import requests
import time
import sys
import platform
import subprocess
import os
from typing import List, Dict, Optional

# 服务器端口
PORT = 8090

def get_network_info() -> Dict:
    """获取网络信息"""
    info = {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.release(),
        "interfaces": {}
    }
    
    # 尝试获取IP地址
    try:
        # 获取主机名对应的IP
        info["ip"] = socket.gethostbyname(info["hostname"])
    except:
        info["ip"] = "无法获取"
    
    # 获取网络接口信息（仅限Unix系统）
    if platform.system() != "Windows":
        try:
            # 运行ifconfig命令获取网络接口信息
            result = subprocess.run(["ifconfig"], capture_output=True, text=True)
            info["interfaces_raw"] = result.stdout
        except:
            info["interfaces_raw"] = "无法获取"
    
    return info

def get_connection_urls(port: int) -> List[str]:
    """获取可能的服务器URL列表"""
    urls = []
    
    # 添加常用的本地主机名和IP
    urls.append(f"http://localhost:{port}")
    urls.append(f"http://127.0.0.1:{port}")
    urls.append(f"http://0.0.0.0:{port}")
    
    # 添加IPv6回环地址
    urls.append(f"http://[::1]:{port}")
    
    # 尝试获取本机IP地址（非回环）
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip != "127.0.0.1":
            urls.append(f"http://{ip}:{port}")
            urls.append(f"http://{hostname}:{port}")
            
        # 尝试获取所有可能的IP地址
        all_ips = socket.gethostbyname_ex(hostname)[2]
        for ip in all_ips:
            if ip != "127.0.0.1" and f"http://{ip}:{port}" not in urls:
                urls.append(f"http://{ip}:{port}")
    except Exception as e:
        print(f"获取本机IP地址时出错: {e}")
    
    # 添加可能的Docker网络IP
    urls.append(f"http://172.17.0.1:{port}")
    
    return urls

def test_socket_connection(host: str, port: int, timeout: int = 2) -> bool:
    """测试原始套接字连接"""
    try:
        # 从URL中提取主机名
        if host.startswith("http://"):
            host = host.replace("http://", "")
        if host.startswith("https://"):
            host = host.replace("https://", "")
        if ":" in host:
            host = host.split(":")[0]
        
        # 创建套接字并尝试连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        return result == 0
    except Exception as e:
        print(f"  套接字连接测试失败: {e}")
        return False

def test_http_connection(url: str, timeout: int = 2) -> Dict:
    """测试HTTP连接"""
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
    
    # 从URL中提取主机名和端口
    try:
        host = url.replace("http://", "").replace("https://", "").split("/")[0]
        if ":" in host:
            host, port_str = host.split(":")
            port = int(port_str)
        else:
            port = 80 if url.startswith("http://") else 443
            
        # 测试套接字连接
        result["socket_ok"] = test_socket_connection(host, port, timeout)
        
        if not result["socket_ok"]:
            result["error"] = "套接字连接失败"
            return result
            
        # 测试HTTP连接
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        result["time_ms"] = round((end_time - start_time) * 1000)
        result["status_code"] = response.status_code
        result["http_ok"] = 200 <= response.status_code < 300
        
        if result["http_ok"]:
            try:
                result["response"] = response.json()
                # 检查健康端点
                if url.endswith("/health"):
                    result["health_ok"] = (
                        isinstance(result["response"], dict) and 
                        result["response"].get("status") == "running"
                    )
            except:
                result["response"] = response.text[:100]
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    """主函数"""
    print("\n===== TTS服务器连接诊断工具 =====\n")
    
    # 获取网络信息
    print("正在获取网络信息...")
    network_info = get_network_info()
    print(f"主机名: {network_info['hostname']}")
    print(f"操作系统: {network_info['os']} {network_info['os_version']}")
    print(f"主IP地址: {network_info['ip']}")
    print("")
    
    # 测试端口是否开放
    print(f"测试端口 {PORT} 是否开放...")
    open_port = test_socket_connection("localhost", PORT)
    if open_port:
        print(f"✓ 端口 {PORT} 已开放")
    else:
        print(f"✗ 端口 {PORT} 未开放或被阻止")
        print(f"请确保TTS服务器正在运行，并监听端口 {PORT}")
        sys.exit(1)
        
    # 获取可能的URL列表
    urls = get_connection_urls(PORT)
    print(f"\n将测试 {len(urls)} 个可能的服务器URL...")
    
    # 测试连接健康端点
    successful_urls = []
    health_urls = [f"{url}/health" for url in urls]
    
    for i, url in enumerate(health_urls):
        print(f"\n正在测试 {url}...")
        result = test_http_connection(url)
        
        if result["socket_ok"]:
            print(f"  ✓ 套接字连接成功")
        else:
            print(f"  ✗ 套接字连接失败")
            
        if result["http_ok"]:
            print(f"  ✓ HTTP请求成功 (状态码: {result['status_code']}, 耗时: {result['time_ms']}ms)")
        else:
            print(f"  ✗ HTTP请求失败 (状态码: {result['status_code']})")
            
        if result["health_ok"]:
            print(f"  ✓ 健康检查通过")
            successful_urls.append(urls[i])
        else:
            print(f"  ✗ 健康检查失败")
            
        if result["error"]:
            print(f"  错误: {result['error']}")
    
    # 总结结果
    print("\n===== 诊断结果 =====")
    if successful_urls:
        print(f"找到 {len(successful_urls)} 个可用的服务器URL:")
        for url in successful_urls:
            print(f"  ✓ {url}")
        
        print("\n推荐操作:")
        print(f"1. 使用这些可用的URL之一创建客户端:")
        print(f"   python vpn_compatible_tts.py --server-url {successful_urls[0]}")
    else:
        print("✗ 未找到可用的服务器URL")
        print("\n可能的原因:")
        print("1. TTS服务器未运行或未在正确的端口上监听")
        print("2. VPN软件正在阻止所有本地连接")
        print("3. 防火墙规则阻止了连接")
        print("4. 服务器健康检查端点未正确实现")
        
        print("\n推荐操作:")
        print("1. 确认TTS服务器正在运行: python tts_server.py")
        print(f"2. 检查端口 {PORT} 是否被监听: netstat -ant | grep {PORT}")
        print("3. 尝试临时禁用VPN，测试是否可以连接")
        print("4. 检查防火墙规则，确保允许本地连接")
        print("5. 尝试使用不同的端口")
    
    print("\n==========================")

if __name__ == "__main__":
    main() 