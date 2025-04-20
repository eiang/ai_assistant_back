# 导入必要的模块
from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI相关组件
from sqlalchemy.orm import Session  # 数据库会话

# 导入项目内部模块
import sys
sys.path.append('/Users/heqiang/my_project/ai_assistant_back')
from database import get_db  # 数据库会话依赖
from database import get_db  # 数据库会话依赖
from models import User  # 数据模型
from utils import get_current_user  # 用户认证依赖

# 创建路由器
router = APIRouter()

# 获取用户信息接口
@router.get("/info")
async def get_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取当前用户信息接口
    
    返回用户基本信息和个性化设置
    
    Args:
        current_user: 当前认证用户，由get_current_user依赖项提供
        db: 数据库会话，由get_db依赖项提供
        
    Returns:
        dict: 包含用户信息和设置的响应
    """
    # 获取用户设置
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        # 如果没有设置，创建默认设置
        settings = UserSettings(user_id=current_user.id)  # 创建默认用户设置
        db.add(settings)  # 添加到数据库会话
        db.commit()  # 提交事务
        db.refresh(settings)  # 刷新对象
    
    # 返回响应
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": current_user.id,  # 用户ID
            "openid": current_user.openid,  # 微信openid
            "nickName": current_user.nick_name,  # 用户昵称
            "avatar": current_user.avatar,  # 用户头像
            "createdAt": current_user.created_at.isoformat(),  # 格式化创建时间
            "settings": {  # 用户设置
                "isDarkMode": settings.is_dark_mode,  # 深色模式
                "autoRead": settings.auto_read,  # 自动朗读
                "saveHistory": settings.save_history  # 保存历史
            }
        }
    }