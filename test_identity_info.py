"""
Script để kiểm tra việc lưu thông tin vào bảng identity_info
"""
from app import create_app
from models import db, IdentityInfo, User, KYCVerification
from datetime import datetime, date
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_identity_info():
    """
    Kiểm tra việc lưu thông tin vào bảng identity_info
    """
    app = create_app()
    with app.app_context():
        try:
            # Kiểm tra xem có user nào trong hệ thống không
            user_count = User.query.count()
            logger.info(f"Số lượng user trong hệ thống: {user_count}")
            
            if user_count == 0:
                logger.warning("Không có user nào trong hệ thống, không thể kiểm tra")
                return
            
            # Lấy user đầu tiên để kiểm tra
            user = User.query.first()
            logger.info(f"Kiểm tra với user ID: {user.id}, Email: {user.email}")
            
            # Kiểm tra xem user này đã có bản ghi KYCVerification chưa
            verification = KYCVerification.query.filter_by(user_id=user.id).first()
            if verification:
                logger.info(f"User đã có bản ghi KYCVerification, status: {verification.status}")
                logger.info(f"ID card front: {verification.identity_card_front}")
                logger.info(f"ID card back: {verification.identity_card_back}")
            else:
                logger.warning("User chưa có bản ghi KYCVerification")
                # Tạo bản ghi KYCVerification mới
                verification = KYCVerification(
                    user_id=user.id,
                    status='verified',
                    identity_card_front='test_front.jpg',
                    identity_card_back='test_back.jpg',
                    id_card_verified=True
                )
                db.session.add(verification)
                db.session.commit()
                logger.info("Đã tạo bản ghi KYCVerification mới")
            
            # Kiểm tra xem user này đã có bản ghi IdentityInfo chưa
            identity = IdentityInfo.query.filter_by(user_id=user.id).first()
            if identity:
                logger.info(f"User đã có bản ghi IdentityInfo, ID: {identity.id}")
                logger.info(f"Thông tin: {identity.full_name}, {identity.id_number}")
                
                # Cập nhật thông tin
                identity.full_name = "NGUYỄN VĂN A"
                identity.id_number = "079123456789"
                identity.date_of_birth = date(1990, 1, 1)
                identity.gender = "Nam"
                identity.nationality = "Việt Nam"
                identity.issue_date = date(2020, 1, 1)
                identity.expiry_date = date(2030, 1, 1)
                
                db.session.add(identity)
                db.session.commit()
                logger.info("Đã cập nhật bản ghi IdentityInfo")
            else:
                logger.warning("User chưa có bản ghi IdentityInfo")
                # Tạo bản ghi IdentityInfo mới
                try:
                    identity = IdentityInfo(
                        user_id=user.id,
                        full_name="NGUYỄN VĂN A",
                        id_number="079123456789",
                        date_of_birth=date(1990, 1, 1),
                        gender="Nam",
                        nationality="Việt Nam",
                        issue_date=date(2020, 1, 1),
                        expiry_date=date(2030, 1, 1)
                    )
                    db.session.add(identity)
                    db.session.commit()
                    logger.info("Đã tạo bản ghi IdentityInfo mới")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Lỗi khi tạo bản ghi IdentityInfo: {e}")
            
            # Kiểm tra lại sau khi cập nhật
            identity = IdentityInfo.query.filter_by(user_id=user.id).first()
            if identity:
                logger.info(f"Thông tin sau khi cập nhật: {identity.full_name}, {identity.id_number}")
                logger.info(f"Ngày sinh: {identity.date_of_birth}")
                logger.info(f"Giới tính: {identity.gender}")
                logger.info(f"Quốc tịch: {identity.nationality}")
                logger.info(f"Ngày cấp: {identity.issue_date}")
                logger.info(f"Ngày hết hạn: {identity.expiry_date}")
            else:
                logger.error("Không tìm thấy bản ghi IdentityInfo sau khi cập nhật")
            
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra: {e}")

if __name__ == "__main__":
    logger.info("Bắt đầu kiểm tra...")
    test_identity_info()
    logger.info("Kết thúc kiểm tra.")
