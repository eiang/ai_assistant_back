from langchain_deepseek import ChatDeepSeek

# 导入必要的模块
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 加载环境变量
env = os.getenv("ENV", "development")
load_dotenv(f".env.{env}")

# 从环境变量中获取DeepSeek配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
TEMPERATURE = os.getenv("TEMPERATURE")
MODEL_NAME = os.getenv("MODEL_NAME")


# 初始化DeepSeek客户端
def get_deepseek_client(userMessage: str):
    """
    获取DeepSeek客户端实例
    
    Returns:
        ChatDeepSeek: DeepSeek聊天客户端实例
    """
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DeepSeek API密钥未配置"
        )
    
    try:
        # 构建系统提示词模版
        system_prompt = """你是一个简洁的AI助手。请用纯文本格式回复，每次回复内容不超过300字。"""
        
        # 正确使用 ChatDeepSeek
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=TEMPERATURE
        )
        
        # 使用 ChatDeepSeek 的正确API调用方式
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=userMessage)
        ]
        
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        print(f"DeepSeek调用错误: {str(e)}")
        return f"抱歉，我现在无法回答您的问题，因为: {str(e)}"
