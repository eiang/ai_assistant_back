from langchain_deepseek import ChatDeepSeek

# 导入必要的模块
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import requests
from langchain_core.messages import HumanMessage, SystemMessage
import json
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 加载环境变量
env = os.getenv("ENV", "development")
load_dotenv(f".env.{env}")

# 从环境变量中获取DeepSeek配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
TEMPERATURE = os.getenv("TEMPERATURE")
MODEL_NAME = os.getenv("MODEL_NAME")

# 从环境变量中获取Text2Image配置
TEXT2IMAGE_API_KEY = os.getenv("TEXT2IMAGE_API_KEY")
# 添加默认URL，避免未设置环境变量的问题
TEXT2IMAGE_URL = os.getenv("TEXT2IMAGE_URL", "https://api.acedata.cloud/flux/images")
TEXT2IMAGE_API_AUTHORIZATION = os.getenv("TEXT2IMAGE_API_AUTHORIZATION", "")  # 添加默认空值

# 检查并提示认证信息缺失
if not TEXT2IMAGE_API_AUTHORIZATION:
    print("警告：TEXT2IMAGE_API_AUTHORIZATION 未设置，API调用可能会失败")

headers = {
    "accept": "application/json",
    "authorization": TEXT2IMAGE_API_AUTHORIZATION,
    "content-type": "application/json"
}

payload = {
    "model": "flux",
    "action": "generate",
    "size": "1024x1024",
    "prompt": "a white siamese cat"
}
url = TEXT2IMAGE_URL

# 禁用不安全连接警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建一个具有重试功能的会话
def create_retry_session(retries=3, backoff_factor=0.5):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def text2image(userMessage: str):
    """
     根据用户的输入，将userMessage传入deepseek的api，让deepseek优化提示词，
     将优化好的提示词传入text2image的api，生成图片
    """
    try:
        print(f"开始处理用户请求: '{userMessage}'")
        # 优化提示词处理
        try:
            prompt = deepseek_optimize_prompt(userMessage)
            print(f"优化后的提示词: '{prompt}'")
        except Exception as prompt_err:
            print(f"提示词优化失败，使用原始输入: {str(prompt_err)}")
            # 如果优化提示词失败，使用原始输入，不影响整体流程
            prompt = userMessage
            
        payload = {
            "model": "flux",
            "action": "generate",
            "size": "1024x1024",
            "prompt": prompt
        }
        print("payload: ", payload)
        
        # 设置超时时间和重试次数
        timeout = 180  # 增加超时时间到180秒(3分钟),因为图片生成可能需要较长时间
        max_retries = 3
        retry_count = 0
        
        # 使用重试会话
        session = create_retry_session()
        
        while retry_count < max_retries:
            try:
                print(f"开始第 {retry_count + 1}/{max_retries} 次请求图片API...")
                # 尝试不进行SSL验证，解决SSL问题
                response = session.post(
                    url, 
                    json=payload, 
                    headers=headers, 
                    timeout=timeout,
                    verify=False  # 禁用SSL验证
                )
                
                # 检查响应状态码
                if response.status_code == 401:
                    print("认证失败：请检查TEXT2IMAGE_API_AUTHORIZATION环境变量")
                    return json.dumps({
                        "success": False,
                        "error": "API认证失败",
                        "message": "图片生成失败：API认证失败，请联系管理员检查API密钥"
                    })
                elif response.status_code != 200:
                    print(f"API请求失败，状态码: {response.status_code}，响应: {response.text}")
                    # 非200状态码也重试
                    retry_count += 1
                    time.sleep(2)
                    continue
                    
                print("text2image response status:", response.status_code)
                print("text2image response长度: ", len(response.text))
                # 只打印响应的前200个字符，避免日志过大
                print("text2image response预览: ", response.text)
                return response.text
            except requests.exceptions.SSLError as ssl_err:
                print(f"SSL错误 (尝试 {retry_count+1}/{max_retries}): {str(ssl_err)}")
                retry_count += 1
                # 添加延迟避免快速重试
                time.sleep(2)  # 增加延迟时间
                if retry_count >= max_retries:
                    return json.dumps({
                        "success": False,
                        "error": "SSL连接失败",
                        "message": f"SSL连接失败，已尝试 {max_retries} 次: {str(ssl_err)}"
                    })
            except requests.exceptions.Timeout:
                print(f"请求超时 (尝试 {retry_count+1}/{max_retries})")
                retry_count += 1
                time.sleep(2)
                if retry_count >= max_retries:
                    return json.dumps({
                        "success": False,
                        "error": "请求超时",
                        "message": f"图片生成请求超时，已尝试 {max_retries} 次，每次等待 {timeout} 秒。请尝试简化您的描述或稍后再试。"
                    })
            except requests.exceptions.ConnectionError as conn_err:
                print(f"连接错误 (尝试 {retry_count+1}/{max_retries}): {str(conn_err)}")
                retry_count += 1
                time.sleep(2)
                if retry_count >= max_retries:
                    return json.dumps({
                        "success": False,
                        "error": "连接失败",
                        "message": f"连接失败，已尝试 {max_retries} 次: {str(conn_err)}"
                    })
        
        # 如果重试次数达到上限仍然失败
        return json.dumps({
            "success": False,
            "error": "多次尝试失败",
            "message": f"图片生成失败，已尝试 {max_retries} 次但未成功"
        })
        
    except Exception as e:
        print(f"text2image调用错误: {str(e)}")
        # 返回格式化的JSON错误信息
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"抱歉，图片生成过程中出现错误: {str(e)}"
        })

# 添加测试函数用于故障排查
def test_text2image_connection():
    """测试与Text2Image服务的连接"""
    try:
        # 简化的测试请求
        test_payload = {
            "model": "flux",
            "action": "generate",
            "size": "512x512",  # 使用较小尺寸加快测试
            "prompt": "test connection"
        }
        
        session = create_retry_session()
        response = session.post(
            url,
            json=test_payload,
            headers=headers,
            timeout=30,
            verify=False
        )
        
        print(f"连接测试状态码: {response.status_code}")
        print(f"连接测试响应: {response.text[:200]}...")  # 只打印前200个字符
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "message": "连接成功" if response.status_code < 400 else "连接失败"
        }
    except Exception as e:
        print(f"连接测试错误: {str(e)}")
        return {
            "success": False,
            "message": f"连接测试错误: {str(e)}"
        }

# 初始化DeepSeek客户端
def get_deepseek_client(userMessage: str):
    """
    获取DeepSeek客户端实例并处理用户消息
    
    Args:
        userMessage: 用户消息内容
        
    Returns:
        str: AI回复内容
    """
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DeepSeek API密钥未配置"
        )
    
    try:
        print(f"开始处理DeepSeek文本请求: '{userMessage[:100]}...'")
        start_time = time.time()
        
        # 构建系统提示词模版
        system_prompt = """你是一个简洁的AI助手。请用纯文本格式回复，每次回复内容不超过300字。"""
        
        # 设置超时值
        os.environ["LANGCHAIN_TIMEOUT"] = "120"  # 设置120秒超时
        
        # 正确使用 ChatDeepSeek
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            timeout=120  # 直接设置超时为120秒(2分钟)
        )
        
        # 使用 ChatDeepSeek 的正确API调用方式
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=userMessage)
        ]
        
        # 执行调用
        print("正在发送请求到DeepSeek API...")
        response = llm.invoke(messages)
        
        # 计算处理时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"DeepSeek API响应时间: {elapsed_time:.2f}秒")
        
        # 输出响应内容（限制长度）
        content = response.content
        print(f"DeepSeek响应长度: {len(content)}")
        print(f"DeepSeek响应前200字符: {content[:200]}...")
        
        return content
    except Exception as e:
        # 记录详细错误信息
        import traceback
        error_trace = traceback.format_exc()
        print(f"DeepSeek调用错误: {str(e)}")
        print(f"详细错误堆栈: {error_trace}")
        
        # 检查是否是超时错误
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            return f"抱歉，响应超时。您的问题可能过于复杂，请尝试简化问题或稍后再试。"
        
        return f"抱歉，我现在无法回答您的问题，因为: {str(e)}"

def deepseek_optimize_prompt(userMessage: str):
    """
     根据用户的输入，将userMessage传入deepseek的api，让deepseek优化提示词
     """
    try:
        system_prompt = """你是一个专业的prompt优化师，请根据用户的输入，优化提示词，使得生成的图片更加符合用户的需求，要求只返回优化后的英文提示词文本，不要返回其他内容。"""
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=TEMPERATURE
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=userMessage)
        ]
        prompt = llm.invoke(messages)
        return prompt.content
    except Exception as e:
        print(f"DeepSeek调用错误: {str(e)}")
        return f"抱歉，我现在无法优化提示词，因为: {str(e)}"