import cv2
import numpy as np
import pytesseract
from datetime import datetime
import re
import os
import platform
import subprocess

# Cấu hình Tesseract OCR
def configure_tesseract():
    """Cấu hình đường dẫn Tesseract dựa trên hệ điều hành"""
    system = platform.system()

    if system == "Windows":
        # Kiểm tra các đường dẫn phổ biến trên Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path

                # Thiết lập biến môi trường TESSDATA_PREFIX
                tessdata_path = os.path.join(os.path.dirname(path), 'tessdata')
                os.environ['TESSDATA_PREFIX'] = tessdata_path
                print(f"Đã cấu hình Tesseract OCR: {path}")
                print(f"TESSDATA_PREFIX: {tessdata_path}")

                # Kiểm tra file ngôn ngữ tiếng Việt
                vie_file = os.path.join(tessdata_path, 'vie.traineddata')
                if not os.path.exists(vie_file):
                    print(f"Cảnh báo: Không tìm thấy file ngôn ngữ tiếng Việt: {vie_file}")
                    print("Vui lòng tải file vie.traineddata và đặt vào thư mục tessdata")
                else:
                    print(f"Tìm thấy file ngôn ngữ tiếng Việt: {vie_file}")

                return True

    # Kiểm tra xem Tesseract có trong PATH không
    try:
        result = subprocess.run(["tesseract", "--version"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        if "tesseract" in result.stdout.lower():
            print(f"Tesseract OCR đã được cài đặt trong PATH: {result.stdout.splitlines()[0]}")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    print("CẢNH BÁO: Không tìm thấy Tesseract OCR. Vui lòng cài đặt Tesseract OCR.")
    return False

# Gọi hàm cấu hình khi import module
configure_tesseract()

def preprocess_image(image_path):
    # Đọc ảnh
    img = cv2.imread(image_path)

    # Kiểm tra kích thước ảnh và resize nếu cần
    height, width = img.shape[:2]
    # Tăng kích thước ảnh nếu quá nhỏ
    if width < 1000:
        scale_factor = 1000 / width
        img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        print(f"Tăng kích thước ảnh lên {scale_factor:.2f} lần")

    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Cân bằng histogram để cải thiện độ tương phản
    equalized = cv2.equalizeHist(gray)

    # Làm mịn ảnh để giảm nhiễu (sử dụng bộ lọc nhỏ hơn để giữ chi tiết)
    blur = cv2.GaussianBlur(equalized, (3, 3), 0)

    # Tăng độ tương phản với CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(blur)

    # Làm sắc nét ảnh
    kernel = np.array([[-1,-1,-1],
                       [-1, 9,-1],
                       [-1,-1,-1]])
    sharpened = cv2.filter2D(contrast, -1, kernel)

    # Giảm nhiễu với bộ lọc song phương
    denoised = cv2.bilateralFilter(sharpened, 9, 75, 75)

    # Ngưỡng hóa thích nghi
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Lưu ảnh đã xử lý để debug
    debug_dir = os.path.join(os.path.dirname(image_path), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    cv2.imwrite(os.path.join(debug_dir, f"preprocessed_{os.path.basename(image_path)}"), thresh)

    return thresh

def extract_text(image):
    # Sử dụng Tesseract OCR để trích xuất text với các tham số tối ưu
    try:
        # Thử với tiếng Việt và các tham số tối ưu
        # --psm 6: Giả định một khối văn bản thống nhất
        # --oem 3: Sử dụng LSTM OCR Engine only
        # -c preserve_interword_spaces=1: Giữ khoảng cách giữa các từ
        custom_config = r'--psm 6 --oem 3 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(image, lang='vie', config=custom_config)

        # Kiểm tra nếu text quá ngắn, có thể OCR không hoạt động tốt
        if len(text.strip()) < 20:
            print("Văn bản trích xuất quá ngắn, thử lại với các tham số khác...")
            # Thử với PSM 4 (giả định một cột văn bản duy nhất)
            text = pytesseract.image_to_string(image, lang='vie', config='--psm 4 --oem 3')

        return text
    except Exception as e:
        print(f"Lỗi khi sử dụng ngôn ngữ tiếng Việt: {e}")
        try:
            # Nếu không được, thử với tiếng Anh và các tham số tương tự
            print("Thử lại với ngôn ngữ tiếng Anh...")
            text = pytesseract.image_to_string(image, lang='eng', config='--psm 6 --oem 3')
            return text
        except Exception as e2:
            print(f"Lỗi khi sử dụng ngôn ngữ tiếng Anh: {e2}")
            # Nếu vẫn không được, thử không chỉ định ngôn ngữ
            try:
                print("Thử lại không chỉ định ngôn ngữ...")
                text = pytesseract.image_to_string(image, config='--psm 6')
                return text
            except Exception as e3:
                print(f"Lỗi khi không chỉ định ngôn ngữ: {e3}")
                raise Exception("Không thể trích xuất văn bản từ ảnh. Lỗi Tesseract OCR.")

def parse_id_info(text, is_front):
    info = {}

    if is_front:
        # Trích xuất số CCCD (12 số)
        id_match = re.search(r'\b\d{12}\b', text)
        if id_match:
            info['id_number'] = id_match.group()

        # Trích xuất họ tên
        name_match = re.search(r'Họ và tên:?\s*([^\n]+)', text)
        if name_match:
            info['full_name'] = name_match.group(1).strip()

        # Trích xuất ngày sinh
        dob_match = re.search(r'Ngày sinh:?\s*(\d{2}/\d{2}/\d{4})', text)
        if dob_match:
            info['date_of_birth'] = datetime.strptime(dob_match.group(1), '%d/%m/%Y').date()

        # Trích xuất giới tính
        if 'Nam' in text:
            info['gender'] = 'Nam'
        elif 'Nữ' in text:
            info['gender'] = 'Nữ'

        # Trích xuất quốc tịch
        nationality_match = re.search(r'Quốc tịch:?\s*([^\n]+)', text)
        if nationality_match:
            info['nationality'] = nationality_match.group(1).strip()

    else:  # Mặt sau CCCD
        # Trích xuất quê quán
        birth_place_match = re.search(r'Quê quán:?\s*([^\n]+)', text)
        if birth_place_match:
            info['birth_place'] = birth_place_match.group(1).strip()

        # Trích xuất nơi thường trú
        residence_match = re.search(r'Nơi thường trú:?\s*([^\n]+)', text)
        if residence_match:
            info['residence_address'] = residence_match.group(1).strip()

        # Trích xuất ngày cấp
        issue_date_match = re.search(r'Ngày cấp:?\s*(\d{2}/\d{2}/\d{4})', text)
        if issue_date_match:
            info['issue_date'] = datetime.strptime(issue_date_match.group(1), '%d/%m/%Y').date()

        # Trích xuất ngày hết hạn
        expiry_date_match = re.search(r'Có giá trị đến:?\s*(\d{2}/\d{2}/\d{4})', text)
        if expiry_date_match:
            info['expiry_date'] = datetime.strptime(expiry_date_match.group(1), '%d/%m/%Y').date()

    return info

def process_id_card(image_path, is_front):
    try:
        # Kiểm tra xem Tesseract đã được cài đặt chưa
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            print(f"Lỗi Tesseract OCR: {e}")
            # Thử cấu hình lại Tesseract
            if not configure_tesseract():
                raise Exception("tesseract is not installed or it's not in your PATH. See README file for more information.")

        # Đọc ảnh gốc để lưu trữ
        original_img = cv2.imread(image_path)

        # Tiền xử lý ảnh
        processed_image = preprocess_image(image_path)

        # Trích xuất text
        text = extract_text(processed_image)

        # Lưu text vào file để debug
        debug_dir = os.path.join(os.path.dirname(image_path), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, f"ocr_text_{os.path.basename(image_path)}.txt")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(text)

        # Phân tích thông tin
        info = parse_id_info(text, is_front)

        # Nếu không trích xuất được thông tin cơ bản, thử lại với các phương pháp tiền xử lý khác
        if is_front and ("id_number" not in info or "full_name" not in info):
            print("Không tìm thấy thông tin cơ bản, thử lại với phương pháp tiền xử lý khác...")

            # Phương pháp 2: Sử dụng ngưỡng hóa Otsu
            gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Lưu ảnh đã xử lý để debug
            cv2.imwrite(os.path.join(debug_dir, f"otsu_thresh_{os.path.basename(image_path)}"), otsu_thresh)

            # Thử OCR với ảnh đã xử lý mới
            text = pytesseract.image_to_string(otsu_thresh, lang='vie', config='--psm 6 --oem 3')

            # Lưu text vào file để debug
            with open(os.path.join(debug_dir, f"ocr_text_otsu_{os.path.basename(image_path)}.txt"), "w", encoding="utf-8") as f:
                f.write(text)

            # Phân tích thông tin lại
            info = parse_id_info(text, is_front)

            # Nếu vẫn không tìm thấy, thử phương pháp 3
            if "id_number" not in info or "full_name" not in info:
                print("Vẫn không tìm thấy thông tin cơ bản, thử lại với phương pháp thứ 3...")

                # Phương pháp 3: Tăng độ sáng và độ tương phản
                alpha = 1.5  # Điều chỉnh độ tương phản
                beta = 30    # Điều chỉnh độ sáng
                adjusted = cv2.convertScaleAbs(original_img, alpha=alpha, beta=beta)

                # Chuyển sang ảnh xám và áp dụng ngưỡng hóa thích nghi
                adjusted_gray = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)
                adaptive_thresh = cv2.adaptiveThreshold(adjusted_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

                # Lưu ảnh đã xử lý để debug
                cv2.imwrite(os.path.join(debug_dir, f"adaptive_thresh_{os.path.basename(image_path)}"), adaptive_thresh)

                # Thử OCR với ảnh đã xử lý mới
                text = pytesseract.image_to_string(adaptive_thresh, lang='vie', config='--psm 4 --oem 3')

                # Lưu text vào file để debug
                with open(os.path.join(debug_dir, f"ocr_text_adaptive_{os.path.basename(image_path)}.txt"), "w", encoding="utf-8") as f:
                    f.write(text)

                # Phân tích thông tin lại
                info = parse_id_info(text, is_front)

        return info
    except Exception as e:
        print(f"Lỗi xử lý OCR: {e}")
        raise e
