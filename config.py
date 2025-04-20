# 配置文件
import os
import sys
from dotenv import load_dotenv

# 确定当前环境
ENV = os.getenv("ENV", "development")

# 根据环境加载对应的.env文件
env_file = f".env.{ENV}"
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"已加载 {env_file} 配置文件")
else:
    # 如果特定环境的配置文件不存在，尝试加载.env文件
    if os.path.exists(".env"):
        load_dotenv()
        print("已加载 .env 配置文件")
    else:
        print(f"警告: 配置文件 {env_file} 或 .env 不存在，使用默认配置")

# 基础URL配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# 数据库配置 - 删除密码的硬编码
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 默认为空，必须通过环境变量提供
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ai_assistant")
# 构建数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# JWT认证配置 - 使用随机生成的密钥作为默认值
import secrets
DEFAULT_SECRET_KEY = secrets.token_hex(32)  # 生成随机密钥
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

# 微信小程序配置 - 移除硬编码的AppID和Secret
WECHAT_APPID = os.getenv("WECHAT_APPID", "")  # 默认为空，必须通过环境变量提供
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "")  # 默认为空，必须通过环境变量提供
WECHAT_LOGIN_URL = os.getenv("WECHAT_LOGIN_URL", "https://api.weixin.qq.com/sns/jscode2session")

# AI服务配置
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")

# 语音识别服务配置
SPEECH_API_KEY = os.getenv("SPEECH_API_KEY", "")
SPEECH_API_URL = os.getenv("SPEECH_API_URL", "")

# 文件上传配置
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
ALLOWED_AUDIO_FORMATS = os.getenv("ALLOWED_AUDIO_FORMATS", "audio/mp3,audio/wav,audio/x-m4a").split(",")

# 应用配置
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# API文档配置
API_TITLE = os.getenv("API_TITLE", "AI聊天助手API")
API_DESCRIPTION = os.getenv("API_DESCRIPTION", "AI聊天助手后端API")

# 跨域配置
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "True").lower() == "true"
ALLOW_METHODS = os.getenv("ALLOW_METHODS", "*").split(",")
ALLOW_HEADERS = os.getenv("ALLOW_HEADERS", "*").split(",")

# 认证相关配置
OAUTH2_TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL", "token")

# 系统路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 打印当前环境
print(f"当前运行环境: {ENV}")
if ENV == "development":
    print("调试模式已启用") if DEBUG else print("调试模式已禁用")

# 检查关键配置是否已设置
if not WECHAT_APPID or not WECHAT_SECRET:
    print("警告: 微信小程序配置(WECHAT_APPID, WECHAT_SECRET)未设置，微信登录功能可能无法正常工作")

if not DB_PASSWORD and not os.getenv("DATABASE_URL"):
    print("警告: 数据库密码未设置，请在环境变量中配置DB_PASSWORD或DATABASE_URL")

if SECRET_KEY == DEFAULT_SECRET_KEY:
    print("警告: 正在使用自动生成的SECRET_KEY，重启应用后令牌将失效，请在环境变量中配置SECRET_KEY")