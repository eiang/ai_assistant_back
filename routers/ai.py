# 导入必要的模块
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File  # FastAPI相关组件
from sqlalchemy.orm import Session  # 数据库会话
import os  # 操作系统功能
import tempfile  # 临时文件处理

# 导入项目内部模块
import sys
sys.path.append('/Users/heqiang/my_project/ai_assistant_back')
from database import get_db  # 数据库会话依赖
from models import User  # 用户模型
from utils import get_current_user  # 用户认证依赖
from config import ALLOWED_AUDIO_FORMATS  # 导入支持的音频格式配置

# 创建路由器
router = APIRouter()

# 语音识别接口
@router.post("/speech-to-text")
async def speech_to_text(
    audio: UploadFile = File(...),  # 上传的音频文件
    current_user: User = Depends(get_current_user),  # 当前认证用户
    db: Session = Depends(get_db)  # 数据库会话
):
    """
    语音识别接口
    
    将上传的音频文件转换为文本
    
    Args:
        audio: 上传的音频文件
        current_user: 当前认证用户，由get_current_user依赖项提供
        db: 数据库会话，由get_db依赖项提供
        
    Returns:
        dict: 包含识别文本的响应
        
    Raises:
        HTTPException: 当音频格式不支持时抛出400错误
    """
    # 检查文件格式
    if audio.content_type not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的音频格式，请上传mp3、wav或m4a格式")  # 格式不支持则抛出异常
    
    # 保存临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False)  # 创建命名临时文件
    try:
        contents = await audio.read()  # 异步读取上传的文件内容
        with open(temp_file.name, "wb") as f:
            f.write(contents)  # 写入临时文件
        
        # 在实际应用中，这里应该调用语音识别服务
        # 例如百度语音识别、讯飞语音识别或其他第三方服务
        # 这里简化处理，直接返回模拟结果
        
        # 模拟语音识别结果
        recognized_text = "这是从语音中识别出的文本。在实际应用中，这里应该是真实的语音识别结果。"
        
        # 返回响应
        return {
            "code": 200,  # 状态码
            "message": "success",  # 状态消息
            "data": {
                "text": recognized_text  # 识别出的文本
            }
        }
    finally:
        # 清理临时文件
        temp_file.close()  # 关闭文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)  # 删除临时文件