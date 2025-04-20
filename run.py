#!/usr/bin/env python
# 启动脚本，根据指定环境启动服务
import os
import sys
import argparse
import subprocess

def main():
    """
    根据命令行参数设置环境变量并启动服务
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AI助手后端服务启动脚本')
    parser.add_argument('-e', '--env', 
                        choices=['development', 'production'], 
                        default='development',
                        help='指定运行环境 (默认: development)')
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ["ENV"] = args.env
    
    # 提示当前环境
    print(f"正在使用 {args.env} 环境启动服务...")
    
    # 检查对应的环境文件是否存在
    env_file = f".env.{args.env}"
    if not os.path.exists(env_file):
        print(f"警告: 配置文件 {env_file} 不存在")
        if not os.path.exists(".env"):
            print(f"警告: 默认配置文件 .env 也不存在，将使用程序内置默认值")
        else:
            print(f"将使用默认配置文件 .env")
    
    # 启动服务
    subprocess.run(["python", "main.py"])

if __name__ == "__main__":
    main() 