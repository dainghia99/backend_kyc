"""
Script để tạo dữ liệu mẫu cho database
- 20 user đã xác thực KYC
- 20 user đang chờ xác thực KYC
"""
import os
import sys
import random
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash
import logging
import shutil

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Danh sách họ phổ biến ở Việt Nam
HO_VIET_NAM = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đinh", "Mai", "Trịnh"
]

# Danh sách tên đệm và tên phổ biến ở Việt Nam
TEN_DEM_NAM = ["Văn", "Hữu", "Đức", "Thành", "Công", "Quốc", "Minh", "Hải", "Anh", "Tuấn"]
TEN_NAM = ["Nam", "Hùng", "Dũng", "Thắng", "Trung", "Kiên", "Cường", "Phong", "Long", "Tùng"]

TEN_DEM_NU = ["Thị", "Ngọc", "Thúy", "Thanh", "Kim", "Hoài", "Mỹ", "Thu", "Phương", "Bích"]
TEN_NU = ["Hương", "Lan", "Linh", "Hà", "Thảo", "Trang", "Hạnh", "Mai", "Yến", "Ngọc"]

# Danh sách quốc tịch
QUOC_TICH = ["Việt Nam"]

# Danh sách giới tính
GIOI_TINH = ["Nam", "Nữ"]

def generate_vietnamese_name(gender="Nam"):
    """
    Tạo ngẫu nhiên một họ và tên tiếng Việt
    """
    ho = random.choice(HO_VIET_NAM)
    
    if gender == "Nam":
        ten_dem = random.choice(TEN_DEM_NAM)
        ten = random.choice(TEN_NAM)
    else:
        ten_dem = random.choice(TEN_DEM_NU)
        ten = random.choice(TEN_NU)
    
    return f"{ho} {ten_dem} {ten}"

def generate_random_date(start_year=1970, end_year=2000):
    """
    Tạo ngẫu nhiên một ngày trong khoảng từ start_year đến end_year
    """
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Sử dụng 28 để tránh lỗi với tháng 2
    return date(year, month, day)

def generate_id_number():
    """
    Tạo ngẫu nhiên một số CCCD 12 số
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

def seed_database():
    """
    Tạo dữ liệu mẫu cho database
    """
    try:
        from app import create_app
        from models import db, User, KYCVerification, IdentityInfo
        
        logger.info("Bắt đầu tạo dữ liệu mẫu...")
        
        # Tạo ứng dụng Flask
        app = create_app()
        
        with app.app_context():
            # Tạo thư mục uploads nếu chưa tồn tại
            uploads_dir = os.path.join(app.root_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Tạo 20 user đã xác thực KYC
            logger.info("Đang tạo 20 user đã xác thực KYC...")
            create_verified_users(app, 20)
            
            # Tạo 20 user đang chờ xác thực KYC
            logger.info("Đang tạo 20 user đang chờ xác thực KYC...")
            create_pending_users(app, 20)
            
        logger.info("Tạo dữ liệu mẫu hoàn tất!")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo dữ liệu mẫu: {str(e)}")
        return False

def create_verified_users(app, count):
    """
    Tạo các user đã xác thực KYC
    """
    from models import db, User, KYCVerification, IdentityInfo
    
    with app.app_context():
        for i in range(1, count + 1):
            # Tạo thông tin ngẫu nhiên
            gender = random.choice(GIOI_TINH)
            full_name = generate_vietnamese_name(gender)
            email = f"verified_user{i}@example.com"
            password = f"Password{i}@"
            date_of_birth = generate_random_date(1970, 2000)
            id_number = generate_id_number()
            nationality = "Việt Nam"
            issue_date = generate_random_date(2020, 2022)
            expiry_date = date(issue_date.year + 10, issue_date.month, issue_date.day)
            
            # Tạo user mới
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            user = User(
                email=email,
                password=hashed_password,
                kyc_status='verified',
                kyc_verified_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                identity_verified=True,
                role='user',
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 60))
            )
            
            db.session.add(user)
            db.session.flush()  # Để lấy user.id
            
            # Tạo bản ghi KYC Verification
            kyc = KYCVerification(
                user_id=user.id,
                status='verified',
                verified_at=user.kyc_verified_at,
                liveness_score=random.uniform(0.8, 1.0),
                blink_count=random.randint(3, 5),
                face_match=True,
                face_distance=random.uniform(0.1, 0.4),
                id_card_verified=True,
                created_at=user.created_at + timedelta(days=1)
            )
            
            db.session.add(kyc)
            
            # Tạo bản ghi Identity Info
            identity = IdentityInfo(
                user_id=user.id,
                id_number=id_number,
                full_name=full_name,
                date_of_birth=date_of_birth,
                gender=gender,
                nationality=nationality,
                issue_date=issue_date,
                expiry_date=expiry_date,
                created_at=user.created_at + timedelta(days=1),
                verified_at=user.kyc_verified_at
            )
            
            db.session.add(identity)
            
            logger.info(f"Đã tạo user đã xác thực: {email} - {full_name}")
        
        db.session.commit()
        logger.info(f"Đã tạo thành công {count} user đã xác thực KYC")

def create_pending_users(app, count):
    """
    Tạo các user đang chờ xác thực KYC
    """
    from models import db, User, KYCVerification
    
    with app.app_context():
        for i in range(1, count + 1):
            # Tạo thông tin ngẫu nhiên
            gender = random.choice(GIOI_TINH)
            full_name = generate_vietnamese_name(gender)
            email = f"pending_user{i}@example.com"
            password = f"Password{i}@"
            
            # Tạo user mới
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            user = User(
                email=email,
                password=hashed_password,
                kyc_status='pending',
                identity_verified=False,
                role='user',
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
            )
            
            db.session.add(user)
            db.session.flush()  # Để lấy user.id
            
            # Tạo bản ghi KYC Verification (một số đã upload CCCD, một số chưa)
            has_uploaded_id = random.choice([True, False])
            
            if has_uploaded_id:
                kyc = KYCVerification(
                    user_id=user.id,
                    status='pending',
                    id_card_verified=False,
                    created_at=user.created_at + timedelta(days=1)
                )
                
                db.session.add(kyc)
            
            logger.info(f"Đã tạo user đang chờ xác thực: {email}")
        
        db.session.commit()
        logger.info(f"Đã tạo thành công {count} user đang chờ xác thực KYC")

if __name__ == "__main__":
    print("=" * 50)
    print("TẠO DỮ LIỆU MẪU CHO DATABASE")
    print("=" * 50)
    
    success = seed_database()
    
    if success:
        print("\nTạo dữ liệu mẫu thành công!")
        print("- 20 user đã xác thực KYC (email: verified_user1@example.com, verified_user2@example.com, ...)")
        print("- 20 user đang chờ xác thực KYC (email: pending_user1@example.com, pending_user2@example.com, ...)")
        print("- Mật khẩu cho verified_userN@example.com: PasswordN@")
        print("- Mật khẩu cho pending_userN@example.com: PasswordN@")
    else:
        print("\nTạo dữ liệu mẫu thất bại!")
    
    print("\n" + "=" * 50)
    print("Nhấn Enter để thoát...")
    input()
    
    # Trả về mã thoát
    sys.exit(0 if success else 1)
