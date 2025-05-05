import os
import sys
import time
from app import create_app
from models import db, User
from update_db import update_database
from create_admin import create_admin_user

def setup_admin():
    """
    Script để cập nhật cơ sở dữ liệu và tạo tài khoản admin
    """
    print("=" * 50)
    print("THIẾT LẬP TÀI KHOẢN ADMIN")
    print("=" * 50)
    
    # Bước 1: Cập nhật cơ sở dữ liệu
    print("\n[1/2] Đang cập nhật cơ sở dữ liệu...")
    try:
        update_database()
        print("✓ Cập nhật cơ sở dữ liệu thành công!")
    except Exception as e:
        print(f"✗ Lỗi khi cập nhật cơ sở dữ liệu: {str(e)}")
        return False
    
    # Bước 2: Tạo tài khoản admin
    print("\n[2/2] Đang tạo tài khoản admin...")
    
    # Thông tin tài khoản admin mặc định
    admin_email = "admin@gmail.com"
    admin_password = "Admin12345@"
    
    # Cho phép người dùng nhập thông tin tùy chỉnh
    use_custom = input("Bạn có muốn sử dụng thông tin tài khoản admin tùy chỉnh? (y/n, mặc định: n): ").strip().lower()
    
    if use_custom == 'y':
        admin_email = input(f"Nhập email admin (mặc định: {admin_email}): ").strip() or admin_email
        admin_password = input(f"Nhập mật khẩu admin (mặc định: {admin_password}): ").strip() or admin_password
    
    # Tạo ứng dụng Flask
    app = create_app()
    
    try:
        # Tạo tài khoản admin
        admin = create_admin_user(app, admin_email, admin_password)
        
        if admin:
            print("\n✓ Tạo tài khoản admin thành công!")
            print("\nThông tin tài khoản admin:")
            print(f"  - Email: {admin_email}")
            print(f"  - Mật khẩu: {admin_password}")
            print(f"  - Vai trò: superadmin")
        else:
            print("\n✗ Không thể tạo tài khoản admin.")
            return False
    except Exception as e:
        print(f"\n✗ Lỗi khi tạo tài khoản admin: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("THIẾT LẬP HOÀN TẤT")
    print("=" * 50)
    print("\nBạn có thể đăng nhập vào khu vực admin tại: http://localhost:3000/admin/login")
    
    return True

if __name__ == "__main__":
    success = setup_admin()
    
    # Tạm dừng để người dùng có thể đọc thông báo
    print("\nNhấn Enter để thoát...")
    input()
    
    # Trả về mã thoát
    sys.exit(0 if success else 1)
