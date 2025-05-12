"""
Script để thêm cột id_card_verified vào bảng kyc_verification
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database():
    """
    Thêm cột id_card_verified vào bảng kyc_verification nếu chưa tồn tại
    """
    # Lấy DATABASE_URL từ biến môi trường hoặc sử dụng giá trị mặc định
    database_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/kyc_system')

    try:
        # Tạo kết nối đến cơ sở dữ liệu
        engine = create_engine(database_url)

        with engine.connect() as connection:
            # Kiểm tra xem cột id_card_verified đã tồn tại chưa
            try:
                connection.execute(text("SELECT id_card_verified FROM kyc_verification LIMIT 1"))
                logger.info("Cột id_card_verified đã tồn tại.")
            except Exception:
                # Thêm cột id_card_verified nếu chưa tồn tại
                try:
                    connection.execute(text("ALTER TABLE kyc_verification ADD COLUMN id_card_verified BOOLEAN DEFAULT FALSE"))
                    logger.info("Đã thêm cột id_card_verified.")
                except Exception as e:
                    logger.error(f"Lỗi khi thêm cột id_card_verified: {e}")
                    return False

            # Cập nhật model
            try:
                # Thêm cột id_card_verified vào model KYCVerification
                with open('models.py', 'r') as file:
                    content = file.read()

                # Kiểm tra xem cột đã tồn tại trong model chưa
                if 'id_card_verified = db.Column(db.Boolean, default=False)' not in content:
                    # Tìm vị trí để thêm cột mới
                    lines = content.split('\n')
                    kyc_model_start = False
                    for i, line in enumerate(lines):
                        if 'class KYCVerification(db.Model):' in line:
                            kyc_model_start = True
                        elif kyc_model_start and 'rejection_reason = db.Column' in line:
                            # Thêm cột mới sau cột rejection_reason
                            lines.insert(i + 1, '    id_card_verified = db.Column(db.Boolean, default=False)')
                            break

                    # Ghi lại nội dung đã cập nhật
                    with open('models.py', 'w') as file:
                        file.write('\n'.join(lines))

                    logger.info("Đã cập nhật model KYCVerification.")
                else:
                    logger.info("Cột id_card_verified đã tồn tại trong model.")

            except Exception as e:
                logger.error(f"Lỗi khi cập nhật model: {e}")
                return False

            return True

    except SQLAlchemyError as e:
        logger.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        return False

if __name__ == "__main__":
    logger.info("Bắt đầu cập nhật cơ sở dữ liệu...")
    success = update_database()

    if success:
        logger.info("Cập nhật cơ sở dữ liệu thành công!")
        sys.exit(0)
    else:
        logger.error("Cập nhật cơ sở dữ liệu thất bại!")
        sys.exit(1)
