# 导入必要的模块
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text  # 数据库列类型
from sqlalchemy.ext.declarative import declarative_base  # 声明式基类
from sqlalchemy.orm import relationship  # 关系管理
from datetime import datetime  # 日期时间处理
import uuid  # 生成唯一标识符

# 创建声明式基类，所有模型都将继承此基类
Base = declarative_base()


class User(Base):
    """用户模型
    
    存储用户基本信息，包括微信openid、昵称和头像
    
    Attributes:
        id: 用户唯一标识，UUID格式
        openid: 微信用户唯一标识
        nick_name: 用户昵称
        avatar: 用户头像URL
        created_at: 用户创建时间
    """
    __tablename__ = "users"  # 数据库表名

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 主键，默认生成UUID
    openid = Column(String(100), unique=True, index=True, nullable=False)  # 微信openid，唯一且建立索引
    nick_name = Column(String(100))  # 用户昵称
    avatar = Column(String(255))  # 用户头像URL
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间，默认为当前UTC时间

    # 关系定义
    settings = relationship("UserSettings", back_populates="user", uselist=False)  # 一对一关系：用户设置
    sessions = relationship("ChatSession", back_populates="user")  # 一对多关系：聊天会话


class UserSettings(Base):
    """用户设置模型
    
    存储用户个性化设置，如深色模式、自动朗读等
    
    Attributes:
        id: 设置唯一标识，UUID格式
        user_id: 关联的用户ID
        is_dark_mode: 是否启用深色模式
        auto_read: 是否启用自动朗读
        save_history: 是否保存聊天历史
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = "user_settings"  # 数据库表名

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 主键，默认生成UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 外键，关联用户表
    is_dark_mode = Column(Boolean, default=False)  # 深色模式开关，默认关闭
    auto_read = Column(Boolean, default=False)  # 自动朗读开关，默认关闭
    save_history = Column(Boolean, default=True)  # 保存历史记录开关，默认开启
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间，自动更新

    # 关系定义
    user = relationship("User", back_populates="settings")  # 多对一关系：关联用户


class ChatSession(Base):
    """聊天会话模型
    
    表示用户与AI助手之间的一个完整对话会话
    
    Attributes:
        id: 会话唯一标识，UUID格式
        user_id: 关联的用户ID
        title: 会话标题
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = "chat_sessions"  # 数据库表名

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 主键，默认生成UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 外键，关联用户表
    title = Column(String(255), default="新会话")  # 会话标题，默认为"新会话"
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间，自动更新
    
    # 关系定义
    user = relationship("User", back_populates="sessions")  # 多对一关系：关联用户
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")  # 一对多关系：聊天消息，级联删除


class ChatMessage(Base):
    """聊天消息模型
    
    存储会话中的单条消息，包括用户发送的消息和AI的回复
    
    Attributes:
        id: 消息唯一标识，UUID格式
        session_id: 关联的会话ID
        is_user: 是否为用户消息
        content: 消息内容
        created_at: 创建时间
    """
    __tablename__ = "chat_messages"  # 数据库表名

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 主键，默认生成UUID
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)  # 外键，关联会话表
    is_user = Column(Boolean, default=True)  # 消息类型：True表示用户消息，False表示AI回复
    content = Column(Text, nullable=False)  # 消息内容，文本类型
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

    # 关系定义
    session = relationship("ChatSession", back_populates="messages")  # 多对一关系：关联会话