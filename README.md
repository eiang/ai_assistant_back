uv# AI聊天助手后端

基于Python和FastAPI开发的AI聊天助手后端服务，提供用户认证、聊天功能和AI功能等API接口。

## 项目结构

```
ai_assistant_back/
├── main.py                  # 主应用入口
├── models.py                # 数据库模型
├── config.py                # 配置管理
├── database.py              # 数据库连接
├── utils.py                 # 工具函数
├── requirements.txt         # 项目依赖
├── run.py                   # 环境启动脚本
├── routers/                 # 路由模块
│   ├── __init__.py
│   ├── auth.py              # 认证相关路由
│   ├── user.py              # 用户相关路由
│   ├── chat.py              # 聊天相关路由
│   ├── chatwithdeepseek.py  # DeepSeek AI集成
│   └── ai.py                # AI功能相关路由
├── .env.example             # 环境变量示例
└── api_documentation.md     # API文档
```

## 功能特性

- 用户认证：微信授权登录、退出登录、获取用户信息
- 聊天功能：发送消息给AI并获取回复
- AI集成：支持DeepSeek大模型接口
- 语音识别：语音转文本功能
- 多环境配置：支持开发环境和生产环境分离

## 安装与运行

1. 克隆项目

```bash
git clone <repository-url>
cd ai_assistant_back
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

复制示例配置文件并根据需要修改：

```bash
cp .env.example .env.development
# 编辑 .env.development 文件，填写相关配置
```

4. 运行服务

```bash
# 使用开发环境启动（默认）
python run.py

# 或显式指定环境
python run.py --env development
```

服务将在 http://localhost:8000 启动

## API文档

启动服务后，可以通过以下地址访问自动生成的API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

详细API说明请参考 [api_documentation.md](api_documentation.md) 文件。

## 开发说明

### 1. 微信登录配置

在`.env.development`文件中配置微信小程序信息：

```
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret
```

### 2. DeepSeek AI集成

本项目集成了DeepSeek AI大模型，使用LangChain框架进行调用。相关配置在`.env.development`中：

```
# DeepSeek API配置
MODEL_NAME=deepseek-chat
TEMPERATURE=0.5
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
```

### 3. 数据库配置

在`.env.development`文件中配置数据库连接信息：

```
DATABASE_URL=mysql+pymysql://用户名:密码@localhost:3306/ai_assistant
```

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或token已过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 配置管理

项目采用集中式配置管理，所有重要的配置项都在`config.py`文件中定义。配置分为以下几类：

1. **基础URL配置**
   - API_BASE_URL: API基础URL

2. **数据库配置**
   - DATABASE_URL: 数据库连接URL
   - DB_USER, DB_PASSWORD等细分配置

3. **JWT认证配置**
   - SECRET_KEY: JWT加密密钥
   - ALGORITHM: JWT加密算法
   - ACCESS_TOKEN_EXPIRE_MINUTES: 访问令牌过期时间

4. **微信小程序配置**
   - WECHAT_APPID: 微信小程序AppID
   - WECHAT_SECRET: 微信小程序AppSecret
   - WECHAT_LOGIN_URL: 微信登录接口URL

5. **AI服务配置**
   - AI_API_KEY: AI服务API密钥
   - AI_API_URL: AI服务接口URL
   - DEEPSEEK_API_KEY: DeepSeek API密钥
   - MODEL_NAME: 使用的模型名称
   - TEMPERATURE: 模型温度参数

6. **语音识别服务配置**
   - SPEECH_API_KEY: 语音识别服务API密钥
   - SPEECH_API_URL: 语音识别服务接口URL

7. **文件上传配置**
   - UPLOAD_DIR: 文件上传目录
   - MAX_UPLOAD_SIZE: 最大上传文件大小
   - ALLOWED_AUDIO_FORMATS: 支持的音频格式

8. **应用配置**
   - DEBUG: 调试模式
   - HOST: 主机
   - PORT: 端口

9. **API文档配置**
   - API_TITLE: API文档标题
   - API_DESCRIPTION: API文档描述

10. **跨域配置**
    - ALLOW_ORIGINS: 允许的来源
    - ALLOW_CREDENTIALS: 允许携带凭证
    - ALLOW_METHODS: 允许的HTTP方法
    - ALLOW_HEADERS: 允许的HTTP头

## 环境配置

项目支持多环境配置，包括开发环境和生产环境。

### 配置文件

系统提供了以下环境配置文件：

- `.env.example` - 示例配置文件，可以作为模板
- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置

你可以根据需要修改这些文件中的配置项。

### 启动不同环境

使用以下命令启动不同环境的服务：

```bash
# 启动开发环境（默认）
python run.py

# 或者明确指定开发环境
python run.py --env development

# 启动生产环境
python run.py --env production
```

### 添加自定义环境

如果需要添加自定义环境（如测试环境），只需创建对应的配置文件（如 `.env.testing`），并在启动时指定该环境：

```bash
# 创建测试环境配置文件
cp .env.example .env.testing
# 编辑测试环境配置...

# 通过环境变量直接指定环境
ENV=testing python main.py
```
