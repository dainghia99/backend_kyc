import cv2
import numpy as np
import pytesseract
from datetime import datetime
import re

def preprocess_image(image_path):
    # Đọc ảnh
    img = cv2.imread(image_path)
    
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Làm mịn ảnh để giảm nhiễu
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Tăng độ tương phản
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(blur)
    
    # Ngưỡng hóa
    thresh = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    return thresh

def extract_text(image):
    # Sử dụng Tesseract OCR để trích xuất text
    text = pytesseract.image_to_string(image, lang='vie')
    return text

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
    # Tiền xử lý ảnh
    processed_image = preprocess_image(image_path)
    
    # Trích xuất text
    text = extract_text(processed_image)
    
    # Phân tích thông tin
    info = parse_id_info(text, is_front)
    
    return info
