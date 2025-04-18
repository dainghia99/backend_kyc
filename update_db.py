from app import create_app
from models import db
import pymysql
from sqlalchemy import text

def update_database():
    app = create_app()
    with app.app_context():
        # Kết nối trực tiếp đến cơ sở dữ liệu
        connection = db.engine.connect()
        
        # Kiểm tra xem cột blink_count đã tồn tại chưa
        try:
            connection.execute(text("SELECT blink_count FROM kyc_verification LIMIT 1"))
            print("Cột blink_count đã tồn tại.")
        except Exception:
            # Thêm cột blink_count nếu chưa tồn tại
            try:
                connection.execute(text("ALTER TABLE kyc_verification ADD COLUMN blink_count INT NULL"))
                print("Đã thêm cột blink_count.")
            except Exception as e:
                print(f"Lỗi khi thêm cột blink_count: {e}")
        
        # Kiểm tra xem cột attempt_count đã tồn tại chưa
        try:
            connection.execute(text("SELECT attempt_count FROM kyc_verification LIMIT 1"))
            print("Cột attempt_count đã tồn tại.")
        except Exception:
            # Thêm cột attempt_count nếu chưa tồn tại
            try:
                connection.execute(text("ALTER TABLE kyc_verification ADD COLUMN attempt_count INT DEFAULT 0"))
                print("Đã thêm cột attempt_count.")
            except Exception as e:
                print(f"Lỗi khi thêm cột attempt_count: {e}")
        
        # Kiểm tra xem cột last_attempt_at đã tồn tại chưa
        try:
            connection.execute(text("SELECT last_attempt_at FROM kyc_verification LIMIT 1"))
            print("Cột last_attempt_at đã tồn tại.")
        except Exception:
            # Thêm cột last_attempt_at nếu chưa tồn tại
            try:
                connection.execute(text("ALTER TABLE kyc_verification ADD COLUMN last_attempt_at DATETIME NULL"))
                print("Đã thêm cột last_attempt_at.")
            except Exception as e:
                print(f"Lỗi khi thêm cột last_attempt_at: {e}")
        
        # Kiểm tra xem cột rejection_reason đã tồn tại chưa
        try:
            connection.execute(text("SELECT rejection_reason FROM kyc_verification LIMIT 1"))
            print("Cột rejection_reason đã tồn tại.")
        except Exception:
            # Thêm cột rejection_reason nếu chưa tồn tại
            try:
                connection.execute(text("ALTER TABLE kyc_verification ADD COLUMN rejection_reason VARCHAR(200) NULL"))
                print("Đã thêm cột rejection_reason.")
            except Exception as e:
                print(f"Lỗi khi thêm cột rejection_reason: {e}")
        
        connection.close()
        print("Cập nhật cơ sở dữ liệu hoàn tất.")

if __name__ == "__main__":
    update_database()
