import os
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 请确保你的项目目录结构中包含 app.db 和 app.api 模块
from app.db.init_db import init_db
from app.api.resume_routes import router as resume_router

def setup_database_file():
    """
    【Zeabur 部署专用】初始化数据库文件
    自动将代码包内的初始数据库同步到持久化硬盘 /data 目录
    """
    target_db_path = "/data/resume.db"
    # 获取当前文件所在目录的父目录的父目录，即 backend 根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_db_path = os.path.join(base_dir, "data", "resume.db")

    # 强制创建 /data 目录，防止因目录不存在导致程序启动崩溃
    try:
        os.makedirs(os.path.dirname(target_db_path), exist_ok=True)
    except Exception as e:
        print(f"⚠️ 无法创建目录: {e}")

    if not os.path.exists(target_db_path):
        if os.path.exists(source_db_path):
            try:
                shutil.copy2(source_db_path, target_db_path)
                print(f"✅ 成功将初始数据库同步至: {target_db_path}")
            except Exception as e:
                print(f"❌ 数据库同步失败: {e}")
        else:
            print(f"⚠️ 未找到源数据库文件 {source_db_path}，将由 SQLAlchemy 自动创建空表")
    else:
        print("✅ 检测到已存在的持久化数据库文件")

def create_app() -> FastAPI:
    # 1. 预处理数据库文件
    setup_database_file()
    
    app = FastAPI(title="Resume Optimizer API", version="1.0.0")

    # 2. 核心修复：动态 CORS 配置逻辑
    # 优先读取 ALLOWED_ORIGINS 环境变量（例如：https://zxf-resume.zeabur.app）
    raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
    
    if raw_origins:
        # 支持逗号分隔多个域名
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        # 当指定具体域名时，允许 credentials (解决 502/CORS 冲突)
        allow_credentials = True 
    else:
        # 如果没有配置环境变量，默认允许所有
        # 注意：使用 "*" 时 allow_credentials 必须为 False，否则 FastAPI 会报错导致崩溃
        origins = ["*"]
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. 执行数据库初始化
    init_db()
    
    # 4. 挂载业务路由
    app.include_router(resume_router, prefix="/api")
    
    return app

app = create_app()