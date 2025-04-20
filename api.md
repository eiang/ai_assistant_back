# AI聊天助手后端API文档

## 概述
这是一个基于python+fastapi的后端项目，我的本地测试数据库连接url：jdbc:mysql://localhost:3306
本文档详细描述了AI聊天助手前端应用所需的后端API接口。这些接口包括用户认证、聊天功能、设置管理以及AI功能等方面。

## 基础信息

- 基础URL: `https://api.example.com/v1`
- 所有请求和响应均使用JSON格式
- 认证方式: Bearer Token (JWT)
- 错误响应格式:
  ```json
  {
    "code": 400,
    "message": "错误描述",
    "data": null
  }
  ```
- 成功响应格式:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": { ... }
  }
  ```

## 1. 用户认证接口

### 1.1 微信授权登录

**接口**: `POST /auth/wechat-login`

**描述**: 通过微信授权登录系统

**请求参数**:
```json
{
  "code": "string", // 微信授权返回的临时code
  "userInfo": {
    "nickName": "string",
    "avatarUrl": "string"
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "id": "string",
      "openid": "string",
      "nickName": "string",
      "avatar": "string",
      "createdAt": "2023-04-01T12:00:00Z"
    }
  }
}
```

### 1.2 退出登录

**接口**: `POST /auth/logout`

**描述**: 用户退出登录

**请求头**: 
- Authorization: Bearer {token}

**响应**:
```json
{
  "code": 200,
  "message": "已成功退出登录",
  "data": null
}
```

### 1.3 获取用户信息

**接口**: `GET /user/info`

**描述**: 获取当前登录用户的详细信息

**请求头**: 
- Authorization: Bearer {token}

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "string",
    "openid": "string",
    "nickName": "string",
    "avatar": "string",
    "createdAt": "2023-04-01T12:00:00Z",
    "settings": {
      "isDarkMode": false,
      "autoRead": false,
      "saveHistory": true
    }
  }
}
```

## 2. 聊天功能接口

### 2.1 发送消息

**接口**: `POST /chat/message`

**描述**: 发送消息给AI并获取回复

**请求头**: 
- Authorization: Bearer {token}

**请求参数**:
```json
{
  "content": "string", // 用户发送的消息内容
  "sessionId": "string" // 可选，会话ID，如果为空则创建新会话
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessionId": "string", // 会话ID
    "messageId": "string", // 消息ID
    "reply": {
      "content": "string", // AI回复内容
      "time": "2023-04-01T12:01:30Z"
    }
  }
}
```






## 3. AI功能接口

### 3.1 语音识别

**接口**: `POST /ai/speech-to-text`

**描述**: 将语音转换为文本

**请求头**: 
- Authorization: Bearer {token}
- Content-Type: multipart/form-data

**请求参数**:
```
audio: [二进制音频文件] // 支持格式: mp3, wav, m4a
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "text": "识别出的文本内容"
  }
}
```
## 4. 错误码说明

| 错误码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或token已过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 5. 开发建议

1. 所有API请求应添加适当的错误处理
2. 对于聊天功能，建议实现消息发送失败重试机制
3. 对于语音相关功能，需要处理各种音频格式和质量问题
4. 实现适当的缓存机制，减少不必要的网络请求
5. 对于敏感操作（如清空聊天记录），前端应添加二次确认