# AI助手后端API文档

## 基础信息
- 基础URL: `http://localhost:8000/api`
- 所有请求都需要在header中携带token（除了登录接口）
- token格式: `Authorization: Bearer {token}`

## 认证相关接口

### 1. 微信登录
- **接口**: `/auth/wechat-login`
- **方法**: POST
- **描述**: 使用微信小程序登录
- **请求参数**:
  ```json
  {
    "code": "微信登录临时凭证",
    "userInfo": {
      "nickName": "用户昵称",
      "avatarUrl": "用户头像URL"
    }
  } 
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "token": "JWT访问令牌",
      "userInfo": {
        "id": "用户ID",
        "openid": "微信openid",
        "nickName": "用户昵称",
        "avatar": "用户头像",
        "createdAt": "创建时间"
      }
    }
  }
  ```
- **错误响应**:
  ```json
  {
    "code": 400,
    "message": "微信授权失败"
  }
  ```

### 2. 退出登录
- **接口**: `/auth/logout`
- **方法**: POST
- **描述**: 退出登录
- **请求头**: 需要携带token
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "已成功退出登录",
    "data": null
  }
  ```

## 用户相关接口

### 1. 获取用户信息
- **接口**: `/user/info`
- **方法**: GET
- **描述**: 获取当前用户信息和设置
- **请求头**: 需要携带token
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": "用户ID",
      "openid": "微信openid",
      "nickName": "用户昵称",
      "avatar": "用户头像",
      "createdAt": "创建时间",
      "settings": {
        "isDarkMode": true,
        "autoRead": true,
        "saveHistory": true
      }
    }
  }
  ```

## 聊天相关接口

### 1. 发送消息
- **接口**: `/chat/message`
- **方法**: POST
- **描述**: 发送消息并获取AI回复
- **请求头**: 需要携带token
- **请求参数**:
  ```json
  {
    "content": "消息内容",
    "sessionId": "会话ID（可选）"
  }
  ```
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "sessionId": "会话ID",
      "messageId": "消息ID",
      "reply": {
        "content": "AI回复内容",
        "time": "回复时间"
      }
    }
  }
  ```
- **错误响应**:
  ```json
  {
    "code": 404,
    "message": "会话不存在"
  }
  ```

## AI相关接口

### 1. 语音识别
- **接口**: `/ai/speech-to-text`
- **方法**: POST
- **描述**: 将语音文件转换为文本
- **请求头**: 需要携带token
- **请求参数**: 
  - 文件上传字段名: `audio`
  - 支持格式: mp3、wav、m4a
- **成功响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "text": "识别出的文本"
    }
  }
  ```
- **错误响应**:
  ```json
  {
    "code": 400,
    "message": "不支持的音频格式，请上传mp3、wav或m4a格式"
  }
  ```

## 错误码说明
- 200: 成功
- 400: 请求参数错误
- 401: 未授权
- 404: 资源不存在
- 500: 服务器内部错误 