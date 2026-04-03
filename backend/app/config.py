import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
        
    # 密钥
    SECRET_KEY = '8f4b2e1d9a3c5e7b1a2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v'
    
    # 数据库连接配置
    db_host = os.getenv('DB_HOST', 'localhost')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:123456@{db_host}/video_push_db'
    
    
    # 关闭追踪，节省内存
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件保存路径
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/uploads')


    # 邮件配置
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # 支付宝沙盒配置
    ALIPAY_APPID = os.getenv("ALIPAY_APPID")
    ALIPAY_DEBUG = True
    site_domain = os.getenv('SITE_DOMAIN', 'http://localhost:5173')
    
    ALIPAY_RETURN_URL = f"{site_domain}/pay/result"
    
    ALIPAY_NOTIFY_URL = "https://pay.aeasywink.top/api/pay/notify" 

    # 读取私钥
    ALIPAY_PRIVATE_KEY_STRING = os.getenv("ALIPAY_PRIVATE_KEY")
    
    # 读取公钥
    ALIPAY_PUBLIC_KEY_STRING = os.getenv("ALIPAY_PUBLIC_KEY")

    # AI 总结配置
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
    ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash-250414")
    ZHIPU_API_URL = os.getenv("ZHIPU_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
    ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")
