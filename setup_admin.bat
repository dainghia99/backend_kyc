@echo off
echo Cập nhật cơ sở dữ liệu...
python update_db.py

echo Tạo tài khoản admin...
python create_admin.py admin@gmail.com Admin12345@

echo Hoàn tất! Tài khoản admin đã được tạo:
echo Email: admin@gmail.com
echo Mật khẩu: Admin12345@
echo Vai trò: superadmin
pause
