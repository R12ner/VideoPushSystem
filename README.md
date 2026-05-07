# VideoPushSystem 开发与部署文档

本文档基于当前仓库代码结构整理，包含模块说明、支付部署、本地非 Docker 开发调试、Docker 部署与代码同步、数据库与 Navicat 连接等内容。

---

## 1. 项目概览

**项目名称**：VideoPushSystem  
**技术栈**：  
- 后端：Flask + SQLAlchemy + MySQL  
- 前端：Vue 3 + Vite + Pinia + Element Plus  
- 推荐：召回模型（Two-Tower 召回）  
- 支付：支付宝沙箱（python-alipay-sdk）  
- 部署：Docker Compose（MySQL + Backend + Frontend + Cloudflared）

**核心访问入口**：  
- 前端：`http://localhost:5173`（本地开发）/ `http://localhost:8080`（Docker）  
- 后端：`http://localhost:5000`（本地开发）  
- 后端文档：`http://localhost:5000/api/docs`  

---

## 2. 目录结构

```
VideoPushSystem/
  backend/                 # Flask 后端
    app/
      api/                 # API 路由
      models.py            # 数据模型
      services/            # 推荐模型服务
      static/              # 上传视频/封面/字幕等
    run.py                 # 后端启动入口
    requirements.txt       # 后端依赖
    .env                   # 后端本地环境配置
    seed_data.py           # 初始化/造数据脚本
    train_two_tower.py     # 训练推荐模型
  frontend/                # Vue 前端
    src/
      api/                 # API 请求封装
      views/               # 页面
      components/          # 组件
      store/               # Pinia
    vite.config.js         # Vite 配置（含本地代理）
  data/                    # Docker MySQL 数据卷
  docker-compose.yml       # Docker 编排
  .env                     # Docker Compose 环境变量
```

---

## 3. 模块说明

### 3.1 后端模块

API 路由注册位置：`backend/app/__init__.py`

- `app/api/auth.py`  
  登录、注册、发送邮箱验证码、密码重置流程。

- `app/api/user.py`  
  用户资料、关注、个人主页、历史/收藏等。

- `app/api/video.py`  
  视频上传、发布、审核状态、详情、操作（点赞/收藏/观看）、创作者统计。

- `app/api/recommend.py`  
  首页推荐与召回逻辑（含 Two-Tower 召回 + 热门兜底）。

- `app/api/interaction.py`  
  评论、回复、点赞、置顶等。

- `app/api/playlist.py`  
  播放列表增删改查。

- `app/api/admin.py`  
  管理后台：视频审核、用户管理、封禁、统计。

- `app/api/pay.py`  
  支付宝支付创建、异步回调、订单查询。

- `app/services/recall_service.py`  
  Two-Tower 召回模型加载与推理服务，依赖 `train_two_tower.py` 生成的模型文件。

### 3.2 前端模块

前端入口目录：`frontend/src`

- `views/`  
  页面级：首页、详情页、频道页、工作室、后台、支付等。

- `components/`  
  通用组件：视频编辑弹窗、播放器、裁剪组件、徽章等。

- `api/`  
  Axios 封装 + 各模块 API 请求。

- `store/`  
  Pinia 用户状态管理。

---

## 4. 环境配置说明

### 4.1 后端本地环境变量（非 Docker）

文件：`backend/.env`  
关键字段：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=video_push_db

SITE_DOMAIN=http://localhost:5173

MAIL_SERVER=...
MAIL_USERNAME=...
MAIL_PASSWORD=...

ALIPAY_APPID=...
ALIPAY_PUBLIC_KEY=...
ALIPAY_PRIVATE_KEY=...
ALIPAY_NOTIFY_URL=...
ALIPAY_RETURN_URL=...

ZHIPU_API_KEY=...
ZHIPU_MODEL=glm-4-flash-250414
ZHIPU_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
```

### 4.2 Docker Compose 环境变量

文件：`.env`（项目根目录）  
用于 `docker-compose.yml`：

```
MYSQL_ROOT_PASSWORD=123456
MYSQL_DATABASE=video_push_db

DB_HOST=db
DB_USER=root
DB_PASSWORD=123456
SITE_DOMAIN=https://你的域名

CLOUDFLARE_TUNNEL_TOKEN=...
ZHIPU_API_KEY=...
ZHIPU_MODEL=glm-4-flash-250414
ZHIPU_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
```

---

## 5. 本地开发（非 Docker）

### 5.1 前置依赖

1. Node.js 18+  
2. Python 3.10+  
3. MySQL 8.0  

### 5.2 数据库准备

1. 创建数据库：
```
CREATE DATABASE video_push_db DEFAULT CHARACTER SET utf8mb4;
```

2. 后端启动时会自动 `db.create_all()` 创建表。  

3. 可选初始化数据：
```
cd backend
python seed_data.py
```

### 5.3 后端启动（非 Docker）

```
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```

后端启动成功后：
- API 基础地址：`http://localhost:5000/api`
- 文档：`http://localhost:5000/api/docs`

### 5.4 前端启动（非 Docker）

```
cd frontend
npm install
npm run dev
```

前端默认运行在：`http://localhost:5173`  
Vite 代理配置（`frontend/vite.config.js`）将 `/api` 与 `/static` 转发到后端 `http://localhost:5000`。

---

## 6. 支付接口部署（支付宝）

### 6.1 现有支付流程

后端 `app/api/pay.py`：
1. `/api/pay/create` 创建订单并返回支付链接（沙箱网关）。
2. 用户跳转支付。
3. 支付完成后支付宝异步回调 `/api/pay/notify`。
4. 前端可轮询 `/api/pay/query` 查询订单状态。

### 6.2 部署要点

1. `ALIPAY_NOTIFY_URL` 必须是公网可访问地址。  
2. `SITE_DOMAIN` 应该指向可访问的前端域名（用于支付完成后的回跳）。
3. 当前代码使用**支付宝沙箱网关**：
```
https://openapi-sandbox.dl.alipaydev.com/gateway.do
```
如需生产环境，需要替换为正式网关并配置正式应用密钥。

### 6.3 推荐配置（本地联调）

- 使用内网穿透（例如 Cloudflared / Ngrok）。  
- 将 `ALIPAY_NOTIFY_URL` 设置为公网域名，例如：
```
https://your-domain.com/api/pay/notify
```
- 将 `ALIPAY_RETURN_URL` 设置为：
```
http://localhost:5173/pay/result
```

---

## 7. Docker 部署

### 7.1 启动 Docker Compose

```
docker compose up -d --build
```

### 7.2 服务与端口

- MySQL：`127.0.0.1:3306`  
- Backend：`127.0.0.1:5000`  
- Frontend：`127.0.0.1:8080`

### 7.3 静态文件持久化

后端上传文件目录挂载：
```
./backend/app/static -> /app/app/static
```
视频、封面、字幕等文件不会丢失。

### 7.4 推荐模型

Docker 启动时会加载：
```
backend/app/services/model_data/recall_data.pkl
```

若文件不存在，需要在宿主机运行：
```
cd backend
python train_two_tower.py
```

---

## 8. 修改代码同步到 Docker

当前 `docker-compose.yml` **没有**挂载后端/前端源码，因此修改代码后必须重新构建镜像。

推荐流程：

```
docker compose build backend frontend
docker compose up -d --build backend frontend
```

或者全量重建：
```
docker compose up -d --build
```

如需更快开发调试，可自行调整 `docker-compose.yml` 将源码目录映射到容器内（不建议生产环境使用）。

---

## 9. Navicat 连接数据库

### 9.1 本地非 Docker

- Host: `127.0.0.1`  
- Port: `3306`  
- User: `root`  
- Password: `123456`（以 `backend/.env` 为准）  
- Database: `video_push_db`  

### 9.2 Docker 模式

Docker 映射为 `127.0.0.1:3306`，连接方式同上。  
如果你在服务器远程部署，请把 `docker-compose.yml` 中端口映射改为开放地址（注意安全）。

---

## 10. 常见问题排查

1. **前端请求 404**  
确认请求是 `/api/...`，前端 `request.js` 已配置 baseURL `/api`。

2. **跨域问题**  
后端 CORS 仅允许 `http://localhost:5173` 与 `http://127.0.0.1:5173`。  
若需要其他域名，请修改 `backend/app/__init__.py` 中的 CORS 配置。

3. **首页看不到视频**  
需满足：
```
status = 1（审核通过）
visibility = public（公开）
```

4. **推荐模型无数据**  
确认 `backend/app/services/model_data/recall_data.pkl` 是否存在。

---

## 11. 推荐的开发流程

1. 非 Docker 模式下完成开发调试。  
2. 测试通过后，重新构建 Docker 镜像。  
3. 上线后通过域名与公网回调验证支付流程。  

---

## 12. 安全建议

- `.env` 中包含密钥，建议只保留 `.env.example` 并在部署时注入真实值。  
- 支付宝私钥、邮箱密码等敏感数据不要提交到 Git。  
- 线上部署时建议使用反向代理（Nginx/1Panel）并开启 HTTPS。
沙盒账号iklgec5101@sandbox.com 密码111111