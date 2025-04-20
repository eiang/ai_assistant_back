# 导入必要的模块
from fastapi import Depends, HTTPException, status  # FastAPI相关组件
from fastapi.security import OAuth2PasswordBearer  # OAuth2密码流认证
from sqlalchemy.orm import Session  # 数据库会话
import jwt  # JWT令牌处理
from datetime import datetime, timedelta  # 日期时间处理
from typing import Optional  # 类型提示

# 导入项目内部模块
from config import SECRET_KEY, ALGORITHM  # 配置
from database import get_db  # 数据库依赖
from models import User  # 数据模型

# OAuth2认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # 配置OAuth2密码流认证，指定获取令牌的URL

# 验证令牌
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    验证JWT令牌并获取当前用户
    
    Args:
        token: JWT令牌，由OAuth2PasswordBearer依赖项提供
        db: 数据库会话，由get_db依赖项提供
        
    Returns:
        User: 当前认证用户对象
        
    Raises:
        HTTPException: 令牌无效或用户不存在时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")  # 获取用户ID
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        # JWT解码错误
        raise credentials_exception
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # 用户不存在
        raise credentials_exception
    return user