# 导入必要的模块
# FastAPI相关模块，用于构建API服务
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware  # 用于处理跨域资源共享
from fastapi.security import OAuth2PasswordBearer  # 用于OAuth2密码流认证
from typing import Optional  # 类型提示，表示可选参数

# 服务器和工具模块
import uvicorn  # ASGI服务器，用于运行FastAPI应用
import jwt  # JSON Web Token，用于生成和验证令牌
from datetime import datetime, timedelta  # 日期时间处理
import os  # 操作系统功能，文件路径处理等
from pydantic import BaseModel  # 数据验证和设置管理

# 数据库相关模块
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text  # SQL工具和列类型
from sqlalchemy.ext.declarative import declarative_base  # 声明式基类
from sqlalchemy.orm import sessionmaker, relationship, Session  # ORM会话和关系管理

# 其他工具模块
import uuid  # 用于生成唯一标识符
import json  # JSON数据处理

# 导入配置信息
from config import (
    DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    HOST, PORT, DEBUG, API_TITLE, API_DESCRIPTION,
    ALLOW_ORIGINS, ALLOW_CREDENTIALS, ALLOW_METHODS, ALLOW_HEADERS,
    OAUTH2_TOKEN_URL
)  # 从配置文件导入所有需要的配置

# 创建数据库引擎和会话
engine = create_engine(DATABASE_URL)  # 创建SQLAlchemy引擎实例
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # 创建会话工厂
Base = declarative_base()  # 创建模型基类

# 创建FastAPI应用
app = FastAPI(title=API_TITLE, description=API_DESCRIPTION)  # 创建应用实例，设置API文档标题和描述

# 配置CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,  # 添加CORS中间件
    allow_origins=ALLOW_ORIGINS,  # 允许的来源
    allow_credentials=ALLOW_CREDENTIALS,  # 允许携带凭证
    allow_methods=ALLOW_METHODS,  # 允许的HTTP方法
    allow_headers=ALLOW_HEADERS,  # 允许的HTTP头
)

# OAuth2认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH2_TOKEN_URL)  # 配置OAuth2密码流认证，指定获取令牌的URL

# 导入路由模块
from routers import auth, user, chat, ai, chatwithdeepseek

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["认证"])  # 认证相关路由，如登录、注册
app.include_router(user.router, prefix="/user", tags=["用户"])  # 用户相关路由，如获取用户信息
app.include_router(chat.router, prefix="/chat", tags=["聊天"])  # 聊天相关路由，如发送消息
app.include_router(ai.router, prefix="/ai", tags=["AI功能"])  # AI功能路由，如语音识别

# 主入口
if __name__ == "__main__":
    # 创建数据库表，如果表不存在则创建
    Base.metadata.create_all(bind=engine)
    # 启动服务
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)