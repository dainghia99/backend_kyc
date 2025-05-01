from flask import Flask
from flask_cors import CORS
from models import db
from config import config
from routes.auth import auth_bp
from routes.kyc import kyc_bp
from routes.ocr_direct import ocr_bp
from middleware.error_handler import register_error_handlers
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_name='development'):

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Set up logging
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Custom RotatingFileHandler to handle file access issues
    class SafeRotatingFileHandler(RotatingFileHandler):
        def doRollover(self):
            try:
                # Try the normal rollover
                super().doRollover()
            except (PermissionError, OSError) as e:
                # If we can't roll over, just continue without rolling
                print(f"Warning: Could not rotate log file: {e}")
                # Try to at least write to the file
                try:
                    # Reopen the file if needed
                    if self.stream.closed:
                        self.stream = self._open()
                except Exception as e:
                    print(f"Error reopening log file: {e}")

    try:
        # Use the safer handler
        file_handler = SafeRotatingFileHandler(
            'logs/app.log',
            maxBytes=10240,
            backupCount=10,
            delay=True,  # Delay file opening until first log
            encoding='utf-8'  # Sử dụng mã hóa UTF-8 cho file log
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

        # Also log to console in development
        if app.config['DEBUG']:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            console_handler.setLevel(logging.INFO)
            app.logger.addHandler(console_handler)

        app.logger.info('Application startup')
    except Exception as e:
        print(f"Warning: Could not set up logging: {e}")
        # Set up a basic console logger as fallback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup (with fallback logging)')

    # Initialize CORS
    CORS(app, resources={
        r"/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(kyc_bp, url_prefix='/kyc')
    app.register_blueprint(ocr_bp, url_prefix='/ocr')

    @app.route('/')
    def index():
        return {"message": "KYC API Server"}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)


