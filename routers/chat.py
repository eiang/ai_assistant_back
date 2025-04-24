# 导入必要的模块
from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI相关组件
from sqlalchemy.orm import Session  # 数据库会话
from typing import Optional  # 类型提示
from pydantic import BaseModel  # 数据验证
from datetime import datetime  # 日期时间处理
import uuid  # 生成唯一标识符
import json  # 用于解析JSON数据
from fastapi.responses import JSONResponse  # 用于返回JSON响应

# 导入项目内部模块

from database import get_db  # 数据库会话依赖
from models import User, ChatSession, ChatMessage  # 数据模型
from routers.chatwithdeepseek import deepseek_optimize_prompt, get_deepseek_client, text2image, test_text2image_connection
from utils import get_current_user  # 用户认证依赖

# 创建路由器
router = APIRouter()

# 发送消息请求模型
class MessageRequest(BaseModel):
    """发送消息请求数据模型
    
    Attributes:
        content: 消息内容
        sessionId: 会话ID，可选，如果不提供则创建新会话
    """
    content: str  # 消息内容
    sessionId: Optional[str] = None  # 会话ID，可选

# 发送消息接口
@router.post("/message")
async def send_message(request: MessageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """发送消息接口
    
    处理用户发送的消息，获取AI回复并保存对话记录
    
    Args:
        request: 消息请求数据
        current_user: 当前认证用户，由get_current_user依赖项提供
        db: 数据库会话，由get_db依赖项提供
        
    Returns:
        dict: 包含会话ID、消息ID和AI回复的响应
        
    Raises:
        HTTPException: 当指定的会话不存在时抛出404错误
    """
    # 获取或创建会话
    session = None
    if request.sessionId:
        # 如果提供了会话ID，查找该会话
        session = db.query(ChatSession).filter(
            ChatSession.id == request.sessionId,
            ChatSession.user_id == current_user.id  # 确保会话属于当前用户
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        # 如果没有提供会话ID，创建新会话
        session = ChatSession(user_id=current_user.id)
        db.add(session)  # 添加到数据库会话
        db.commit()  # 提交事务
        db.refresh(session)  # 刷新对象
    
    # 创建用户消息记录
    user_message = ChatMessage(
        session_id=session.id,
        is_user=True,  # 标记为用户消息
        content=request.content
    )
    db.add(user_message)  # 添加到数据库会话
    db.commit()  # 提交事务
    db.refresh(user_message)  # 刷新对象
    
    # 这里应该调用AI服务获取回复
    # 在实际应用中，可能需要调用OpenAI API或其他AI服务
    ai_reply = "这是AI的回复。在实际应用中，这里应该调用AI服务获取真实回复。"
    
    # 创建AI回复消息记录
    ai_message = ChatMessage(
        session_id=session.id,
        is_user=False,  # 标记为AI消息
        content=ai_reply
    )
    db.add(ai_message)  # 添加到数据库会话
    db.commit()  # 提交事务
    db.refresh(ai_message)  # 刷新对象
    
    # 更新会话最后更新时间
    session.updated_at = datetime.utcnow()
    db.commit()  # 提交事务
    
    # 返回响应
    return {
        "code": 200,
        "message": "success",
        "data": {
            "sessionId": session.id,  # 会话ID
            "messageId": ai_message.id,  # 消息ID
            "reply": {
                "content": ai_message.content,  # AI回复内容
                "time": ai_message.created_at.isoformat()  # 格式化创建时间
            }
        }
    }

@router.get("/chatAi")
async def chat_ai(message: str, functionType: str = None, functionValue: str = None):
    """
    使用deepseek api回复消息，支持额外功能（翻译、评价生成、朋友圈文案、小红书文案、砍价话术）
    
    Args:
        message: 用户发送的消息内容
        functionType: 功能类型，如"翻译中译英"、"评价好评"、"朋友圈生日"等
        functionValue: 功能附加值，如评价功能中的字数要求："二十字"、"三十字"等
        
    Returns:
        dict: 包含AI回复的响应
    """
    try:
        # 记录接收到的参数
        print(f"接收到的消息参数: {message}")
        print(f"功能类型: {functionType}, 功能值: {functionValue}")
        
        if not message:
            print("消息内容为空")
            return {
                "code": 400,
                "message": "消息内容不能为空",
                "data": None
            }
        
        # 根据是否启用附加功能决定处理方式
        if functionType:
            print(f"使用附加功能: {functionType}")
            
            # 翻译功能
            if functionType.startswith("翻译"):
                from routers.chatwithdeepseek import translate_text
                response = translate_text(message, functionType)
                
            # 评价功能
            elif functionType.startswith("评价"):
                from routers.chatwithdeepseek import generate_review
                response = generate_review(message, functionType[2:], functionValue)
                
            # 朋友圈文案功能
            elif functionType.startswith("朋友圈"):
                from routers.chatwithdeepseek import generate_friend_circle_post
                response = generate_friend_circle_post(message, functionType[3:], functionValue)
                
            # 小红书文案功能
            elif functionType.startswith("小红书"):
                from routers.chatwithdeepseek import generate_xiaohongshu_post
                response = generate_xiaohongshu_post(message, functionType[3:], functionValue)
                
            # 砍价话术功能
            elif functionType.startswith("砍价"):
                from routers.chatwithdeepseek import generate_bargain_script
                response = generate_bargain_script(message, functionType[2:], functionValue)
                
            # 做菜达人功能
            elif functionType.startswith("做菜达人"):
                from routers.chatwithdeepseek import generate_cooking_recipe
                response = generate_cooking_recipe(message)
                
            # 不支持的功能类型
            else:
                response = f"不支持的功能类型: {functionType}"
                
        # 无附加功能，使用常规AI回复
        else:
            response = get_deepseek_client(message)
            
        print(f"AI响应: {response}")
        
        if response:
            return {
                "code": 200,
                "message": "success",
                "data": response
            }
        else:
            return {
                "code": 500,
                "message": "error",
                "data": "AI回复失败"
            }
    except Exception as e:
        print(f"处理AI聊天请求时出错: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"详细错误堆栈: {error_trace}")
        return {
            "code": 500,
            "message": "error",
            "data": f"处理请求失败: {str(e)}"
        }
    

@router.get("/text2imagewithdeepseek")
async def text2imagewithdeepseek(message: str):
    """
    生成图片的接口
    """
    try:
        print(f"收到文生图请求，消息内容: '{message[:100]}...'")
        response = text2image(message)
        print(f"文生图请求处理完成，返回数据长度: {len(response)}")
        
        # 确保返回的是有效的JSON格式
        try:
            import json
            # 尝试解析response确保是有效的JSON
            if isinstance(response, str):
                json_obj = json.loads(response)
                # 已经是有效的JSON字符串，直接返回
                return JSONResponse(content={"result": response})
            else:
                # 如果已经是对象，转为JSON字符串
                return JSONResponse(content={"result": json.dumps(response)})
        except Exception as json_err:
            print(f"JSON处理错误: {str(json_err)}")
            # 如果不是有效的JSON，包装为错误响应
            return JSONResponse(content={
                "result": json.dumps({
                    "success": False,
                    "error": "无效的响应格式",
                    "message": "服务器返回的数据不是有效的JSON格式"
                })
            })
    except Exception as e:
        print(f"文生图请求处理错误: {str(e)}")
        import json
        import traceback
        error_trace = traceback.format_exc()
        print(f"详细错误堆栈: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "result": json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "图片生成失败，服务器内部错误"
                })
            }
        )

# 添加测试API连接的端点
@router.get("/test-text2image-connection")
async def test_image_connection():
    """
    测试Text2Image API连接的接口
    """
    try:
        result = test_text2image_connection()
        return JSONResponse(content=result)
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
