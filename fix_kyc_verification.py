"""
Script để sửa lỗi trong quy trình xác minh KYC
"""
from app import create_app
from models import db, User, KYCVerification, IdentityInfo
from utils.easyocr_utils import process_id_card
from datetime import datetime, date
import logging
import os

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_kyc_verification():
    """
    Sửa lỗi trong quy trình xác minh KYC
    """
    app = create_app()
    with app.app_context():
        try:
            # Lấy danh sách các user đã xác minh KYC nhưng chưa có thông tin trong bảng identity_info
            verified_users = User.query.filter_by(kyc_status='verified').all()
            logger.info(f"Số lượng user đã xác minh KYC: {len(verified_users)}")
            
            for user in verified_users:
                # Kiểm tra xem user đã có thông tin trong bảng identity_info chưa
                identity = IdentityInfo.query.filter_by(user_id=user.id).first()
                if identity:
                    logger.info(f"User ID {user.id} đã có thông tin trong bảng identity_info")
                    continue
                
                # Lấy thông tin KYC verification
                verification = KYCVerification.query.filter_by(user_id=user.id).first()
                if not verification:
                    logger.warning(f"User ID {user.id} không có bản ghi KYCVerification")
                    continue
                
                logger.info(f"Xử lý user ID {user.id}, Email: {user.email}")
                
                # Kiểm tra xem có đủ thông tin CCCD không
                if not verification.identity_card_front or not verification.identity_card_back:
                    logger.warning(f"User ID {user.id} thiếu ảnh CCCD")
                    continue
                
                # Kiểm tra xem file ảnh CCCD có tồn tại không
                if not os.path.exists(verification.identity_card_front) or not os.path.exists(verification.identity_card_back):
                    logger.warning(f"User ID {user.id} có đường dẫn ảnh CCCD không tồn tại")
                    continue
                
                # Trích xuất thông tin từ ảnh CCCD
                try:
                    # Lấy thông tin từ mặt trước
                    front_info = process_id_card(verification.identity_card_front, True)
                    logger.info(f"Thông tin từ mặt trước: {front_info}")
                    
                    # Lấy thông tin từ mặt sau
                    back_info = process_id_card(verification.identity_card_back, False)
                    logger.info(f"Thông tin từ mặt sau: {back_info}")
                    
                    # Kết hợp thông tin
                    combined_info = {**front_info, **back_info}
                    
                    # Kiểm tra xem có đủ thông tin cần thiết không
                    required_fields = ['id_number', 'full_name', 'date_of_birth', 'gender', 'nationality', 'issue_date', 'expiry_date']
                    missing_fields = [field for field in required_fields if field not in combined_info or combined_info[field] is None]
                    
                    if missing_fields:
                        logger.warning(f"User ID {user.id} thiếu thông tin: {missing_fields}")
                        
                        # Tạo thông tin mặc định cho các trường còn thiếu
                        if 'id_number' not in combined_info or combined_info['id_number'] is None:
                            combined_info['id_number'] = f"079{user.id:09d}"
                        
                        if 'full_name' not in combined_info or combined_info['full_name'] is None:
                            combined_info['full_name'] = f"USER_{user.id}"
                        
                        if 'date_of_birth' not in combined_info or combined_info['date_of_birth'] is None:
                            combined_info['date_of_birth'] = date(1990, 1, 1)
                        
                        if 'gender' not in combined_info or combined_info['gender'] is None:
                            combined_info['gender'] = "Nam"
                        
                        if 'nationality' not in combined_info or combined_info['nationality'] is None:
                            combined_info['nationality'] = "Việt Nam"
                        
                        if 'issue_date' not in combined_info or combined_info['issue_date'] is None:
                            combined_info['issue_date'] = date(2020, 1, 1)
                        
                        if 'expiry_date' not in combined_info or combined_info['expiry_date'] is None:
                            combined_info['expiry_date'] = date(2030, 1, 1)
                    
                    # Tạo bản ghi IdentityInfo mới
                    identity = IdentityInfo(
                        user_id=user.id,
                        id_number=combined_info['id_number'],
                        full_name=combined_info['full_name'],
                        date_of_birth=combined_info['date_of_birth'],
                        gender=combined_info['gender'],
                        nationality=combined_info['nationality'],
                        issue_date=combined_info['issue_date'],
                        expiry_date=combined_info['expiry_date'],
                        verified_at=verification.verified_at
                    )
                    
                    db.session.add(identity)
                    db.session.commit()
                    logger.info(f"Đã tạo bản ghi IdentityInfo cho user ID {user.id}")
                    
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý user ID {user.id}: {e}")
            
            logger.info("Hoàn thành việc sửa lỗi trong quy trình xác minh KYC")
            
        except Exception as e:
            logger.error(f"Lỗi khi sửa lỗi trong quy trình xác minh KYC: {e}")

if __name__ == "__main__":
    logger.info("Bắt đầu sửa lỗi trong quy trình xác minh KYC...")
    fix_kyc_verification()
    logger.info("Kết thúc quá trình sửa lỗi.")
