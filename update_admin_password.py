from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User
from config import config

def update_admin_password(app, email="admin@gmail.com", password="Admin12345@"):
    """
    Cập nhật mật khẩu của tài khoản admin với thuật toán mã hóa pbkdf2:sha256
    """
    with app.app_context():
        # Tìm tài khoản admin
        admin = User.query.filter_by(email=email).first()
        
        if not admin:
            print(f"Không tìm thấy tài khoản admin với email {email}")
            return None
        
        # Cập nhật mật khẩu với thuật toán pbkdf2:sha256
        admin.password = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            db.session.commit()
            print(f"Đã cập nhật mật khẩu cho tài khoản admin {email} thành công")
            return admin
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi cập nhật mật khẩu: {str(e)}")
            return None

if __name__ == "__main__":
    # Tạo ứng dụng Flask
    app = Flask(__name__)
    app.config.from_object(config['development'])
    config['development'].init_app(app)
    
    # Khởi tạo database
    db.init_app(app)
    
    # Cập nhật mật khẩu admin
    admin = update_admin_password(app)
    
    if admin:
        print(f"Tài khoản admin đã được cập nhật:")
        print(f"Email: {admin.email}")
        print(f"Vai trò: {admin.role}")
