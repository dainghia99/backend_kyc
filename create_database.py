"""
Script để tạo mới database và tài khoản admin
"""
import os
import sys
from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database():
    """
    Tạo mới database và các bảng cần thiết
    """
    try:
        from app import create_app
        from models import db, User, KYCVerification, IdentityInfo, UserSession
        
        logger.info("Bắt đầu tạo mới database...")
        
        # Tạo ứng dụng Flask
        app = create_app()
        
        with app.app_context():
            # Xóa database cũ nếu tồn tại
            db.drop_all()
            logger.info("Đã xóa database cũ (nếu có)")
            
            # Tạo mới database
            db.create_all()
            logger.info("Đã tạo mới database và các bảng")
            
            # Tạo thư mục uploads nếu chưa tồn tại
            uploads_dir = os.path.join(app.root_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            logger.info(f"Đã tạo thư mục uploads tại {uploads_dir}")
            
            # Tạo tài khoản admin
            create_admin_account(app)
            
        logger.info("Tạo mới database hoàn tất!")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo mới database: {str(e)}")
        return False

def create_admin_account(app):
    """
    Tạo tài khoản admin với quyền cao nhất
    """
    from models import db, User
    
    admin_email = "admin@gmail.com"
    admin_password = "Admin12345@"
    
    logger.info(f"Đang tạo tài khoản admin với email: {admin_email}")
    
    with app.app_context():
        # Kiểm tra xem tài khoản admin đã tồn tại chưa
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            logger.info(f"Tài khoản admin với email {admin_email} đã tồn tại.")
            return existing_admin
        
        # Tạo tài khoản admin mới
        hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
        admin_user = User(
            email=admin_email,
            password=hashed_password,
            role='superadmin',
            kyc_status='verified',  # Admin mặc định đã được xác minh
            kyc_verified_at=datetime.utcnow(),
            identity_verified=True,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"Đã tạo tài khoản admin thành công với email: {admin_email}")
            
            # Hiển thị thông tin tài khoản admin
            logger.info("Thông tin tài khoản admin:")
            logger.info(f"  - Email: {admin_email}")
            logger.info(f"  - Mật khẩu: {admin_password}")
            logger.info(f"  - Vai trò: superadmin")
            
            return admin_user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Lỗi khi tạo tài khoản admin: {str(e)}")
            return None

if __name__ == "__main__":
    print("=" * 50)
    print("TẠO MỚI DATABASE VÀ TÀI KHOẢN ADMIN")
    print("=" * 50)
    
    success = create_database()
    
    if success:
        print("\nTạo mới database và tài khoản admin thành công!")
        print("\nThông tin tài khoản admin:")
        print("  - Email: admin@gmail.com")
        print("  - Mật khẩu: Admin12345@")
        print("  - Vai trò: superadmin")
    else:
        print("\nTạo mới database và tài khoản admin thất bại!")
    
    print("\n" + "=" * 50)
    print("Nhấn Enter để thoát...")
    input()
    
    # Trả về mã thoát
    sys.exit(0 if success else 1)
