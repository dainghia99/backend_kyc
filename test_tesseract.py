import pytesseract
from PIL import Image
import sys
import os

def test_tesseract():
    try:
        # Kiểm tra phiên bản Tesseract
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR phiên bản: {version}")
        
        # Kiểm tra các ngôn ngữ có sẵn
        langs = pytesseract.get_languages()
        print(f"Các ngôn ngữ có sẵn: {langs}")
        
        # Kiểm tra xem tiếng Việt có sẵn không
        if 'vie' in langs:
            print("✅ Ngôn ngữ tiếng Việt (vie) đã được cài đặt.")
        else:
            print("⚠️ Ngôn ngữ tiếng Việt (vie) chưa được cài đặt.")
            print("   Vui lòng cài đặt thêm gói ngôn ngữ tiếng Việt.")
        
        # Thử nhận dạng một đoạn văn bản tiếng Việt đơn giản
        try:
            # Tạo một hình ảnh văn bản đơn giản để kiểm tra
            from PIL import Image, ImageDraw, ImageFont
            
            # Tạo hình ảnh trắng
            img = Image.new('RGB', (400, 100), color = (255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Thử tìm font mặc định
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 24)
                except:
                    font = ImageFont.load_default()
            
            # Vẽ văn bản
            d.text((10,10), "Xin chào Việt Nam 123", fill=(0,0,0), font=font)
            
            # Lưu hình ảnh
            test_image_path = "test_ocr_image.png"
            img.save(test_image_path)
            
            # Nhận dạng văn bản
            text = pytesseract.image_to_string(Image.open(test_image_path), lang='vie')
            print(f"\nKết quả OCR: {text.strip()}")
            
            # Xóa hình ảnh tạm
            os.remove(test_image_path)
            
        except Exception as e:
            print(f"Không thể thực hiện kiểm tra OCR: {e}")
        
        print("\nTesseract OCR đã được cài đặt và cấu hình đúng! 🎉")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra Tesseract: {e}")
        
        # Kiểm tra đường dẫn Tesseract
        try:
            tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
            print(f"\nĐường dẫn Tesseract hiện tại: {tesseract_cmd}")
        except:
            print("\nKhông thể xác định đường dẫn Tesseract.")
        
        print("\nGợi ý khắc phục:")
        print("1. Đảm bảo Tesseract OCR đã được cài đặt")
        print("2. Đảm bảo Tesseract đã được thêm vào PATH hệ thống")
        print("3. Hoặc thiết lập đường dẫn Tesseract trong code:")
        print("   pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Windows")
        print("   pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/macOS")
        return False

if __name__ == "__main__":
    print("=== Kiểm tra cài đặt Tesseract OCR ===\n")
    test_tesseract()
