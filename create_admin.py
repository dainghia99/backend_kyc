from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User
from config import config
import sys

def create_admin_user(app, email="admin@gmail.com", password="Admin12345@"):
    """
    Tạo tài khoản admin mặc định với quyền cao nhất
    """
    with app.app_context():
        # Kiểm tra xem tài khoản admin đã tồn tại chưa
        existing_admin = User.query.filter_by(email=email).first()

        if existing_admin:
            print(f"Tài khoản admin với email {email} đã tồn tại.")

            # Cập nhật quyền nếu chưa phải là superadmin
            if existing_admin.role != 'superadmin':
                existing_admin.role = 'superadmin'
                db.session.commit()
                print(f"Đã cập nhật quyền của tài khoản {email} thành superadmin.")

            return existing_admin

        # Tạo tài khoản admin mới
        # Sử dụng thuật toán pbkdf2:sha256 thay vì scrypt để đảm bảo tương thích
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        admin_user = User(
            email=email,
            password=hashed_password,
            role='superadmin',
            kyc_status='verified'  # Admin mặc định đã được xác minh
        )

        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"Đã tạo tài khoản admin thành công với email: {email}")
            return admin_user
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi tạo tài khoản admin: {str(e)}")
            return None

if __name__ == "__main__":
    # Tạo ứng dụng Flask
    app = Flask(__name__)
    app.config.from_object(config['development'])
    config['development'].init_app(app)

    # Khởi tạo database
    db.init_app(app)

    # Lấy thông tin đăng nhập từ tham số dòng lệnh (nếu có)
    email = "admin@gmail.com"
    password = "Admin12345@"

    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]

    # Tạo tài khoản admin
    admin = create_admin_user(app, email, password)

    if admin:
        print(f"Tài khoản admin đã sẵn sàng sử dụng:")
        print(f"Email: {admin.email}")
        print(f"Vai trò: {admin.role}")
