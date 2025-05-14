from app import create_app
from models import db, IdentityInfo
import sys

def check_identity_info():
    app = create_app()
    with app.app_context():
        print('Cấu trúc bảng identity_info:')
        print(IdentityInfo.__table__)
        
        # Kiểm tra số lượng bản ghi trong bảng
        count = IdentityInfo.query.count()
        print(f'Số lượng bản ghi trong bảng identity_info: {count}')
        
        # Liệt kê các bản ghi
        if count > 0:
            print('Danh sách các bản ghi:')
            records = IdentityInfo.query.all()
            for record in records:
                print(f'ID: {record.id}, User ID: {record.user_id}, Họ tên: {record.full_name}, Số CCCD: {record.id_number}')
        else:
            print('Không có bản ghi nào trong bảng identity_info')

if __name__ == '__main__':
    check_identity_info()
