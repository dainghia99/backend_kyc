"""
Script để cập nhật bảng identity_info, loại bỏ các trường không cần thiết và đảm bảo chỉ lưu các thông tin:
- Số CCCD
- Họ và tên
- Ngày sinh
- Giới tính
- Quốc tịch
- Ngày cấp
- Ngày hết hạn
"""
from app import create_app
from models import db
from sqlalchemy import text
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_identity_info_table():
    """
    Cập nhật bảng identity_info để phù hợp với yêu cầu mới
    """
    app = create_app()
    with app.app_context():
        connection = db.engine.connect()
        
        # Kiểm tra xem bảng identity_info có tồn tại không
        try:
            connection.execute(text("SELECT * FROM identity_info LIMIT 1"))
            logger.info("Bảng identity_info đã tồn tại.")
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra bảng identity_info: {e}")
            logger.info("Tạo bảng identity_info mới...")
            
            # Tạo bảng mới nếu chưa tồn tại
            try:
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
                logger.info("Đã tạo bảng identity_info mới.")
                return
            except Exception as e:
                logger.error(f"Lỗi khi tạo bảng identity_info: {e}")
                return
        
        # Kiểm tra các cột hiện có
        try:
            result = connection.execute(text("SHOW COLUMNS FROM identity_info"))
            columns = [row[0] for row in result]
            logger.info(f"Các cột hiện có trong bảng identity_info: {columns}")
            
            # Các cột cần giữ lại
            required_columns = [
                'id', 'user_id', 'id_number', 'full_name', 'date_of_birth', 
                'gender', 'nationality', 'issue_date', 'expiry_date', 
                'created_at', 'verified_at'
            ]
            
            # Các cột cần xóa
            columns_to_drop = [col for col in columns if col not in required_columns]
            
            if columns_to_drop:
                logger.info(f"Các cột cần xóa: {columns_to_drop}")
                
                # Xóa các cột không cần thiết
                for column in columns_to_drop:
                    try:
                        connection.execute(text(f"ALTER TABLE identity_info DROP COLUMN {column}"))
                        logger.info(f"Đã xóa cột {column}")
                    except Exception as e:
                        logger.error(f"Lỗi khi xóa cột {column}: {e}")
            else:
                logger.info("Không có cột nào cần xóa.")
            
            # Kiểm tra các cột cần thiết
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                logger.info(f"Các cột cần thêm: {missing_columns}")
                
                # Thêm các cột còn thiếu
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
                
                for column in missing_columns:
                    if column != 'id':  # Không thêm cột id nếu đã có primary key
                        try:
                            connection.execute(text(f"ALTER TABLE identity_info ADD COLUMN {column} {column_definitions[column]}"))
                            logger.info(f"Đã thêm cột {column}")
                        except Exception as e:
                            logger.error(f"Lỗi khi thêm cột {column}: {e}")
            else:
                logger.info("Không có cột nào cần thêm.")
            
            # Cập nhật model trong file models.py
            update_model_file()
            
            logger.info("Hoàn thành cập nhật bảng identity_info.")
            
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra cấu trúc bảng identity_info: {e}")

def update_model_file():
    """
    Cập nhật định nghĩa model IdentityInfo trong file models.py
    """
    try:
        model_file = 'models.py'
        with open(model_file, 'r') as file:
            content = file.read()
        
        # Tìm vị trí của class IdentityInfo
        identity_info_start = content.find('class IdentityInfo(db.Model):')
        if identity_info_start == -1:
            logger.error("Không tìm thấy class IdentityInfo trong file models.py")
            return
        
        # Tìm vị trí kết thúc của class IdentityInfo
        next_class_start = content.find('class', identity_info_start + 1)
        if next_class_start == -1:
            identity_info_end = len(content)
        else:
            identity_info_end = content.rfind('\n', 0, next_class_start)
        
        # Tạo định nghĩa mới cho class IdentityInfo
        new_identity_info_class = """class IdentityInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id_number = db.Column(db.String(12), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)"""
        
        # Thay thế định nghĩa cũ bằng định nghĩa mới
        new_content = content[:identity_info_start] + new_identity_info_class + content[identity_info_end:]
        
        # Ghi lại file
        with open(model_file, 'w') as file:
            file.write(new_content)
        
        logger.info("Đã cập nhật model IdentityInfo trong file models.py")
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật file models.py: {e}")

if __name__ == "__main__":
    logger.info("Bắt đầu cập nhật bảng identity_info...")
    update_identity_info_table()
    logger.info("Kết thúc quá trình cập nhật.")
