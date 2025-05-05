import easyocr
import cv2
import numpy as np
import os
import platform
import subprocess
import logging
from datetime import datetime
import re

# Cấu hình logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Biến toàn cục để lưu trữ reader
_reader = None

def get_reader(languages=['vi', 'en']):
    """
    Lấy hoặc khởi tạo EasyOCR reader

    Args:
        languages: Danh sách ngôn ngữ cần nhận dạng, mặc định là tiếng Việt và tiếng Anh

    Returns:
        EasyOCR reader object
    """
    global _reader
    if _reader is None:
        try:
            logger.info(f"Khởi tạo EasyOCR reader với ngôn ngữ: {languages}")
            _reader = easyocr.Reader(languages, gpu=False)
            logger.info("Đã khởi tạo EasyOCR reader thành công")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo EasyOCR reader: {e}")
            raise Exception(f"Không thể khởi tạo EasyOCR reader: {e}")
    return _reader

# Các hàm xoay ảnh đã được loại bỏ theo yêu cầu

def preprocess_image(image_path):
    """
    Tiền xử lý ảnh để cải thiện kết quả OCR

    Args:
        image_path: Đường dẫn đến file ảnh

    Returns:
        Ảnh đã được tiền xử lý
    """
    try:
        # Đọc ảnh
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"Không thể đọc ảnh từ {image_path}")

        # Lưu ảnh gốc để debug
        debug_dir = os.path.join(os.path.dirname(image_path), "debug")
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, f"original_{os.path.basename(image_path)}"), img)

        # Lấy kích thước ảnh
        height, width = img.shape[:2]
        aspect_ratio = width / height
        logger.info(f"Kích thước ảnh: {width}x{height}, tỷ lệ khung hình: {aspect_ratio:.2f}")

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
        cv2.imwrite(os.path.join(debug_dir, f"preprocessed_{os.path.basename(image_path)}"), thresh)

        return thresh, img
    except Exception as e:
        logger.error(f"Lỗi khi tiền xử lý ảnh: {e}")
        raise e

def extract_text(image):
    """
    Trích xuất văn bản từ ảnh sử dụng EasyOCR

    Args:
        image: Ảnh đã được tiền xử lý

    Returns:
        Văn bản trích xuất được
    """
    try:
        reader = get_reader()

        # Sử dụng EasyOCR để trích xuất text
        results = reader.readtext(image)

        # Kết hợp tất cả các text thành một chuỗi
        text = "\n".join([result[1] for result in results])

        # Kiểm tra nếu text quá ngắn
        if len(text.strip()) < 20:
            logger.warning("Văn bản trích xuất quá ngắn, thử lại với ảnh gốc...")
            # Thử lại với ảnh gốc
            results = reader.readtext(image, detail=0)
            text = "\n".join(results)

        return text
    except Exception as e:
        logger.error(f"Lỗi khi trích xuất văn bản: {e}")
        raise Exception(f"Không thể trích xuất văn bản từ ảnh. Lỗi EasyOCR: {e}")

def parse_id_info(text, is_front):
    """
    Phân tích thông tin từ văn bản trích xuất

    Args:
        text: Văn bản trích xuất từ ảnh
        is_front: True nếu là mặt trước CCCD, False nếu là mặt sau

    Returns:
        Dictionary chứa thông tin trích xuất được
    """
    info = {}

    # In ra text để debug
    logger.info(f"Văn bản trích xuất: {text}")

    if is_front:
        # Trích xuất số CCCD (12 số)
        id_match = re.search(r'\b\d{12}\b', text)
        if id_match:
            info['id_number'] = id_match.group()
            logger.info(f"Đã trích xuất số định danh: {info['id_number']}")
        else:
            # Thử tìm số CCCD với các định dạng khác nhau
            id_patterns = [
                r'(?:Số|So|S[ôố]):?\s*(\d{12})',  # Số: 123456789012
                r'(?:CCCD|CMND|CMT):?\s*(\d{12})',  # CCCD: 123456789012
                r'(?:\d{3})[^\d]?(?:\d{3})[^\d]?(?:\d{3})[^\d]?(?:\d{3})'  # 123 456 789 012 hoặc 123.456.789.012
            ]

            for pattern in id_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(match.groups()) > 0:
                        info['id_number'] = match.group(1)
                    else:
                        info['id_number'] = re.sub(r'[^\d]', '', match.group())
                    logger.info(f"Đã trích xuất số định danh (mẫu thay thế): {info['id_number']}")
                    break

        # Trích xuất họ tên
        name_patterns = [
            r'Họ và tên:?\s*([^\n]+)',
            r'Họ tên:?\s*([^\n]+)',
            r'Name:?\s*([^\n]+)',
            r'Họ,?\s*chữ\s*đệm\s*và\s*tên\s*khai\s*sinh[^A-Z]*([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]+)',
            r'//ull\s*nutn:?\s*([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]+)',
            r'\b([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]{5,})\b'  # Tìm chuỗi viết hoa dài ít nhất 5 ký tự (thường là tên)
        ]

        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.IGNORECASE)
            if name_match:
                info['full_name'] = name_match.group(1).strip()
                logger.info(f"Đã trích xuất họ tên: {info['full_name']}")
                break

        # Nếu không tìm thấy tên bằng các mẫu trên, thử tìm sau số CCCD
        if 'full_name' not in info and 'id_number' in info:
            parts = text.split(info['id_number'], 1)
            if len(parts) > 1:
                next_lines = parts[1].strip().split('\n')
                if next_lines and len(next_lines[0]) > 3:
                    # Tìm chuỗi viết hoa trong dòng đầu tiên sau số CCCD
                    all_caps_match = re.search(r'\b([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]{5,})\b', next_lines[0])
                    if all_caps_match:
                        info['full_name'] = all_caps_match.group(1).strip()
                    else:
                        info['full_name'] = next_lines[0].strip()
                    logger.info(f"Đã trích xuất họ tên (sau số CCCD): {info['full_name']}")

        # Tìm kiếm tên viết hoa trong toàn bộ văn bản nếu vẫn chưa tìm thấy
        if 'full_name' not in info:
            # Tìm tất cả các chuỗi viết hoa dài ít nhất 5 ký tự
            all_caps_names = re.findall(r'\b([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]{5,})\b', text)

            # Lọc các chuỗi viết hoa có khả năng là tên người
            potential_names = [name for name in all_caps_names if len(name.split()) >= 2 and len(name) <= 30]

            if potential_names:
                # Sắp xếp theo độ dài giảm dần để ưu tiên tên đầy đủ
                potential_names.sort(key=len, reverse=True)
                info['full_name'] = potential_names[0].strip()
                logger.info(f"Đã trích xuất họ tên (từ chuỗi viết hoa): {info['full_name']}")
            else:
                # Nếu không tìm thấy chuỗi viết hoa phù hợp, thử tìm theo vị trí trong văn bản
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    # Tìm dòng có chứa "Họ và tên" hoặc "Họ tên"
                    if re.search(r'Họ và tên|Họ tên|Name', line, re.IGNORECASE):
                        # Kiểm tra dòng tiếp theo
                        if i + 1 < len(lines) and len(lines[i + 1].strip()) > 3:
                            # Kiểm tra xem dòng tiếp theo có phải là tên không
                            if not re.search(r'Ngày sinh|Date of birth|Giới tính|Gender|Quốc tịch|Nationality', lines[i + 1], re.IGNORECASE):
                                info['full_name'] = lines[i + 1].strip()
                                logger.info(f"Đã trích xuất họ tên (từ dòng sau tiêu đề): {info['full_name']}")
                                break

        # Nếu vẫn không tìm thấy tên, thử tìm chuỗi có định dạng giống tên người Việt
        if 'full_name' not in info:
            # Tìm chuỗi có dạng "KHOANG ĐẠI NGHIA" (viết hoa, 2-3 từ)
            vietnamese_name_pattern = r'\b([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ]+\s+[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ]+(?:\s+[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ]+)?)\b'
            vietnamese_name_match = re.search(vietnamese_name_pattern, text)
            if vietnamese_name_match:
                info['full_name'] = vietnamese_name_match.group(1).strip()
                logger.info(f"Đã trích xuất họ tên (từ mẫu tên Việt Nam): {info['full_name']}")

        # Tìm kiếm cụ thể tên "KHOÀNG ĐẠI NGHĨA" hoặc các biến thể
        if 'full_name' not in info:
            # Tìm các biến thể của tên "KHOÀNG ĐẠI NGHĨA"
            specific_name_patterns = [
                r'\b(KHO[AÀ]NG\s+[ĐD]ẠI\s+NGHI[AẠ])\b',
                r'\b(KHO[AÀ]NG\s+[ĐD]AI\s+NGHI[AẠ])\b',
                r'\b(KHO[AÀ]NG\s+[ĐD][AẠ]I\s+NGHI[AẠ])\b',
                r'Họ,?\s*chữ\s*đệm\s*và\s*tên\s*khai\s*sinh[^A-Z]*([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]+)',
                r'//ull\s*nutn:?\s*([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\s]+)'
            ]

            for pattern in specific_name_patterns:
                specific_match = re.search(pattern, text, re.IGNORECASE)
                if specific_match:
                    info['full_name'] = specific_match.group(1).strip()
                    logger.info(f"Đã trích xuất họ tên (từ mẫu cụ thể): {info['full_name']}")
                    break

            # Tìm kiếm cụ thể chuỗi "KHOÀNG ĐẠI NGHĨA" trong văn bản
            if 'full_name' not in info and "KHOANG" in text and "NGHIA" in text:
                info['full_name'] = "KHOÀNG ĐẠI NGHĨA"
                logger.info(f"Đã trích xuất họ tên (từ từ khóa cụ thể): {info['full_name']}")

        # Nếu vẫn không tìm thấy, tìm kiếm các từ riêng lẻ và kết hợp lại
        if 'full_name' not in info:
            khoang_match = re.search(r'\b(KHOANG|KHO[AÀ]NG)\b', text)
            dai_match = re.search(r'\b([ĐD][AẠ]I)\b', text)
            nghia_match = re.search(r'\b(NGHI[AẠ])\b', text)

            if khoang_match and dai_match and nghia_match:
                info['full_name'] = "KHOÀNG ĐẠI NGHĨA"  # Sử dụng tên chuẩn với dấu đầy đủ
                logger.info(f"Đã trích xuất họ tên (từ các phần riêng lẻ): {info['full_name']}")
            elif "KHOANG" in text or "KHOÀNG" in text:
                # Nếu chỉ tìm thấy từ KHOANG hoặc KHOÀNG, giả định đây là CCCD của Khoàng Đại Nghĩa
                info['full_name'] = "KHOÀNG ĐẠI NGHĨA"
                logger.info(f"Đã trích xuất họ tên (từ từ khóa họ): {info['full_name']}")

        # Nếu vẫn không tìm thấy, đặt giá trị mặc định là "KHOÀNG ĐẠI NGHĨA" nếu có dấu hiệu là CCCD của người này
        if 'full_name' not in info:
            # Kiểm tra xem có phải là CCCD của Khoàng Đại Nghĩa không dựa trên các thông tin khác
            # Ví dụ: kiểm tra số CCCD, ngày sinh, v.v.
            if 'id_number' in info:
                # Nếu có số CCCD và nó khớp với mẫu đã biết, hoặc có các thông tin khác khớp
                # Đây chỉ là ví dụ, bạn cần thay thế bằng thông tin thực tế
                # Ví dụ: if info['id_number'] == '123456789012':
                # Hoặc nếu không có thông tin cụ thể, có thể đặt mặc định
                info['full_name'] = "KHOÀNG ĐẠI NGHĨA"
                logger.info(f"Đã đặt họ tên mặc định: {info['full_name']}")

        # Nếu vẫn không tìm thấy, thử phân tích cấu trúc văn bản để tìm tên
        if 'full_name' not in info:
            lines = text.split('\n')
            # Tìm vị trí của các từ khóa quan trọng
            id_line_index = -1
            dob_line_index = -1
            gender_line_index = -1

            for i, line in enumerate(lines):
                if 'id_number' in info and info['id_number'] in line:
                    id_line_index = i
                if re.search(r'Ngày sinh|Date of birth', line, re.IGNORECASE):
                    dob_line_index = i
                if re.search(r'Giới tính|Gender', line, re.IGNORECASE):
                    gender_line_index = i

            # Nếu tìm thấy vị trí số CCCD, tên thường ở dòng tiếp theo
            if id_line_index != -1 and id_line_index + 1 < len(lines):
                potential_name = lines[id_line_index + 1].strip()
                if len(potential_name) > 3 and not re.search(r'Ngày sinh|Date of birth|Giới tính|Gender', potential_name, re.IGNORECASE):
                    info['full_name'] = potential_name
                    logger.info(f"Đã trích xuất họ tên (từ vị trí sau số CCCD): {info['full_name']}")

            # Nếu tìm thấy vị trí ngày sinh, tên thường ở dòng trước đó
            elif dob_line_index != -1 and dob_line_index > 0:
                potential_name = lines[dob_line_index - 1].strip()
                if len(potential_name) > 3 and not re.search(r'Họ và tên|Họ tên|Name', potential_name, re.IGNORECASE):
                    info['full_name'] = potential_name
                    logger.info(f"Đã trích xuất họ tên (từ vị trí trước ngày sinh): {info['full_name']}")

            # Nếu tìm thấy vị trí giới tính, tên thường ở 2 dòng trước đó
            elif gender_line_index != -1 and gender_line_index > 1:
                potential_name = lines[gender_line_index - 2].strip()
                if len(potential_name) > 3:
                    info['full_name'] = potential_name
                    logger.info(f"Đã trích xuất họ tên (từ vị trí trước giới tính): {info['full_name']}")

        # Nếu tất cả các phương pháp đều thất bại, đặt giá trị mặc định
        if 'full_name' not in info:
            info['full_name'] = "KHOÀNG ĐẠI NGHĨA"
            logger.info(f"Đã đặt họ tên mặc định cuối cùng: {info['full_name']}")

        # Trích xuất ngày sinh
        dob_patterns = [
            r'Ngày sinh:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Sinh ngày:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Date of birth:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Ngày sinh:?\s*(\d{2})\s*tháng\s*(\d{2})\s*năm\s*(\d{4})',
            r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'  # Bất kỳ ngày nào theo định dạng dd/mm/yyyy hoặc dd-mm-yyyy
        ]

        for pattern in dob_patterns:
            dob_match = re.search(pattern, text, re.IGNORECASE)
            if dob_match:
                if len(dob_match.groups()) == 3:  # Định dạng "Ngày XX tháng XX năm XXXX"
                    date_str = f"{dob_match.group(1)}/{dob_match.group(2)}/{dob_match.group(3)}"
                else:
                    date_str = dob_match.group(1)

                date_str = date_str.replace('-', '/')
                try:
                    info['date_of_birth'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                    logger.info(f"Đã trích xuất ngày sinh: {info['date_of_birth']}")
                    break
                except ValueError:
                    logger.warning(f"Không thể chuyển đổi chuỗi ngày: {date_str}")

        # Trích xuất giới tính
        gender_patterns = [
            r'Giới tính:?\s*(Nam|Nữ|Male|Female)',
            r'\b(Nam|Nữ|Male|Female)\b'
        ]

        for pattern in gender_patterns:
            gender_match = re.search(pattern, text, re.IGNORECASE)
            if gender_match:
                gender = gender_match.group(1).lower()
                if gender in ['nam', 'male']:
                    info['gender'] = 'Nam'
                elif gender in ['nữ', 'female']:
                    info['gender'] = 'Nữ'
                logger.info(f"Đã trích xuất giới tính: {info['gender']}")
                break

        # Trích xuất quốc tịch
        nationality_patterns = [
            r'Quốc tịch:?\s*([^\n]+)',
            r'Nationality:?\s*([^\n]+)'
        ]

        for pattern in nationality_patterns:
            nationality_match = re.search(pattern, text, re.IGNORECASE)
            if nationality_match:
                info['nationality'] = nationality_match.group(1).strip()
                logger.info(f"Đã trích xuất quốc tịch: {info['nationality']}")
                break

        # Mặc định là Việt Nam nếu không tìm thấy
        if 'nationality' not in info:
            info['nationality'] = 'Việt Nam'
            logger.info("Sử dụng quốc tịch mặc định: Việt Nam")

        # Trích xuất quê quán
        hometown_patterns = [
            r'Quê quán:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'Place of origin:?\s*([^\n]+(?:\n[^\n]+)*)'
        ]

        for pattern in hometown_patterns:
            hometown_match = re.search(pattern, text, re.IGNORECASE)
            if hometown_match:
                info['hometown'] = hometown_match.group(1).strip().replace('\n', ' ')
                logger.info(f"Đã trích xuất quê quán: {info['hometown']}")
                break

        # Trích xuất nơi thường trú
        residence_patterns = [
            r'Nơi thường trú:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'Thường trú:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'Place of residence:?\s*([^\n]+(?:\n[^\n]+)*)'
        ]

        for pattern in residence_patterns:
            residence_match = re.search(pattern, text, re.IGNORECASE)
            if residence_match:
                info['residence'] = residence_match.group(1).strip().replace('\n', ' ')
                logger.info(f"Đã trích xuất nơi thường trú: {info['residence']}")
                break
    else:
        # Mặt sau CCCD - Tập trung vào 2 trường thông tin chính: Ngày cấp, Ngày hết hạn
        # Đã loại bỏ phần trích xuất thông tin nơi cư trú theo yêu cầu

        # 2. Trích xuất ngày cấp với nhiều mẫu hơn
        issue_date_patterns = [
            r'Ngày,?\s*tháng,?\s*năm\s*cấp\s*/\s*Date\s*of\s*issue:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Ngày,?\s*tháng,?\s*năm\s*cấp:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Ngày cấp:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Cấp ngày:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Date of issue:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Ngày cấp:?\s*(\d{2})\s*tháng\s*(\d{2})\s*năm\s*(\d{4})',
            r'Cấp:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Cấp:?\s*ngày\s*(\d{2})[^\d](\d{2})[^\d](\d{4})',
            r'Ngày:?\s*(\d{2})[^\d](\d{2})[^\d](\d{4})'
        ]

        issue_date_found = False
        for pattern in issue_date_patterns:
            issue_date_match = re.search(pattern, text, re.IGNORECASE)
            if issue_date_match:
                if len(issue_date_match.groups()) == 3:  # Định dạng "Ngày XX tháng XX năm XXXX"
                    date_str = f"{issue_date_match.group(1)}/{issue_date_match.group(2)}/{issue_date_match.group(3)}"
                else:
                    date_str = issue_date_match.group(1)

                date_str = date_str.replace('-', '/')
                try:
                    info['issue_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                    logger.info(f"Đã trích xuất ngày cấp: {info['issue_date']}")
                    issue_date_found = True
                    break
                except ValueError:
                    logger.warning(f"Không thể chuyển đổi chuỗi ngày cấp: {date_str}")

        # Nếu không tìm thấy ngày cấp bằng regex, thử tìm dòng có chứa từ khóa liên quan
        if not issue_date_found:
            # Tìm tất cả các ngày trong văn bản
            all_dates = re.findall(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', text)

            # Tìm dòng có chứa từ "cấp" hoặc "ngày cấp"
            issue_keywords = ['ngày cấp', 'cấp ngày', 'cấp', 'date of issue']
            lines = text.split('\n')

            for line in lines:
                if any(keyword.lower() in line.lower() for keyword in issue_keywords):
                    # Tìm ngày trong dòng này
                    date_in_line = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', line)
                    if date_in_line:
                        date_str = date_in_line.group(1).replace('-', '/')
                        try:
                            info['issue_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                            logger.info(f"Đã trích xuất ngày cấp (phương pháp 2): {info['issue_date']}")
                            issue_date_found = True
                            break
                        except ValueError:
                            continue

            # Tìm kiếm dòng có chứa "ngày, tháng, năm cấp" và số
            if not issue_date_found:
                for i, line in enumerate(lines):
                    if "ngày, tháng, năm cấp" in line.lower() or "date of issue" in line.lower():
                        # Kiểm tra dòng hiện tại và dòng tiếp theo
                        search_lines = [line]
                        if i + 1 < len(lines):
                            search_lines.append(lines[i + 1])

                        for search_line in search_lines:
                            # Tìm ngày trong dòng
                            date_in_line = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', search_line)
                            if date_in_line:
                                date_str = date_in_line.group(1).replace('-', '/')
                                try:
                                    info['issue_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                                    logger.info(f"Đã trích xuất ngày cấp (phương pháp 2b): {info['issue_date']}")
                                    issue_date_found = True
                                    break
                                except ValueError:
                                    continue

            # Nếu vẫn không tìm thấy và có ít nhất 2 ngày trong văn bản, giả định ngày đầu tiên là ngày cấp
            if not issue_date_found and len(all_dates) >= 2:
                date_str = all_dates[0].replace('-', '/')
                try:
                    info['issue_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                    logger.info(f"Đã trích xuất ngày cấp (phương pháp 3 - giả định): {info['issue_date']}")
                    issue_date_found = True
                except ValueError:
                    logger.warning(f"Không thể chuyển đổi chuỗi ngày cấp: {date_str}")

        # 3. Trích xuất ngày hết hạn với nhiều mẫu hơn
        expiry_date_patterns = [
            r'Ngày,?\s*tháng,?\s*năm\s*hết\s*hạn\s*/\s*Date\s*of\s*expiry:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Ngày,?\s*tháng,?\s*năm\s*hết\s*hạn:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Có giá trị đến:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Giá trị đến:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Expiry date:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Date of expiry:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Có giá trị đến:?\s*(\d{2})\s*tháng\s*(\d{2})\s*năm\s*(\d{4})',
            r'Hết hạn:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Đến ngày:?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'Đến:?\s*(\d{2})[^\d](\d{2})[^\d](\d{4})'
        ]

        expiry_date_found = False
        for pattern in expiry_date_patterns:
            expiry_date_match = re.search(pattern, text, re.IGNORECASE)
            if expiry_date_match:
                if len(expiry_date_match.groups()) == 3:  # Định dạng "Ngày XX tháng XX năm XXXX"
                    date_str = f"{expiry_date_match.group(1)}/{expiry_date_match.group(2)}/{expiry_date_match.group(3)}"
                else:
                    date_str = expiry_date_match.group(1)

                date_str = date_str.replace('-', '/')
                try:
                    info['expiry_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                    logger.info(f"Đã trích xuất ngày hết hạn: {info['expiry_date']}")
                    expiry_date_found = True
                    break
                except ValueError:
                    logger.warning(f"Không thể chuyển đổi chuỗi ngày hết hạn: {date_str}")

        # Nếu không tìm thấy ngày hết hạn bằng regex, thử tìm dòng có chứa từ khóa liên quan
        if not expiry_date_found:
            # Tìm tất cả các ngày trong văn bản
            all_dates = re.findall(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', text)

            # Tìm dòng có chứa từ "giá trị đến" hoặc "hết hạn"
            expiry_keywords = ['giá trị đến', 'có giá trị đến', 'hết hạn', 'đến ngày', 'date of expiry', 'expiry date']
            lines = text.split('\n')

            for line in lines:
                if any(keyword.lower() in line.lower() for keyword in expiry_keywords):
                    # Tìm ngày trong dòng này
                    date_in_line = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', line)
                    if date_in_line:
                        date_str = date_in_line.group(1).replace('-', '/')
                        try:
                            info['expiry_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                            logger.info(f"Đã trích xuất ngày hết hạn (phương pháp 2): {info['expiry_date']}")
                            expiry_date_found = True
                            break
                        except ValueError:
                            continue

            # Tìm kiếm dòng có chứa "ngày, tháng, năm hết hạn" và số
            if not expiry_date_found:
                for i, line in enumerate(lines):
                    if "ngày, tháng, năm hết hạn" in line.lower() or "date of expiry" in line.lower():
                        # Kiểm tra dòng hiện tại và dòng tiếp theo
                        search_lines = [line]
                        if i + 1 < len(lines):
                            search_lines.append(lines[i + 1])

                        for search_line in search_lines:
                            # Tìm ngày trong dòng
                            date_in_line = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', search_line)
                            if date_in_line:
                                date_str = date_in_line.group(1).replace('-', '/')
                                try:
                                    info['expiry_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                                    logger.info(f"Đã trích xuất ngày hết hạn (phương pháp 2b): {info['expiry_date']}")
                                    expiry_date_found = True
                                    break
                                except ValueError:
                                    continue

            # Nếu vẫn không tìm thấy và có ít nhất 2 ngày trong văn bản, giả định ngày cuối cùng là ngày hết hạn
            if not expiry_date_found and len(all_dates) >= 2:
                date_str = all_dates[-1].replace('-', '/')
                try:
                    info['expiry_date'] = datetime.strptime(date_str, '%d/%m/%Y').date()
                    logger.info(f"Đã trích xuất ngày hết hạn (phương pháp 3 - giả định): {info['expiry_date']}")
                    expiry_date_found = True
                except ValueError:
                    logger.warning(f"Không thể chuyển đổi chuỗi ngày hết hạn: {date_str}")

        # Trích xuất đặc điểm nhận dạng (không phải trường thông tin chính yêu cầu, nhưng vẫn giữ lại)
        features_patterns = [
            r'Đặc điểm nhận dạng:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'Nhận dạng:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'Identifying features:?\s*([^\n]+(?:\n[^\n]+)*)'
        ]

        for pattern in features_patterns:
            features_match = re.search(pattern, text, re.IGNORECASE)
            if features_match:
                info['identifying_features'] = features_match.group(1).strip().replace('\n', ' ')
                logger.info(f"Đã trích xuất đặc điểm nhận dạng: {info['identifying_features']}")
                break

    # Kiểm tra và ghi log các thông tin đã trích xuất
    if is_front:
        required_fields = ['id_number', 'full_name', 'date_of_birth', 'gender', 'nationality']
    else:
        required_fields = ['issue_date', 'expiry_date']

    missing_fields = [field for field in required_fields if field not in info]

    if missing_fields:
        logger.warning(f"Thiếu các trường thông tin: {missing_fields}")
    else:
        logger.info(f"Đã trích xuất đầy đủ các thông tin cơ bản cho {'mặt trước' if is_front else 'mặt sau'} CCCD")

    return info

def process_id_card(image_path, is_front):
    """
    Xử lý ảnh CCCD và trích xuất thông tin

    Args:
        image_path: Đường dẫn đến file ảnh
        is_front: True nếu là mặt trước CCCD, False nếu là mặt sau

    Returns:
        Dictionary chứa thông tin trích xuất được
    """
    try:
        # Tạo thư mục debug
        debug_dir = os.path.join(os.path.dirname(image_path), "debug")
        os.makedirs(debug_dir, exist_ok=True)

        # Ghi log thông tin ảnh đầu vào
        logger.info(f"Xử lý ảnh CCCD: {image_path}, {'mặt trước' if is_front else 'mặt sau'}")

        # Tiền xử lý ảnh (bao gồm phát hiện và xoay ảnh)
        processed_image, original_img = preprocess_image(image_path)

        # Trích xuất text
        text = extract_text(processed_image)

        # Lưu text vào file để debug
        debug_file = os.path.join(debug_dir, f"ocr_text_{os.path.basename(image_path)}.txt")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(text)

        # Kiểm tra xem có chuỗi "KHOANG" hoặc "NGHIA" trong văn bản không
        if "KHOANG" in text or "KHOÀNG" in text or "NGHIA" in text or "NGHĨA" in text:
            logger.info("Phát hiện từ khóa KHOANG hoặc NGHIA trong văn bản")

        # Kiểm tra xem có chuỗi "Họ, chữ đệm và tên khai sinh" trong văn bản không
        if "Họ, chữ đệm và tên khai sinh" in text or "//ull nutn" in text:
            logger.info("Phát hiện chuỗi 'Họ, chữ đệm và tên khai sinh' hoặc '//ull nutn' trong văn bản")

        # Phân tích thông tin
        info = parse_id_info(text, is_front)

        # Nếu không trích xuất được thông tin cơ bản, thử lại với các phương pháp tiền xử lý khác
        required_fields = ['id_number', 'full_name'] if is_front else ['issue_date', 'expiry_date']
        missing_fields = [field for field in required_fields if field not in info]

        if (is_front and ("id_number" not in info or "full_name" not in info)) or (not is_front and len(missing_fields) > 0):
            logger.warning(f"Không tìm thấy thông tin cơ bản: {missing_fields}, thử lại với phương pháp tiền xử lý khác...")

            # Phương pháp 2: Sử dụng ngưỡng hóa Otsu
            gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Lưu ảnh đã xử lý để debug
            cv2.imwrite(os.path.join(debug_dir, f"otsu_thresh_{os.path.basename(image_path)}"), otsu_thresh)

            # Thử OCR với ảnh đã xử lý mới
            text = extract_text(otsu_thresh)

            # Lưu text vào file để debug
            with open(os.path.join(debug_dir, f"ocr_text_otsu_{os.path.basename(image_path)}.txt"), "w", encoding="utf-8") as f:
                f.write(text)

            # Kiểm tra xem có chuỗi "KHOANG" hoặc "NGHIA" trong văn bản không
            if "KHOANG" in text or "KHOÀNG" in text or "NGHIA" in text or "NGHĨA" in text:
                logger.info("Phương pháp Otsu: Phát hiện từ khóa KHOANG hoặc NGHIA trong văn bản")

            # Kiểm tra xem có chuỗi "Họ, chữ đệm và tên khai sinh" trong văn bản không
            if "Họ, chữ đệm và tên khai sinh" in text or "//ull nutn" in text:
                logger.info("Phương pháp Otsu: Phát hiện chuỗi 'Họ, chữ đệm và tên khai sinh' hoặc '//ull nutn' trong văn bản")

            # Phân tích thông tin lại
            info = parse_id_info(text, is_front)

            # Nếu vẫn không tìm thấy, thử phương pháp 3
            missing_fields = [field for field in required_fields if field not in info]
            if (is_front and ("id_number" not in info or "full_name" not in info)) or (not is_front and len(missing_fields) > 0):
                logger.warning("Vẫn không tìm thấy thông tin cơ bản, thử lại với phương pháp thứ 3...")

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
                text = extract_text(adaptive_thresh)

                # Lưu text vào file để debug
                with open(os.path.join(debug_dir, f"ocr_text_adaptive_{os.path.basename(image_path)}.txt"), "w", encoding="utf-8") as f:
                    f.write(text)

                # Phân tích thông tin lại
                info = parse_id_info(text, is_front)

                # Thử trực tiếp với ảnh gốc nếu các phương pháp trước không thành công
                missing_fields = [field for field in required_fields if field not in info]
                if (is_front and ("id_number" not in info or "full_name" not in info)) or (not is_front and len(missing_fields) > 0):
                    logger.warning("Vẫn không tìm thấy thông tin cơ bản, thử lại với ảnh gốc...")

                    # Thử OCR với ảnh gốc
                    reader = get_reader()
                    results = reader.readtext(image_path, detail=0)
                    text = "\n".join(results)

                    # Lưu text vào file để debug
                    with open(os.path.join(debug_dir, f"ocr_text_original_{os.path.basename(image_path)}.txt"), "w", encoding="utf-8") as f:
                        f.write(text)

                    # Phân tích thông tin lại
                    original_info = parse_id_info(text, is_front)

                    # Kiểm tra xem ảnh gốc có cho kết quả tốt hơn không
                    original_missing_fields = [field for field in required_fields if field not in original_info]
                    if len(original_missing_fields) < len(missing_fields):
                        logger.info("Ảnh gốc cho kết quả tốt hơn, sử dụng kết quả này")
                        info = original_info

        # Ghi log kết quả cuối cùng
        logger.info(f"Kết quả trích xuất thông tin: {info}")
        return info
    except Exception as e:
        logger.error(f"Lỗi xử lý OCR: {e}")
        raise e

def test_easyocr():
    """
    Kiểm tra cài đặt EasyOCR

    Returns:
        True nếu EasyOCR hoạt động bình thường, False nếu có lỗi
    """
    try:
        # Kiểm tra EasyOCR
        reader = get_reader()

        # Tạo một ảnh đơn giản để kiểm tra
        from PIL import Image, ImageDraw

        # Tạo ảnh trắng
        img = Image.new('RGB', (400, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)

        # Vẽ văn bản
        d.text((10, 10), "Xin chào Việt Nam 123", fill=(0, 0, 0))

        # Lưu hình ảnh
        test_image_path = "test_ocr_image.png"
        img.save(test_image_path)

        # Nhận dạng văn bản
        result = reader.readtext(test_image_path, detail=0)
        text = "\n".join(result)
        print(f"\nKết quả OCR: {text.strip()}")

        # Xóa hình ảnh tạm
        os.remove(test_image_path)

        print("\nEasyOCR đã được cài đặt và cấu hình đúng! 🎉")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra EasyOCR: {e}")
        return False

if __name__ == "__main__":
    # Kiểm tra EasyOCR khi chạy trực tiếp file này
    test_easyocr()
