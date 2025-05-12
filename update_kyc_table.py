"""
Script để thêm cột id_card_verified, face_match, face_distance, và face_verified_at vào bảng kyc_verification
"""
from app import create_app
from models import db
from sqlalchemy import text
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database():
    """
    Thêm các cột cần thiết vào bảng kyc_verification nếu chưa tồn tại
    """
    app = create_app()
    with app.app_context():
        connection = db.engine.connect()
        
        # Danh sách các cột cần thêm
        columns = [
            {"name": "id_card_verified", "type": "BOOLEAN DEFAULT FALSE"},
            {"name": "face_match", "type": "BOOLEAN DEFAULT FALSE"},
            {"name": "face_distance", "type": "FLOAT NULL"},
            {"name": "face_verified_at", "type": "DATETIME NULL"}
        ]
        
        for column in columns:
            # Kiểm tra xem cột đã tồn tại chưa
            try:
                connection.execute(text(f"SELECT {column['name']} FROM kyc_verification LIMIT 1"))
                logger.info(f"Cột {column['name']} đã tồn tại.")
            except Exception:
                # Thêm cột nếu chưa tồn tại
                try:
                    connection.execute(text(f"ALTER TABLE kyc_verification ADD COLUMN {column['name']} {column['type']}"))
                    logger.info(f"Đã thêm cột {column['name']}.")
                except Exception as e:
                    logger.error(f"Lỗi khi thêm cột {column['name']}: {e}")
        
        logger.info("Hoàn thành cập nhật cơ sở dữ liệu.")

if __name__ == "__main__":
    logger.info("Bắt đầu cập nhật cơ sở dữ liệu...")
    update_database()
    logger.info("Kết thúc quá trình cập nhật.")
