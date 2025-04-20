-- AI聊天助手数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE ai_assistant;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY COMMENT '用户唯一标识，UUID格式',
    openid VARCHAR(100) NOT NULL UNIQUE COMMENT '微信用户唯一标识',
    nick_name VARCHAR(100) COMMENT '用户昵称',
    avatar VARCHAR(255) COMMENT '用户头像URL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_openid (openid) COMMENT '微信openid索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- 创建用户设置表
CREATE TABLE IF NOT EXISTS user_settings (
    id VARCHAR(36) PRIMARY KEY COMMENT '设置唯一标识，UUID格式',
    user_id VARCHAR(36) NOT NULL COMMENT '关联的用户ID',
    is_dark_mode BOOLEAN DEFAULT FALSE COMMENT '是否启用深色模式',
    auto_read BOOLEAN DEFAULT FALSE COMMENT '是否启用自动朗读',
    save_history BOOLEAN DEFAULT TRUE COMMENT '是否保存聊天历史',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id) COMMENT '用户ID索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户设置表';

-- 创建聊天会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) PRIMARY KEY COMMENT '会话唯一标识，UUID格式',
    user_id VARCHAR(36) NOT NULL COMMENT '关联的用户ID',
    title VARCHAR(255) DEFAULT '新会话' COMMENT '会话标题',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id) COMMENT '用户ID索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天会话表';

-- 创建聊天消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY COMMENT '消息唯一标识，UUID格式',
    session_id VARCHAR(36) NOT NULL COMMENT '关联的会话ID',
    is_user BOOLEAN DEFAULT TRUE COMMENT '消息类型：TRUE表示用户消息，FALSE表示AI回复',
    content TEXT NOT NULL COMMENT '消息内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_session_id (session_id) COMMENT '会话ID索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息表';

-- 添加一些说明
/*
数据库设计说明：
1. 所有表使用UUID作为主键，以字符串形式存储
2. 表之间的逻辑关系（不使用外键约束）：
   - user_settings.user_id -> users.id
   - chat_sessions.user_id -> users.id
   - chat_messages.session_id -> chat_sessions.id
3. 所有表都包含created_at字段记录创建时间
4. 需要跟踪更新时间的表包含updated_at字段
5. 数据完整性需要在应用层面进行控制
*/