import os
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 请确保你的项目结构里确实有这两个模块，如果没有请根据你的实际路径调整
from app.db.init_db import init_db
from app.api.resume_routes import router as resume_router

def setup_database_file():
    """
    【Zeabur 部署专用防崩溃补丁】
    在程序启动前，检查并自动将代码包自带的初始数据库同步到云端的持久化硬盘中。
    """
    target_db_path = "/data/resume.db"  # Zeabur 云端硬盘路径 (DATABASE_URL 中 4 个斜杠指向的终点)
    
    # 【修复点 1】使用绝对路径，精准定位代码目录下的 data/resume.db
    # __file__ 指向当前文件 (main.py)，向上两级目录就是 backend 根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_db_path = os.path.join(base_dir, "data", "resume.db")

    print(f"🔍 正在检查云端数据库持久化状态...")
    print(f"📂 预期源数据库路径: {source_db_path}")
    print(f"🎯 目标持久化路径: {target_db_path}")

    # 【修复点 2】无论初始数据库是否存在，都必须强行保证 /data 文件夹存在！
    # 否则后续 init_db 连接数据库时会因为没有这个文件夹而直接报错崩溃。
    try:
        os.makedirs(os.path.dirname(target_db_path), exist_ok=True)
    except Exception as e:
        print(f"⚠️ 创建持久化目录失败 (可能权限受限或已存在): {e}")

    # 如果云端持久化目录里没有数据库文件
    if not os.path.exists(target_db_path):
        print(f"⚠️ 未在持久化硬盘找到 {target_db_path}，正在执行初始化迁移...")
        # 确认代码包里确实带了初始数据库
        if os.path.exists(source_db_path):
            try:
                # 执行复制搬家
                shutil.copy2(source_db_path, target_db_path)
                print("✅ 初始数据库 (resume.db) 已成功同步到云端硬盘！")
            except Exception as e:
                print(f"❌ 复制数据库失败，错误详情: {e}")
        else:
            print(f"⚠️ 代码包中未找到初始数据库({source_db_path})，SQLAlchemy 将稍后自动创建空表。")
    else:
        print("✅ 识别到云端持久化数据库，将直接读取已有数据。")

def create_app() -> FastAPI:
    # 1. 在正式启动应用和连接数据库之前，先确保持久化数据库文件已就位
    setup_database_file()

    app = FastAPI(title="Resume Optimizer API", version="1.0.0")

    # 2. CORS 跨域配置
    # 为了防止填错，兼容 ALLOWED_ORIGINS 和 CORS_ALLOW_ORIGINS 两个环境变量名
    raw_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ALLOW_ORIGINS", "*")
    allowed_origins = raw_origins.split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. 初始化数据库连接 (此时 /data/resume.db 肯定能找到合法路径了)
    init_db()
    
    # 4. 挂载路由
    app.include_router(resume_router, prefix="/api")
    
    return app

app = create_app()