# 导入必要的模块
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 导入配置
from config import DATABASE_URL

# 创建数据库引擎和会话
engine = create_engine(DATABASE_URL)  # 创建SQLAlchemy引擎实例
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # 创建会话工厂
Base = declarative_base()  # 创建模型基类

# 依赖项：获取数据库会话
def get_db():
    """创建数据库会话依赖项
    
    每个请求创建一个新的数据库会话，请求结束后关闭会话
    使用yield使其成为一个依赖生成器，确保资源正确释放
    
    Returns:
        Session: SQLAlchemy数据库会话
    """
    db = SessionLocal()  # 创建新的数据库会话
    try:
        yield db  # 返回数据库会话
    finally:
        db.close()  # 请求结束后关闭会话