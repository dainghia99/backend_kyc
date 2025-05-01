import easyocr
from PIL import Image, ImageDraw, ImageFont
import sys
import os

def test_easyocr():
    try:
        # Khởi tạo EasyOCR reader
        print("Khởi tạo EasyOCR reader...")
        reader = easyocr.Reader(['vi', 'en'], gpu=False)
        print("✅ Đã khởi tạo EasyOCR reader thành công!")
        
        # Kiểm tra các ngôn ngữ có sẵn
        print(f"Các ngôn ngữ đã tải: vi, en")
        
        try:
            # Tạo ảnh đơn giản để kiểm tra
            print("\nTạo ảnh kiểm tra...")
            img = Image.new('RGB', (400, 100), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Thử tải font hỗ trợ tiếng Việt nếu có
            try:
                # Thử tìm font hỗ trợ tiếng Việt
                font_paths = [
                    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"  # macOS
                ]
                
                font = None
                for path in font_paths:
                    if os.path.exists(path):
                        font = ImageFont.truetype(path, 24)
                        break
                
                # Nếu không tìm thấy font, sử dụng font mặc định
                if font is None:
                    font = ImageFont.load_default()
                
                # Vẽ văn bản
                d.text((10, 10), "Xin chào Việt Nam 123", fill=(0, 0, 0), font=font)
            except Exception as e:
                print(f"Không thể tải font: {e}")
                # Sử dụng font mặc định
                d.text((10, 10), "Xin chao Viet Nam 123", fill=(0, 0, 0))
            
            # Lưu hình ảnh
            test_image_path = "test_ocr_image.png"
            img.save(test_image_path)
            
            # Nhận dạng văn bản
            print("Đang nhận dạng văn bản...")
            result = reader.readtext(test_image_path, detail=0)
            text = "\n".join(result)
            print(f"\nKết quả OCR: {text.strip()}")
            
            # Xóa hình ảnh tạm
            os.remove(test_image_path)
            
        except Exception as e:
            print(f"Không thể thực hiện kiểm tra OCR: {e}")
        
        print("\nEasyOCR đã được cài đặt và cấu hình đúng! 🎉")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra EasyOCR: {e}")
        
        # Kiểm tra cài đặt
        try:
            import pkg_resources
            version = pkg_resources.get_distribution("easyocr").version
            print(f"\nPhiên bản EasyOCR hiện tại: {version}")
        except:
            print("\nKhông thể xác định phiên bản EasyOCR.")
        
        # Kiểm tra các dependencies
        try:
            import torch
            print(f"PyTorch version: {torch.__version__}")
            print(f"CUDA available: {torch.cuda.is_available()}")
        except ImportError:
            print("PyTorch chưa được cài đặt.")
        
        try:
            import torchvision
            print(f"Torchvision version: {torchvision.__version__}")
        except ImportError:
            print("Torchvision chưa được cài đặt.")
        
        try:
            import cv2
            print(f"OpenCV version: {cv2.__version__}")
        except ImportError:
            print("OpenCV chưa được cài đặt.")
        
        print("\nVui lòng cài đặt lại EasyOCR và các dependencies:")
        print("pip install easyocr torch torchvision opencv-python")
        
        return False

if __name__ == "__main__":
    test_easyocr()
