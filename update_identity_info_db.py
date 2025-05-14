"""
Script để cập nhật cấu trúc bảng identity_info trong database
"""
from app import create_app
from models import db
from sqlalchemy import text
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_identity_info_db():
    """
    Cập nhật cấu trúc bảng identity_info trong database
    """
    app = create_app()
    with app.app_context():
        connection = db.engine.connect()
        
        try:
            # Kiểm tra xem bảng identity_info có tồn tại không
            connection.execute(text("SHOW TABLES LIKE 'identity_info'"))
            logger.info("Kiểm tra bảng identity_info")
            
            # Kiểm tra các cột cần xóa
            try:
                # Kiểm tra xem cột residence_address có tồn tại không
                connection.execute(text("SHOW COLUMNS FROM identity_info LIKE 'residence_address'"))
                logger.info("Cột residence_address tồn tại, tiến hành xóa...")
                connection.execute(text("ALTER TABLE identity_info DROP COLUMN residence_address"))
                logger.info("Đã xóa cột residence_address")
            except Exception as e:
                logger.info(f"Cột residence_address không tồn tại hoặc có lỗi: {e}")
            
            # Kiểm tra xem cột birth_place có tồn tại không
            try:
                connection.execute(text("SHOW COLUMNS FROM identity_info LIKE 'birth_place'"))
                logger.info("Cột birth_place tồn tại, tiến hành xóa...")
                connection.execute(text("ALTER TABLE identity_info DROP COLUMN birth_place"))
                logger.info("Đã xóa cột birth_place")
            except Exception as e:
                logger.info(f"Cột birth_place không tồn tại hoặc có lỗi: {e}")
            
            # Kiểm tra các cột cần thiết
            required_columns = [
                'id', 'user_id', 'id_number', 'full_name', 'date_of_birth', 
                'gender', 'nationality', 'issue_date', 'expiry_date', 
                'created_at', 'verified_at'
            ]
            
            for column in required_columns:
                try:
                    connection.execute(text(f"SHOW COLUMNS FROM identity_info LIKE '{column}'"))
                    logger.info(f"Cột {column} đã tồn tại")
                except Exception:
                    logger.warning(f"Cột {column} không tồn tại, tiến hành thêm...")
                    
                    # Định nghĩa kiểu dữ liệu cho từng cột
                    column_definitions = {
                        'id': 'INT AUTO_INCREMENT PRIMARY KEY',
                        'user_id': 'INT NOT NULL',
                        'id_number': 'VARCHAR(12) NOT NULL',
                        'full_name': 'VARCHAR(100) NOT NULL',
                        'date_of_birth': 'DATE NOT NULL',
                        'gender': 'VARCHAR(10) NOT NULL',
                        'nationality': 'VARCHAR(50) NOT NULL',
                        'issue_date': 'DATE NOT NULL',
                        'expiry_date': 'DATE NOT NULL',
                        'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                        'verified_at': 'DATETIME NULL'
                    }
                    
                    try:
                        # Không thêm cột id nếu đã có primary key
                        if column != 'id':
                            connection.execute(text(f"ALTER TABLE identity_info ADD COLUMN {column} {column_definitions[column]}"))
                            logger.info(f"Đã thêm cột {column}")
                    except Exception as e:
                        logger.error(f"Lỗi khi thêm cột {column}: {e}")
            
            logger.info("Hoàn thành cập nhật cấu trúc bảng identity_info")
            
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật bảng identity_info: {e}")
            
            # Nếu bảng không tồn tại, tạo mới
            try:
                logger.info("Bảng identity_info không tồn tại, tiến hành tạo mới...")
                connection.execute(text("""
                CREATE TABLE identity_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    id_number VARCHAR(12) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    date_of_birth DATE NOT NULL,
                    gender VARCHAR(10) NOT NULL,
                    nationality VARCHAR(50) NOT NULL,
                    issue_date DATE NOT NULL,
                    expiry_date DATE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    verified_at DATETIME NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    UNIQUE (id_number)
                )
                """))
                logger.info("Đã tạo bảng identity_info mới")
            except Exception as e:
                logger.error(f"Lỗi khi tạo bảng identity_info: {e}")

if __name__ == "__main__":
    logger.info("Bắt đầu cập nhật bảng identity_info...")
    update_identity_info_db()
    logger.info("Kết thúc quá trình cập nhật.")
