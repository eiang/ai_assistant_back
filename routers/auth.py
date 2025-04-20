# 导入必要的模块
from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI相关组件
from sqlalchemy.orm import Session  # 数据库会话
from typing import Optional  # 类型提示
import jwt  # JWT令牌处理
from datetime import datetime, timedelta  # 日期时间处理
import requests  # HTTP请求
from pydantic import BaseModel  # 数据验证

# 导入项目内部模块
import sys
sys.path.append('/Users/heqiang/my_project/ai_assistant_back')
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, WECHAT_APPID, WECHAT_SECRET, WECHAT_LOGIN_URL  # 配置
from database import get_db  # 数据库依赖
from models import User, UserSettings  # 数据模型
from utils import get_current_user  # 导入认证依赖

# 创建路由器
router = APIRouter()

# 微信登录请求模型
class WechatLoginRequest(BaseModel):
    """微信小程序登录请求数据模型
    
    Attributes:
        code: 微信登录临时凭证
        userInfo: 用户信息字典，包含昵称、头像等
    """
    code: str  # 微信登录临时凭证
    userInfo: dict  # 用户信息

# 创建JWT令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌
    
    Args:
        data: 要编码到令牌中的数据
        expires_delta: 令牌过期时间增量，如果为None则使用默认过期时间
        
    Returns:
        str: 编码后的JWT令牌
    """
    to_encode = data.copy()  # 复制数据，避免修改原始数据
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # 使用指定的过期时间
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 使用默认过期时间
    to_encode.update({"exp": expire})  # 添加过期时间声明
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # 编码JWT
    return encoded_jwt

# 使用utils.py中的get_current_user函数

# 微信登录接口
@router.post("/wechat-login")
async def wechat_login(request: WechatLoginRequest, db: Session = Depends(get_db)):
    """微信小程序登录接口
    
    处理微信小程序登录请求，通过code获取openid，查找或创建用户，返回JWT令牌
    
    Args:
        request: 微信登录请求数据
        db: 数据库会话
        
    Returns:
        dict: 包含访问令牌和用户信息的响应
        
    Raises:
        HTTPException: 微信授权失败或获取openid失败时抛出400错误
    """
    # 调用微信接口获取openid
    url = f"{WECHAT_LOGIN_URL}?appid={WECHAT_APPID}&secret={WECHAT_SECRET}&js_code={request.code}&grant_type=authorization_code"
    response = requests.get(url)  # 发送HTTP请求
    result = response.json()  # 解析JSON响应
    
    # 检查微信接口返回的错误
    if "errcode" in result and result["errcode"] != 0:
        raise HTTPException(status_code=400, detail="微信授权失败")
    
    # 获取openid
    openid = result.get("openid")
    if not openid:
        raise HTTPException(status_code=400, detail="获取openid失败")
    
    # 查找或创建用户
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        # 创建新用户
        user = User(
            openid=openid,
            nick_name=request.userInfo.get("nickName", ""),  # 获取昵称，默认为空字符串
            avatar=request.userInfo.get("avatarUrl", "")  # 获取头像URL，默认为空字符串
        )
        db.add(user)  # 添加到数据库会话
        db.commit()  # 提交事务
        db.refresh(user)  # 刷新对象
        
        # 创建用户设置
        settings = UserSettings(user_id=user.id)  # 创建默认用户设置
        db.add(settings)  # 添加到数据库会话
        db.commit()  # 提交事务
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 设置令牌过期时间
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires  # 用户ID作为令牌主题
    )
    
    # 返回响应
    return {
        "code": 200,
        "message": "success",
        "data": {
            "token": access_token,  # JWT访问令牌
            "userInfo": {  # 用户信息
                "id": user.id,
                "openid": user.openid,
                "nickName": user.nick_name,
                "avatar": user.avatar,
                "createdAt": user.created_at.isoformat()  # 格式化创建时间
            }
        }
    }

# 退出登录接口
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """退出登录接口
    
    处理用户退出登录请求
    注意：由于JWT是无状态的，服务端无法真正使已颁发的令牌失效
    在实际应用中，应使用令牌黑名单或Redis缓存来实现令牌失效
    
    Args:
        current_user: 当前认证用户，由get_current_user依赖项提供
        
    Returns:
        dict: 退出登录响应
    """
    # 由于JWT是无状态的，服务端无法真正使令牌失效
    # 在实际应用中，可以使用令牌黑名单或Redis缓存来实现令牌失效
    # 这里简化处理，直接返回成功
    return {
        "code": 200,
        "message": "已成功退出登录",
        "data": None
    }