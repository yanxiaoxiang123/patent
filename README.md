# 智能专利辅助审核系统 (IPRS)

基于 AI 技术的专利文档智能审核平台，帮助专利代理人提高审核效率和文档质量。

## 🎯 项目概述

### 核心功能
- **文档上传与解析**: 支持 .docx 和 .pdf 格式，智能分段解析
- **AI 形式审查**: 基于 Ollama (Qwen3-7b) 的快速错别字、格式检查
- **深度逻辑分析**: 基于 Coze Agent 的权利要求支持性分析
- **交互式编辑**: 实时高亮错误，一键采纳建议
- **报告导出**: 生成专业的审核报告

### 技术架构
- **后端**: Python FastAPI + MySQL + SQLAlchemy
- **前端**: Vue 3 + Element Plus + Vite
- **AI 服务**: 本地 Ollama + 云端 Coze API

## 📁 项目结构

```
patent/
├── patent/                 # Python 虚拟环境
├── backend/                # 后端代码
│   ├── app/
│   │   ├── main.py        # FastAPI 应用入口
│   │   ├── models/        # SQLAlchemy 数据模型
│   │   ├── api/           # API 路由
│   │   ├── schemas/       # Pydantic 数据模式
│   │   ├── core/          # 核心功能
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── .env              # 环境变量配置
│   ├── requirements.txt  # Python 依赖
│   └── run.py            # 启动脚本
├── database/              # 数据库脚本
│   ├── create_tables.sql
│   └── insert_test_data.sql
├── CLAUDE.md             # Claude 项目配置
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- MySQL 8.0+
- Ollama (已安装 Qwen3-7b 模型)

### 1. 激活虚拟环境
```bash
# Windows
patent\Scripts\activate

# Linux/Mac
source patent/bin/activate
```

### 2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置数据库
- 确保 MySQL 服务已启动
- 用户名: your-db-user, 密码: your-db-password
- 执行 `python ../init_database.py` 初始化数据库

### 4. 配置环境变量
编辑 `backend/.env` 文件：
```
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/iprs
TOKEN_SECRET=your-secure-secret-key
COZE_API_KEY=your-coze-api-key-here
```

### 5. 启动后端服务
```bash
cd backend
python run.py
```

服务将在 http://localhost:8000 启动

### 6. API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 数据库设计

### 用户表 (users)
- id, username, password_hash, role, created_at, updated_at

### 文档表 (documents)
- id, user_id, title, file_path, file_type, parsed_content, status

### 审核记录表 (review_records)
- id, document_id, review_type, model_version, result_json, score

## 🔧 开发指南

### 后端开发
- 使用 SQLAlchemy ORM 进行数据库操作
- 采用异步编程模式
- 遵循 RESTful API 设计规范
- 使用 Pydantic 进行数据验证

### 前端开发 (待实现)
- Vue 3 Composition API
- Element Plus 组件库
- Pinia 状态管理
- Axios HTTP 客户端

## 🤖 AI 集成

### 本地 Ollama
- 模型: Qwen3-7b
- 用途: 快速形式检查
- 端点: http://localhost:11434

### 云端 Coze
- API: 需配置 API Key
- 用途: 深度逻辑分析
- 特性: 支持联网搜索、多步推理

## 📝 API 接口

### 认证接口
- POST /api/auth/login - 用户登录
- POST /api/auth/register - 用户注册

### 文档管理
- GET /api/documents - 获取文档列表
- POST /api/documents/upload - 上传文档
- GET /api/documents/{id} - 获取文档详情

### 审核接口
- POST /api/review/formal - 形式审查
- GET /api/review/deep/stream - 深度分析 (流式)

## 🔒 测试账号

- 管理员: admin / (见 .env 配置)
- 普通用户: lizhuanyuan / (见 .env 配置)

## 📋 开发计划

- [x] 项目环境搭建
- [x] 数据库设计与创建
- [x] FastAPI 基础框架
- [x] SQLAlchemy 模型
- [ ] 用户认证 API
- [ ] 文档上传与解析
- [ ] AI 适配器
- [ ] 前端界面
- [ ] 流式 AI 响应
- [ ] 报告导出

## 🐛 问题排查

### 数据库连接问题
1. 检查 MySQL 服务是否启动
2. 确认用户名密码正确
3. 验证数据库是否已创建

### AI 服务问题
1. Ollama 服务是否启动: `ollama list`
2. Coze API Key 是否有效
3. 网络连接是否正常

## 📞 支持

如有问题请参考项目文档或联系开发团队。