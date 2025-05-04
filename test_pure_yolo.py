"""
Script để kiểm thử hệ thống xác thực khuôn mặt chỉ sử dụng YOLOv11
"""
import os
import sys
import cv2
import logging
import argparse
import numpy as np
from verification_models.yolo_face_recognition import YOLOFaceRecognition

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_face_detection(image_path, output_dir=None, confidence=0.5):
    """
    Kiểm thử phát hiện khuôn mặt bằng YOLOv11

    Args:
        image_path: Đường dẫn đến ảnh cần phát hiện khuôn mặt
        output_dir: Thư mục để lưu ảnh kết quả
        confidence: Ngưỡng tin cậy cho việc phát hiện khuôn mặt
    """
    try:
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(image_path):
            logger.error(f"Không tìm thấy file: {image_path}")
            return False

        # Khởi tạo YOLOFaceRecognition
        yolo_face = YOLOFaceRecognition(confidence=confidence)

        # Phát hiện khuôn mặt
        logger.info(f"Đang phát hiện khuôn mặt trong ảnh: {image_path}")
        faces, image = yolo_face.detect_faces(image_path)

        if len(faces) == 0:
            logger.warning(f"Không tìm thấy khuôn mặt trong ảnh: {image_path}")
            return False

        logger.info(f"Đã phát hiện {len(faces)} khuôn mặt trong ảnh")

        # Vẽ các khuôn mặt phát hiện được
        if image is not None:
            for i, (x1, y1, x2, y2) in enumerate(faces):
                # Vẽ bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Hiển thị số thứ tự của khuôn mặt
                cv2.putText(image, f"Face #{i+1}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Lưu ảnh kết quả nếu có output_dir
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"detected_{os.path.basename(image_path)}")
                cv2.imwrite(output_path, image)
                logger.info(f"Đã lưu ảnh kết quả tại: {output_path}")

            # Hiển thị ảnh
            cv2.imshow("Detected Faces", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # Trích xuất đặc trưng khuôn mặt
        logger.info("Đang trích xuất đặc trưng khuôn mặt...")
        face_encoding, face_location, success, message = yolo_face.extract_face_encoding(image_path)

        if not success:
            logger.warning(f"Không thể trích xuất đặc trưng khuôn mặt: {message}")
            return False

        logger.info(f"Đã trích xuất đặc trưng khuôn mặt thành công: {message}")

        return True

    except Exception as e:
        logger.error(f"Lỗi khi kiểm thử phát hiện khuôn mặt: {str(e)}")
        return False

def test_face_verification(id_card_path, selfie_path, output_dir=None, tolerance=0.45):
    """
    Kiểm thử xác thực khuôn mặt bằng YOLOv11

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD
        selfie_path: Đường dẫn đến ảnh selfie
        output_dir: Thư mục để lưu ảnh kết quả
        tolerance: Ngưỡng dung sai để xem xét khuôn mặt khớp nhau
    """
    try:
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(id_card_path):
            logger.error(f"Không tìm thấy file CCCD: {id_card_path}")
            return False

        if not os.path.exists(selfie_path):
            logger.error(f"Không tìm thấy file selfie: {selfie_path}")
            return False

        # Khởi tạo YOLOFaceRecognition
        yolo_face = YOLOFaceRecognition()

        # Xác thực khuôn mặt
        logger.info(f"Đang xác thực khuôn mặt giữa CCCD ({id_card_path}) và selfie ({selfie_path})")
        result = yolo_face.verify_face_match(id_card_path, selfie_path, tolerance)

        # Hiển thị kết quả
        logger.info("=== Kết quả xác thực khuôn mặt ===")
        logger.info(f"Thành công: {result['success']}")
        logger.info(f"Khớp: {result['match']}")
        logger.info(f"Khoảng cách: {result['distance']}")
        logger.info(f"Thông báo: {result['message']}")
        logger.info(f"Tìm thấy khuôn mặt trong CCCD: {result['id_card_face_found']}")
        logger.info(f"Tìm thấy khuôn mặt trong selfie: {result['selfie_face_found']}")

        # Tạo ảnh kết quả nếu có output_dir
        if output_dir and result['success']:
            os.makedirs(output_dir, exist_ok=True)

            # Đọc ảnh
            id_card_image = cv2.imread(id_card_path)
            selfie_image = cv2.imread(selfie_path)

            if id_card_image is not None and selfie_image is not None:
                # Phát hiện khuôn mặt
                id_card_faces, _ = yolo_face.detect_faces(id_card_path)
                selfie_faces, _ = yolo_face.detect_faces(selfie_path)

                # Vẽ khuôn mặt lên ảnh
                if len(id_card_faces) > 0:
                    x1, y1, x2, y2 = id_card_faces[0]
                    cv2.rectangle(id_card_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(id_card_image, "ID Card Face", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                if len(selfie_faces) > 0:
                    x1, y1, x2, y2 = selfie_faces[0]
                    color = (0, 255, 0) if result['match'] else (0, 0, 255)
                    cv2.rectangle(selfie_image, (x1, y1), (x2, y2), color, 2)
                    status = "Match" if result['match'] else "No Match"
                    cv2.putText(selfie_image, f"Selfie Face: {status}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Resize ảnh để có cùng chiều cao
                height = min(id_card_image.shape[0], selfie_image.shape[0])
                id_card_resized = cv2.resize(id_card_image, (int(id_card_image.shape[1] * height / id_card_image.shape[0]), height))
                selfie_resized = cv2.resize(selfie_image, (int(selfie_image.shape[1] * height / selfie_image.shape[0]), height))

                # Ghép ảnh
                result_image = np.hstack((id_card_resized, selfie_resized))

                # Thêm thông tin kết quả
                result_text = f"Match: {result['match']}, Distance: {result['distance']:.4f}, Tolerance: {tolerance}"
                cv2.putText(result_image, result_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Lưu ảnh kết quả
                output_path = os.path.join(output_dir, "verification_result.jpg")
                cv2.imwrite(output_path, result_image)
                logger.info(f"Đã lưu ảnh kết quả tại: {output_path}")

                # Hiển thị ảnh
                cv2.imshow("Verification Result", result_image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

        return result['success']

    except Exception as e:
        logger.error(f"Lỗi khi kiểm thử xác thực khuôn mặt: {str(e)}")
        return False

def test_multiple_face_verification(id_card_path, selfie_paths, output_dir=None, tolerance=0.45):
    """
    Kiểm thử xác thực khuôn mặt với nhiều ảnh selfie so với một ảnh CCCD

    Args:
        id_card_path: Đường dẫn đến ảnh CCCD
        selfie_paths: Danh sách các đường dẫn đến ảnh selfie
        output_dir: Thư mục để lưu ảnh kết quả
        tolerance: Ngưỡng dung sai để xem xét khuôn mặt khớp nhau
    """
    try:
        # Kiểm tra xem file CCCD có tồn tại không
        if not os.path.exists(id_card_path):
            logger.error(f"Không tìm thấy file CCCD: {id_card_path}")
            return False

        # Khởi tạo YOLOFaceRecognition
        yolo_face = YOLOFaceRecognition()

        # Trích xuất đặc trưng khuôn mặt từ CCCD
        logger.info(f"Đang trích xuất đặc trưng khuôn mặt từ CCCD: {id_card_path}")
        id_card_encoding, id_card_location, id_card_success, id_card_message = yolo_face.extract_face_encoding(id_card_path)

        if not id_card_success:
            logger.error(f"Không thể trích xuất khuôn mặt từ CCCD: {id_card_message}")
            return False

        logger.info(f"Đã trích xuất khuôn mặt từ CCCD thành công")

        # Tạo thư mục output nếu cần
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Đọc ảnh CCCD
        id_card_image = cv2.imread(id_card_path)

        # Vẽ khuôn mặt lên ảnh CCCD
        if id_card_image is not None and id_card_location is not None:
            x1, y1, x2, y2 = id_card_location
            cv2.rectangle(id_card_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(id_card_image, "ID Card Face", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Lưu ảnh CCCD với khuôn mặt được đánh dấu
        if output_dir and id_card_image is not None:
            id_card_output_path = os.path.join(output_dir, f"id_card_{os.path.basename(id_card_path)}")
            cv2.imwrite(id_card_output_path, id_card_image)
            logger.info(f"Đã lưu ảnh CCCD với khuôn mặt được đánh dấu tại: {id_card_output_path}")

        # Kiểm tra từng ảnh selfie
        results = []
        for i, selfie_path in enumerate(selfie_paths):
            # Kiểm tra xem file selfie có tồn tại không
            if not os.path.exists(selfie_path):
                logger.error(f"Không tìm thấy file selfie: {selfie_path}")
                continue

            logger.info(f"\n=== Kiểm tra ảnh selfie {i+1}: {selfie_path} ===")

            # Xác thực khuôn mặt
            result = yolo_face.verify_face_match(id_card_path, selfie_path, tolerance)

            # Hiển thị kết quả
            logger.info(f"Thành công: {result['success']}")
            logger.info(f"Khớp: {result['match']}")
            logger.info(f"Khoảng cách: {result['distance']}")
            logger.info(f"Thông báo: {result['message']}")
            logger.info(f"Tìm thấy khuôn mặt trong selfie: {result['selfie_face_found']}")

            # Tạo ảnh kết quả
            if output_dir and result['success']:
                # Đọc ảnh selfie
                selfie_image = cv2.imread(selfie_path)

                if selfie_image is not None:
                    # Phát hiện khuôn mặt trong ảnh selfie
                    selfie_faces, _ = yolo_face.detect_faces(selfie_path)

                    # Vẽ khuôn mặt lên ảnh selfie
                    if len(selfie_faces) > 0:
                        x1, y1, x2, y2 = selfie_faces[0]
                        color = (0, 255, 0) if result['match'] else (0, 0, 255)
                        cv2.rectangle(selfie_image, (x1, y1), (x2, y2), color, 2)
                        status = "Match" if result['match'] else "No Match"
                        cv2.putText(selfie_image, f"Selfie Face: {status}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    # Resize ảnh để có cùng chiều cao
                    height = min(id_card_image.shape[0], selfie_image.shape[0])
                    id_card_resized = cv2.resize(id_card_image.copy(), (int(id_card_image.shape[1] * height / id_card_image.shape[0]), height))
                    selfie_resized = cv2.resize(selfie_image, (int(selfie_image.shape[1] * height / selfie_image.shape[0]), height))

                    # Ghép ảnh
                    result_image = np.hstack((id_card_resized, selfie_resized))

                    # Thêm thông tin kết quả
                    result_text = f"Match: {result['match']}, Distance: {result['distance']:.4f}, Tolerance: {tolerance}"
                    cv2.putText(result_image, result_text, (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    # Lưu ảnh kết quả
                    output_path = os.path.join(output_dir, f"verification_result_{i+1}_{os.path.basename(selfie_path)}")
                    cv2.imwrite(output_path, result_image)
                    logger.info(f"Đã lưu ảnh kết quả tại: {output_path}")

                    # Hiển thị ảnh
                    cv2.imshow(f"Verification Result {i+1}", result_image)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

            # Lưu kết quả
            results.append({
                'selfie_path': selfie_path,
                'success': result['success'],
                'match': result['match'],
                'distance': result['distance'],
                'message': result['message']
            })

        # Hiển thị tổng kết
        logger.info("\n=== Tổng kết kết quả xác thực khuôn mặt ===")
        for i, result in enumerate(results):
            match_status = "KHỚP" if result['match'] else "KHÔNG KHỚP"
            logger.info(f"Ảnh {i+1}: {os.path.basename(result['selfie_path'])} - {match_status} (Khoảng cách: {result['distance']:.4f})")

        return True

    except Exception as e:
        logger.error(f"Lỗi khi kiểm thử xác thực khuôn mặt với nhiều ảnh: {str(e)}")
        return False

def main():
    # Tạo parser cho command line arguments
    parser = argparse.ArgumentParser(description="Kiểm thử hệ thống xác thực khuôn mặt chỉ sử dụng YOLOv11")
    parser.add_argument("--mode", type=str, choices=["detection", "verification", "multi-verification"], required=True, help="Chế độ kiểm thử")
    parser.add_argument("--image", type=str, help="Đường dẫn đến ảnh cần phát hiện khuôn mặt (cho chế độ detection)")
    parser.add_argument("--id-card", type=str, help="Đường dẫn đến ảnh CCCD (cho chế độ verification và multi-verification)")
    parser.add_argument("--selfie", type=str, help="Đường dẫn đến ảnh selfie (cho chế độ verification)")
    parser.add_argument("--selfies", type=str, nargs='+', help="Danh sách các đường dẫn đến ảnh selfie (cho chế độ multi-verification)")
    parser.add_argument("--output", type=str, default="test_results", help="Thư mục để lưu ảnh kết quả")
    parser.add_argument("--confidence", type=float, default=0.5, help="Ngưỡng tin cậy cho việc phát hiện khuôn mặt")
    parser.add_argument("--tolerance", type=float, default=0.45, help="Ngưỡng dung sai cho việc so sánh khuôn mặt")

    # Parse arguments
    args = parser.parse_args()

    # Kiểm thử theo chế độ
    if args.mode == "detection":
        if not args.image:
            logger.error("Thiếu tham số --image cho chế độ detection")
            sys.exit(1)

        success = test_face_detection(args.image, args.output, args.confidence)

        if success:
            logger.info("Kiểm thử phát hiện khuôn mặt thành công!")
        else:
            logger.error("Kiểm thử phát hiện khuôn mặt thất bại!")

    elif args.mode == "verification":
        if not args.id_card or not args.selfie:
            logger.error("Thiếu tham số --id-card hoặc --selfie cho chế độ verification")
            sys.exit(1)

        success = test_face_verification(args.id_card, args.selfie, args.output, args.tolerance)

        if success:
            logger.info("Kiểm thử xác thực khuôn mặt thành công!")
        else:
            logger.error("Kiểm thử xác thực khuôn mặt thất bại!")

    elif args.mode == "multi-verification":
        if not args.id_card or not args.selfies:
            logger.error("Thiếu tham số --id-card hoặc --selfies cho chế độ multi-verification")
            sys.exit(1)

        success = test_multiple_face_verification(args.id_card, args.selfies, args.output, args.tolerance)

        if success:
            logger.info("Kiểm thử xác thực khuôn mặt với nhiều ảnh thành công!")
        else:
            logger.error("Kiểm thử xác thực khuôn mặt với nhiều ảnh thất bại!")

if __name__ == "__main__":
    main()
