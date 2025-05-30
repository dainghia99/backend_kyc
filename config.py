import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/kyc.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_VIDEO_FILE_SIZE = 16 * 1024 * 1024 # 16MB max video file size
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'webm'}

    # Session configuration
    SESSION_LIFETIME = timedelta(days=7)

    # CORS configuration
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:19006', 'http://192.168.1.7:19006', '*'] 

    # KYC configuration
    MIN_BLINK_COUNT = int(os.environ.get('MIN_BLINK_COUNT', 3))  # Chỉ yêu cầu 3 nháy mắt
    MIN_LIVENESS_SCORE = float(os.environ.get('MIN_LIVENESS_SCORE', 0.3))  # Giảm ngưỡng điểm số xuống cực thấp để dễ vượt qua
    MAX_VIDEO_FILE_SIZE = int(os.environ.get('MAX_VIDEO_FILE_SIZE', 16 * 1024 * 1024)) # 16MB max video file size

    # Face verification configuration
    FACE_MATCH_TOLERANCE = float(os.environ.get('FACE_MATCH_TOLERANCE', 0.45))  

    @staticmethod
    def init_app(app):
        # Ensure upload directory exists
        upload_path = os.path.join(app.root_path, Config.UPLOAD_FOLDER)
        os.makedirs(upload_path, exist_ok=True)
        app.config['UPLOAD_FOLDER'] = upload_path
        print(f"Upload directory: {upload_path}")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Override these with secure values in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
