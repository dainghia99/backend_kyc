from flask import Flask
from flask_cors import CORS
from models import db
from config import config
from routes.auth import auth_bp
from routes.kyc import kyc_bp
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
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')
    
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
    
    @app.route('/')
    def index():
        return {"message": "KYC API Server"}
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)


