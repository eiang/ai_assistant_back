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

# 翻译功能的实现
def translate_text(userMessage: str, translation_type: str):
    """
    根据用户选择的翻译类型（中译英或英译中）翻译文本
    
    Args:
        userMessage: 用户要翻译的文本
        translation_type: 翻译类型，可选 "中译英" 或 "英译中"
        
    Returns:
        str: 翻译后的文本
    """
    try:
        print(f"开始处理翻译请求 - 类型: {translation_type}, 内容: '{userMessage[:100]}...'")
        
        if translation_type == "翻译中译英":
            system_prompt = """你是一个专业的中英翻译专家。请将用户输入的中文文本翻译成地道、流畅的英文。只返回翻译后的内容，不要有任何解释或额外说明。保持原文的风格和语气。"""
        elif translation_type == "翻译英译中":
            system_prompt = """你是一个专业的英中翻译专家。请将用户输入的英文文本翻译成地道、流畅的中文。只返回翻译后的内容，不要有任何解释或额外说明。保持原文的风格和语气。"""
        elif translation_type == "翻译中译日":
            system_prompt = """你是一个专业的中日翻译专家。请将用户输入的中文文本翻译成地道、流畅的日文。只返回翻译后的内容，不要有任何解释或额外说明。保持原文的风格和语气。"""
        elif translation_type == "翻译日译中":
            system_prompt = """你是一个专业的日中翻译专家。请将用户输入的日文文本翻译成地道、流畅的中文。只返回翻译后的内容，不要有任何解释或额外说明。保持原文的风格和语气。"""
        elif translation_type == "翻译中译法":
            system_prompt = """你是一个专业的法中翻译专家。请将用户输入的中文文本翻译成地道、流畅的法文。只返回翻译后的内容，不要有任何解释或额外说明。保持原文的风格和语气。"""
        elif translation_type == "翻译法译中":
            system_prompt = """你是一个专业的法中翻译专家。请将用户输入的法文文本翻译成地道、流畅的中文。只返回翻译后的内容，不要有任何解释或额外说明。保持原文的风格和语气。"""
        else:
            return f"不支持的翻译类型: {translation_type}"
        
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=0.2  # 使用较低的温度值保证翻译的准确性
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=userMessage)
        ]
        
        response = llm.invoke(messages)
        translated_text = response.content
        
        print(f"翻译完成 - 结果: '{translated_text[:100]}...'")
        return translated_text
        
    except Exception as e:
        print(f"翻译处理错误: {str(e)}")
        return f"抱歉，翻译过程中出现错误: {str(e)}"

# 评价生成功能的实现
def generate_review(userMessage: str, review_type: str, length: str):
    """
    根据用户输入的关键词生成指定类型和长度的评价
    
    Args:
        userMessage: 用户输入的评价对象关键词
        review_type: 评价类型，可选 "好评" 或 "差评"
        length: 评价字数，可选 "二十字"、"三十字"、"四十字"
        
    Returns:
        str: 生成的评价文本
    """
    try:
        print(f"开始处理评价生成请求 - 类型: {review_type}, 长度: {length}, 关键词: '{userMessage}'")
        
        # 确定字数限制
        if length == "二十字":
            word_limit = 20
        elif length == "三十字":
            word_limit = 30
        elif length == "四十字":
            word_limit = 40
        else:
            word_limit = 30  # 默认值
        
        # 构建系统提示
        if review_type.startswith("好评"):
            system_prompt = f"""你是一个专业的评价生成助手。请为用户输入的内容生成一段正面、积极的好评，体现产品/服务的优点。评价要真实可信，不要过于夸张或做作。评价字数控制在{word_limit}字左右，请只返回生成的评价内容，不要包含任何解释或额外说明。"""
        elif review_type.startswith("差评"):
            system_prompt = f"""你是一个专业的评价生成助手。请为用户输入的内容生成一段负面、客观的差评，指出产品/服务的不足之处。评价要具体、理性，不要无端抱怨或情绪化。评价字数控制在{word_limit}字左右，请只返回生成的评价内容，不要包含任何解释或额外说明。"""
        else:
            return f"不支持的评价类型: {review_type}"
        
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=0.7  # 使用较高的温度值增加评价的多样性
        )
        
        # 构建提示信息
        prompt = f"请为以下内容生成{word_limit}字左右的{review_type}：{userMessage}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        review_text = response.content
        
        print(f"评价生成完成 - 结果: '{review_text}'")
        return review_text
        
    except Exception as e:
        print(f"评价生成错误: {str(e)}")
        return f"抱歉，评价生成过程中出现错误: {str(e)}"

# 朋友圈文案生成功能
def generate_friend_circle_post(userMessage: str, post_type: str, length: str):
    """
    根据用户输入的关键词生成指定类型和长度的朋友圈文案
    
    Args:
        userMessage: 用户输入的关键词或主题
        post_type: 文案类型，可选 "过节"、"生日"、"祝福"、"表白"、"分手"
        length: 文案字数，可选 "二十字"、"三十字"、"四十字"
        
    Returns:
        str: 生成的朋友圈文案
    """
    try:
        print(f"开始处理朋友圈文案生成请求 - 类型: {post_type}, 长度: {length}, 关键词: '{userMessage}'")
        
        # 确定字数限制
        if length == "二十字":
            word_limit = 20
        elif length == "三十字":
            word_limit = 30
        elif length == "四十字":
            word_limit = 40
        else:
            word_limit = 30  # 默认值
        
        # 构建系统提示
        prompts = {
            "过节": f"""你是一个社交媒体文案专家。请为用户输入的节日生成一条朋友圈文案，文案应当简洁有力，能够表达节日的喜悦氛围，字数控制在{word_limit}字左右。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "生日": f"""你是一个社交媒体文案专家。请根据用户输入生成一条关于生日的朋友圈文案，文案应当温馨感人，能够表达对自己或他人生日的祝福，字数控制在{word_limit}字左右。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "祝福": f"""你是一个社交媒体文案专家。请根据用户输入生成一条祝福类朋友圈文案，文案应当真挚诚恳，能够传达美好的祝愿，字数控制在{word_limit}字左右。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "表白": f"""你是一个社交媒体文案专家。请根据用户输入生成一条表白类朋友圈文案，文案应当浪漫感人，能够表达真挚的爱意，字数控制在{word_limit}字左右。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "分手": f"""你是一个社交媒体文案专家。请根据用户输入生成一条关于分手或失恋的朋友圈文案，文案应当伤感但不过度悲观，能够表达对过去感情的告别，字数控制在{word_limit}字左右。请只返回生成的文案内容，不要包含任何解释或额外说明。"""
        }
        
        system_prompt = prompts.get(post_type, f"你是一个社交媒体文案专家。请生成一条朋友圈文案，字数控制在{word_limit}字左右。")
        
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=0.7  # 使用较高的温度值增加文案的创意性
        )
        
        # 构建提示信息
        prompt = f"请根据关键词「{userMessage}」，为我创作一条{post_type}场景的朋友圈文案，字数控制在{word_limit}字左右。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        post_text = response.content
        
        print(f"朋友圈文案生成完成 - 结果: '{post_text}'")
        return post_text
        
    except Exception as e:
        print(f"朋友圈文案生成错误: {str(e)}")
        return f"抱歉，朋友圈文案生成过程中出现错误: {str(e)}"

# 小红书文案生成功能
def generate_xiaohongshu_post(userMessage: str, post_type: str, length: str):
    """
    根据用户输入的关键词生成指定类型和长度的小红书文案
    
    Args:
        userMessage: 用户输入的关键词或主题
        post_type: 文案类型，可选 "种草"、"吐槽"、"分享"、"暗广"
        length: 文案字数，可选 "五十字"、"一百字"、"二百字"
        
    Returns:
        str: 生成的小红书文案
    """
    try:
        print(f"开始处理小红书文案生成请求 - 类型: {post_type}, 长度: {length}, 关键词: '{userMessage}'")
        
        # 确定字数限制
        if length == "五十字":
            word_limit = 50
        elif length == "一百字":
            word_limit = 100
        elif length == "二百字":
            word_limit = 200
        else:
            word_limit = 100  # 默认值
        
        # 构建系统提示
        prompts = {
            "种草": f"""你是一个小红书文案专家。请为用户输入的产品或服务生成一条种草类小红书文案，文案应当真实可信，包含产品亮点和个人使用感受，语气要亲切自然，带有惊喜感，字数控制在{word_limit}字左右。请加入合适的表情符号和排版，但不要过多。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "吐槽": f"""你是一个小红书文案专家。请根据用户输入生成一条吐槽类小红书文案，文案应当幽默诙谐，带有一定的批判性但不要过于尖刻，语气要生活化，字数控制在{word_limit}字左右。请加入合适的表情符号和排版，但不要过多。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "分享": f"""你是一个小红书文案专家。请根据用户输入生成一条分享类小红书文案，文案应当详实有用，提供有价值的信息或经验，语气要真诚，字数控制在{word_limit}字左右。请加入合适的表情符号和排版，但不要过多。请只返回生成的文案内容，不要包含任何解释或额外说明。""",
            "暗广": f"""你是一个小红书文案专家。请根据用户输入生成一条巧妙融入产品推广的小红书文案，文案应当不显刻意，将产品自然地融入内容中，语气要轻松自然，字数控制在{word_limit}字左右。请加入合适的表情符号和排版，但不要过多。请只返回生成的文案内容，不要包含任何解释或额外说明。"""
        }
        
        system_prompt = prompts.get(post_type, f"你是一个小红书文案专家。请生成一条小红书文案，字数控制在{word_limit}字左右。")
        
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=0.8  # 使用较高的温度值增加文案的多样性和创意性
        )
        
        # 构建提示信息
        prompt = f"请为「{userMessage}」创作一篇{post_type}类型的小红书文案，字数约{word_limit}字。加入适量表情符号和排版，使文案生动有趣。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        post_text = response.content
        
        print(f"小红书文案生成完成 - 结果前100字: '{post_text[:100]}...'")
        return post_text
        
    except Exception as e:
        print(f"小红书文案生成错误: {str(e)}")
        return f"抱歉，小红书文案生成过程中出现错误: {str(e)}"

# 砍价话术生成功能
def generate_bargain_script(userMessage: str, product_type: str, length: str):
    """
    根据用户输入生成砍价话术
    
    Args:
        userMessage: 用户输入的具体商品或场景
        product_type: 产品类型，如"衣服"、"鞋子"、"包包"等
        length: 话术字数，可选 "二十字"、"三十字"、"四十字"
        
    Returns:
        str: 生成的砍价话术
    """
    try:
        print(f"开始处理砍价话术生成请求 - 类型: {product_type}, 长度: {length}, 关键词: '{userMessage}'")
        
        # 确定字数限制
        if length == "二十字":
            word_limit = 20
        elif length == "三十字":
            word_limit = 30
        elif length == "四十字":
            word_limit = 40
        else:
            word_limit = 30  # 默认值
        
        # 构建系统提示
        prompts = {
            "衣服": f"""你是一个砍价话术专家。请为用户购买衣服场景生成一条砍价话术，话术应当有理有据，不卑不亢，能够委婉表达降价意愿，字数控制在{word_limit}字左右。请只返回生成的话术内容，不要包含任何解释或额外说明。""",
            "鞋子": f"""你是一个砍价话术专家。请为用户购买鞋子场景生成一条砍价话术，话术应当有理有据，不卑不亢，能够委婉表达降价意愿，字数控制在{word_limit}字左右。请只返回生成的话术内容，不要包含任何解释或额外说明。""",
            "包包": f"""你是一个砍价话术专家。请为用户购买包包场景生成一条砍价话术，话术应当有理有据，不卑不亢，能够委婉表达降价意愿，字数控制在{word_limit}字左右。请只返回生成的话术内容，不要包含任何解释或额外说明。""",
            "化妆品": f"""你是一个砍价话术专家。请为用户购买化妆品场景生成一条砍价话术，话术应当有理有据，不卑不亢，能够委婉表达降价意愿，字数控制在{word_limit}字左右。请只返回生成的话术内容，不要包含任何解释或额外说明。""",
            "数码产品": f"""你是一个砍价话术专家。请为用户购买数码产品场景生成一条砍价话术，话术应当有理有据，不卑不亢，能够委婉表达降价意愿，字数控制在{word_limit}字左右。请只返回生成的话术内容，不要包含任何解释或额外说明。""",
            "闲鱼转转二手": f"""你是一个砍价话术专家。请为用户在二手平台购物场景生成一条砍价话术，话术应当有理有据，不卑不亢，能够委婉表达降价意愿，字数控制在{word_limit}字左右。请只返回生成的话术内容，不要包含任何解释或额外说明。"""
        }
        
        system_prompt = prompts.get(product_type, f"你是一个砍价话术专家。请生成一条砍价话术，字数控制在{word_limit}字左右。")
        
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=0.6  # 使用适中的温度值，保证话术的实用性
        )
        
        # 构建提示信息
        prompt = f"请为我想购买的「{userMessage}」({product_type}类商品)生成一条砍价话术，字数控制在{word_limit}字左右。话术要委婉有效，不卑不亢。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        bargain_text = response.content
        
        print(f"砍价话术生成完成 - 结果: '{bargain_text}'")
        return bargain_text
        
    except Exception as e:
        print(f"砍价话术生成错误: {str(e)}")
        return f"抱歉，砍价话术生成过程中出现错误: {str(e)}"

# 做菜达人功能
def generate_cooking_recipe(ingredients: str):
    """
    根据用户提供的食材生成一道菜的做法
    
    Args:
        ingredients: 用户提供的食材列表，以逗号分隔
        
    Returns:
        str: 生成的菜谱和烹饪方法
    """
    try:
        print(f"开始处理做菜达人请求 - 食材: '{ingredients}'")
        
        # 构建系统提示
        system_prompt = """你是一位专业的中式烹饪大师。
请根据用户提供的食材，创造一道美味可口的菜肴。
你的回答应包含以下内容：
1. 菜名：为这道菜起一个吸引人的名字 🍽️
2. 主要食材：列出用户提供的食材 🥬
3. 辅助食材：推荐一些常见的配料和调味料（如果用户没有提到）🧂
4. 烹饪步骤：详细的步骤指导，包括火候、时间等关键信息 🔥
5. 烹饪小贴士：分享1-2个能提升这道菜口感的专业技巧 💡
6. 最终效果：描述一下这道菜理想的口感和风味 👨‍🍳

生成的文字格式为文本加手机emoji，回答要详细专业，但语言要通俗易懂，让普通家庭也能轻松完成。"""
        
        llm = ChatDeepSeek(
            model=MODEL_NAME,
            temperature=0.7  # 使用较高的温度值增加菜谱的创意性
        )
        
        # 构建提示信息
        prompt = f"我有这些食材：{ingredients}。请教我用这些食材做一道美味的菜，提供详细的步骤和技巧。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        recipe_text = response.content
        
        print(f"菜谱生成完成 - 结果前100字: '{recipe_text[:100]}...'")
        return recipe_text
        
    except Exception as e:
        print(f"菜谱生成错误: {str(e)}")
        return f"抱歉，菜谱生成过程中出现错误: {str(e)}"