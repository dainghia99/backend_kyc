import os
import sys
from utils.easyocr_utils import process_id_card
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_name_extraction(image_path):
    """
    Kiểm tra trích xuất tên từ ảnh CCCD
    
    Args:
        image_path: Đường dẫn đến ảnh CCCD
    """
    logger.info(f"Bắt đầu kiểm tra trích xuất tên từ ảnh: {image_path}")
    
    # Kiểm tra xem file có tồn tại không
    if not os.path.exists(image_path):
        logger.error(f"Không tìm thấy file ảnh: {image_path}")
        return
    
    try:
        # Xử lý ảnh CCCD (giả định là mặt trước)
        info = process_id_card(image_path, is_front=True)
        
        # Kiểm tra kết quả
        if 'full_name' in info:
            logger.info(f"Đã trích xuất thành công họ tên: {info['full_name']}")
            
            # Kiểm tra xem tên có phải là "KHOÀNG ĐẠI NGHĨA" không
            if info['full_name'] == "KHOÀNG ĐẠI NGHĨA":
                logger.info("✅ Trích xuất tên thành công: KHOÀNG ĐẠI NGHĨA")
            else:
                logger.warning(f"❌ Tên trích xuất không phải là KHOÀNG ĐẠI NGHĨA: {info['full_name']}")
        else:
            logger.error("❌ Không thể trích xuất họ tên từ ảnh")
        
        # In ra tất cả thông tin đã trích xuất
        logger.info("Tất cả thông tin trích xuất được:")
        for key, value in info.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Lỗi khi xử lý ảnh: {e}")

if __name__ == "__main__":
    # Kiểm tra tham số dòng lệnh
    if len(sys.argv) < 2:
        print("Sử dụng: python test_name_extraction.py <đường_dẫn_ảnh>")
        sys.exit(1)
    
    # Lấy đường dẫn ảnh từ tham số dòng lệnh
    image_path = sys.argv[1]
    
    # Chạy kiểm tra
    test_name_extraction(image_path)
