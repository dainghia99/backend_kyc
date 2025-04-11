from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes.auth import auth_bp
from routes.kyc import kyc_bp

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(kyc_bp, url_prefix='/api/kyc')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)


