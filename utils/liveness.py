import cv2
import numpy as np  # Sử dụng trong preprocess_frame
import dlib
from imutils import face_utils
from scipy.spatial import distance as dist
import os
import time

# Khởi tạo face detector và facial landmark predictor
face_detector = dlib.get_frontal_face_detector()
predictor_path = os.path.join(os.path.dirname(__file__), 'models', 'shape_predictor_68_face_landmarks.dat')
landmark_predictor = dlib.shape_predictor(predictor_path)

def eye_aspect_ratio(eye):
    # Tính tỉ lệ khung mắt dựa trên landmarks
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def detect_blinks(video_path):
    """
    Phát hiện nháy mắt trong video

    Args:
        video_path: Đường dẫn đến file video

    Returns:
        Dictionary chứa kết quả phân tích
    """
    # Các tham số cho thuật toán phát hiện nháy mắt
    EYE_AR_THRESH = 0.13  # Ngưỡng tỉ lệ khung mắt để phát hiện nháy mắt (giảm xuống để nghiêm ngặt hơn)
    EYE_AR_CONSEC_FRAMES = 2  # Số frame liên tiếp cần thiết để xác định nháy mắt (tăng lên để chính xác hơn)

    # Biến toàn cục để tính EAR trung bình
    global_ear_values = []

    # Tạo thư mục debug
    debug_dir = os.path.join(os.path.dirname(video_path), "debug_frames")
    os.makedirs(debug_dir, exist_ok=True)

    # Xóa các file log cũ
    for file_name in ["ear_values.txt", "blink_frames.txt", "blinks.txt", "liveness_results.txt", "blink_thresholds.txt", "blinks_method2.txt", "blinks_method3.txt"]:
        log_file = os.path.join(debug_dir, file_name)
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                print(f"Đã xóa file log cũ: {log_file}")
            except Exception as e:
                print(f"Không thể xóa file log cũ {log_file}: {e}")

    # Ghi log bắt đầu phân tích
    with open(os.path.join(debug_dir, "analysis_log.txt"), "w", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bắt đầu phân tích video: {video_path}\n")

    # Đọc video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        error_msg = f"Không thể mở video: {video_path}"
        print(error_msg)
        with open(os.path.join(debug_dir, "error_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}\n")
        raise Exception(error_msg)

    # Lấy thông tin video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Ghi log thông tin video
    with open(os.path.join(debug_dir, "video_details.txt"), "w", encoding="utf-8") as f:
        f.write(f"Video path: {video_path}\n")
        f.write(f"Resolution: {width}x{height}\n")
        f.write(f"FPS: {fps}\n")
        f.write(f"Total frames: {total_frames}\n")
        f.write(f"Duration: {total_frames/fps:.2f} seconds\n")

    # Khởi tạo các biến
    blink_counter = 0
    counter = 0
    total_ear = 0
    frame_count = 0
    face_detected_frames = 0
    rotated_frames_count = 0  # Số frame đã được xoay

    # Xóa file log xoay cũ nếu có
    rotation_log_path = os.path.join(debug_dir, "rotation_log.txt")
    if os.path.exists(rotation_log_path):
        try:
            os.remove(rotation_log_path)
            print(f"Đã xóa file log xoay cũ: {rotation_log_path}")
        except Exception as e:
            print(f"Không thể xóa file log xoay cũ {rotation_log_path}: {e}")

    # Danh sách lưu các frame có khuôn mặt để xử lý
    face_frames = []

    # Đọc tất cả các frame
    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Kiểm tra kích thước frame
        if frame.shape[0] == 0 or frame.shape[1] == 0:
            print(f"Frame {frame_index} có kích thước không hợp lệ: {frame.shape}")
            frame_index += 1
            continue

        # Tăng kích thước frame để có độ phân giải tốt hơn (nếu cần)
        if width < 480 or height < 480:
            frame = cv2.resize(frame, (640, 640))

        # Tiền xử lý frame để cải thiện chất lượng
        enhanced_frame = preprocess_frame(frame)

        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2GRAY)

        # Phát hiện khuôn mặt
        faces = face_detector(gray, 0)

        # Nếu không phát hiện được khuôn mặt, thử xoay frame và phát hiện lại
        if len(faces) == 0:
            # Kiểm tra xem frame có bị ngang không (chiều rộng > chiều cao)
            if enhanced_frame.shape[1] > enhanced_frame.shape[0]:
                # Thử xoay frame 90 độ theo chiều kim đồng hồ
                rotated_frame = cv2.rotate(enhanced_frame, cv2.ROTATE_90_CLOCKWISE)
                rotated_gray = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2GRAY)
                rotated_faces = face_detector(rotated_gray, 0)

                # Nếu phát hiện được khuôn mặt sau khi xoay, sử dụng frame đã xoay
                if len(rotated_faces) > 0:
                    enhanced_frame = rotated_frame
                    gray = rotated_gray
                    faces = rotated_faces
                    # Lưu frame gốc và frame đã xoay để debug
                    cv2.imwrite(os.path.join(debug_dir, f"original_frame_{frame_index}.jpg"), frame)
                    cv2.imwrite(os.path.join(debug_dir, f"rotated_frame_{frame_index}.jpg"), rotated_frame)
                    with open(os.path.join(debug_dir, "rotation_log.txt"), "a", encoding="utf-8") as f:
                        f.write(f"Frame {frame_index}: Đã xoay 90 độ CW và phát hiện {len(rotated_faces)} khuôn mặt\n")
                    rotated_frames_count += 1
                else:
                    # Thử xoay frame 90 độ ngược chiều kim đồng hồ
                    rotated_frame = cv2.rotate(enhanced_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    rotated_gray = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2GRAY)
                    rotated_faces = face_detector(rotated_gray, 0)

                    # Nếu phát hiện được khuôn mặt sau khi xoay, sử dụng frame đã xoay
                    if len(rotated_faces) > 0:
                        enhanced_frame = rotated_frame
                        gray = rotated_gray
                        faces = rotated_faces
                        # Lưu frame gốc và frame đã xoay để debug
                        cv2.imwrite(os.path.join(debug_dir, f"original_frame_{frame_index}.jpg"), frame)
                        cv2.imwrite(os.path.join(debug_dir, f"rotated_frame_{frame_index}.jpg"), rotated_frame)
                        with open(os.path.join(debug_dir, "rotation_log.txt"), "a", encoding="utf-8") as f:
                            f.write(f"Frame {frame_index}: Đã xoay 90 độ CCW và phát hiện {len(rotated_faces)} khuôn mặt\n")
                        rotated_frames_count += 1

        # Lưu frame có khuôn mặt để xử lý
        if len(faces) > 0:
            face_detected_frames += 1
            face_frames.append((frame_index, enhanced_frame, gray, faces))

            # Lưu frame để debug (chỉ lưu một số frame)
            if frame_index % 10 == 0 or len(face_frames) < 10:
                cv2.imwrite(os.path.join(debug_dir, f"frame_{frame_index}.jpg"), enhanced_frame)

                # Vẽ hình chữ nhật xung quanh khuôn mặt
                debug_frame = enhanced_frame.copy()
                for face in faces:
                    x, y, w, h = face.left(), face.top(), face.width(), face.height()
                    cv2.rectangle(debug_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imwrite(os.path.join(debug_dir, f"face_detected_{frame_index}.jpg"), debug_frame)

        frame_index += 1

        # Hiển thị tiến trình xử lý
        if frame_index % 30 == 0:
            print(f"Đã xử lý {frame_index}/{total_frames} frames ({frame_index/total_frames*100:.1f}%)")

    # Đóng video sau khi đọc xong
    cap.release()

    # Ghi log số frame đã xử lý
    with open(os.path.join(debug_dir, "analysis_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Đã xử lý {frame_index} frames, phát hiện khuôn mặt trong {face_detected_frames} frames\n")

    # Nếu không phát hiện đủ frame có khuôn mặt
    if face_detected_frames < 10:
        print(f"Chỉ phát hiện được {face_detected_frames} frame có khuôn mặt, không đủ để phân tích")
        return {
            'liveness_score': 0.0,
            'blink_count': 0,
            'avg_ear': 0.0,
            'blink_rate': 0.0,
            'face_detected_frames': face_detected_frames,
            'rotated_frames_count': rotated_frames_count
        }

    # Khởi tạo các biến cho phân tích nháy mắt
    blink_counter = 0
    counter = 0
    total_ear = 0
    frame_count = 0
    global_ear_values = []

    # Các tham số cho thuật toán phát hiện nháy mắt
    EYE_AR_THRESH = 0.13  # Ngưỡng tỉ lệ khung mắt để phát hiện nháy mắt (giảm xuống để nghiêm ngặt hơn)
    EYE_AR_CONSEC_FRAMES = 2  # Số frame liên tiếp cần thiết để xác định nháy mắt (tăng lên để chính xác hơn)

    # Xử lý các frame có khuôn mặt để phát hiện nháy mắt
    for frame_index, enhanced_frame, gray, faces in face_frames:
        for face in faces:
            # Phát hiện facial landmarks
            shape = landmark_predictor(gray, face)
            shape = face_utils.shape_to_np(shape)

            # Lấy tọa độ của mắt
            (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
            (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]

            # Tính EAR cho cả 2 mắt
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0

            # Lưu debug thông tin EAR
            if frame_index % 5 == 0:
                # Vẽ đường viền mắt để debug
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                debug_frame = enhanced_frame.copy()
                cv2.drawContours(debug_frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(debug_frame, [rightEyeHull], -1, (0, 255, 0), 1)

                # Hiển thị giá trị EAR
                cv2.putText(debug_frame, f"EAR: {ear:.2f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Lưu frame đã được chỉnh sửa
                cv2.imwrite(os.path.join(debug_dir, f"eye_frame_{frame_index}.jpg"), debug_frame)

            total_ear += ear
            frame_count += 1

            # Lưu tất cả giá trị EAR để debug
            with open(os.path.join(debug_dir, "ear_values.txt"), "a", encoding="utf-8") as f:
                f.write(f"Frame {frame_index}: EAR = {ear:.4f}\n")

            # Lưu giá trị EAR vào danh sách toàn cục
            global_ear_values.append(ear)

            # Tính EAR trung bình hiện tại
            current_avg_ear = sum(global_ear_values) / len(global_ear_values) if global_ear_values else 0.25

            # Phương pháp 1: Phát hiện nháy mắt khi EAR nhỏ hơn ngưỡng
            if ear < EYE_AR_THRESH:
                counter += 1
                # Lưu frame khi phát hiện mắt nhắm
                cv2.imwrite(os.path.join(debug_dir, f"blink_detected_{frame_index}.jpg"), enhanced_frame)
                with open(os.path.join(debug_dir, "blink_frames.txt"), "a", encoding="utf-8") as f:
                    f.write(f"Blink detected at frame {frame_index}: EAR = {ear:.4f}\n")
            else:
                # Nếu đã phát hiện mắt nhắm trong ít nhất 1 frame, coi như đã nháy mắt
                if counter >= EYE_AR_CONSEC_FRAMES:
                    blink_counter += 1
                    # Lưu thông tin về nháy mắt được phát hiện
                    with open(os.path.join(debug_dir, "blinks.txt"), "a", encoding="utf-8") as f:
                        f.write(f"Blink #{blink_counter} detected at frame {frame_index}, lasted for {counter} frames\n")
                counter = 0

            # Phương pháp 2: Phát hiện nháy mắt khi EAR thấp hơn trung bình đáng kể
            # Tăng độ nghiêm ngặt của phương pháp 2
            if ear < current_avg_ear * 0.7 and ear < 0.18:  # Giảm ngưỡng xuống để nghiêm ngặt hơn
                # Phát hiện nháy mắt bằng phương pháp thứ hai
                with open(os.path.join(debug_dir, "blinks_method2.txt"), "a", encoding="utf-8") as f:
                    f.write(f"Potential blink detected at frame {frame_index} using method 2: ear={ear:.4f}, avg_ear={current_avg_ear:.4f}\n")

                # Chỉ tăng bộ đếm nếu chưa phát hiện bằng phương pháp khác và có ít nhất 3 frame đã được xử lý
                # Điều này giúp tránh phát hiện sai ở đầu video khi chưa có đủ dữ liệu
                if counter == 0 and blink_counter == 0 and frame_count > 10:
                    blink_counter += 1
                    with open(os.path.join(debug_dir, "blinks.txt"), "a", encoding="utf-8") as f:
                        f.write(f"Blink #{blink_counter} detected at frame {frame_index} using method 2\n")

            # Phương pháp 3: Phát hiện sự thay đổi đột ngột của EAR
            if frame_index > 0 and frame_index < len(face_frames) - 1:
                # Lấy giá trị EAR của frame trước nếu có
                prev_ear = None

                # Tìm frame trước có khuôn mặt
                for i in range(frame_index-1, max(0, frame_index-10), -1):
                    if i in [f[0] for f in face_frames]:
                        # Tính EAR cho frame trước
                        prev_frame = next((f for f in face_frames if f[0] == i), None)
                        if prev_frame:
                            prev_shape = landmark_predictor(prev_frame[2], prev_frame[3][0])
                            prev_shape = face_utils.shape_to_np(prev_shape)
                            prev_left_eye = prev_shape[lStart:lEnd]
                            prev_right_eye = prev_shape[rStart:rEnd]
                            prev_left_ear = eye_aspect_ratio(prev_left_eye)
                            prev_right_ear = eye_aspect_ratio(prev_right_eye)
                            prev_ear = (prev_left_ear + prev_right_ear) / 2.0
                            break

                # Nếu có sự thay đổi đột ngột của EAR (giảm rồi tăng), có thể là nháy mắt
                # Tăng ngưỡng thay đổi EAR để nghiêm ngặt hơn
                if prev_ear is not None and prev_ear - ear > 0.05 and ear < 0.15:
                    # Phát hiện nháy mắt bằng phương pháp thứ ba
                    with open(os.path.join(debug_dir, "blinks_method3.txt"), "a", encoding="utf-8") as f:
                        f.write(f"Potential blink detected at frame {frame_index} using method 3: prev_ear={prev_ear:.4f}, current_ear={ear:.4f}\n")

                    # Chỉ tăng bộ đếm nếu chưa phát hiện bằng phương pháp khác và có ít nhất 10 frame đã được xử lý
                    # Điều này giúp tránh phát hiện sai ở đầu video khi chưa có đủ dữ liệu
                    if counter == 0 and blink_counter == 0 and frame_count > 15:
                        # Kiểm tra thêm: EAR phải thấp hơn đáng kể so với trung bình
                        if ear < current_avg_ear * 0.7:
                            blink_counter += 1
                            with open(os.path.join(debug_dir, "blinks.txt"), "a", encoding="utf-8") as f:
                                f.write(f"Blink #{blink_counter} detected at frame {frame_index} using method 3\n")

    # Tính điểm số liveness
    avg_ear = total_ear / frame_count if frame_count > 0 else 0
    duration = total_frames / fps if fps > 0 else 0
    blink_rate = blink_counter / duration if duration > 0 else 0

    # Thêm bước kiểm tra chéo để xác nhận nháy mắt thực sự
    # Phân tích phân phối EAR để phát hiện nháy mắt thực sự
    if len(global_ear_values) > 10:
        # Sắp xếp các giá trị EAR
        sorted_ear_values = sorted(global_ear_values)

        # Tính phần trăm 10% giá trị EAR thấp nhất
        lowest_10_percent = sorted_ear_values[:int(len(sorted_ear_values) * 0.1)]
        lowest_10_percent_avg = sum(lowest_10_percent) / len(lowest_10_percent) if lowest_10_percent else 0

        # Tính phần trăm 50% giá trị EAR trung bình
        median_values = sorted_ear_values[int(len(sorted_ear_values) * 0.25):int(len(sorted_ear_values) * 0.75)]
        median_avg = sum(median_values) / len(median_values) if median_values else 0

        # Ghi log phân tích phân phối EAR
        with open(os.path.join(debug_dir, "ear_distribution.txt"), "w", encoding="utf-8") as f:
            f.write(f"Lowest 10% EAR average: {lowest_10_percent_avg:.4f}\n")
            f.write(f"Median 50% EAR average: {median_avg:.4f}\n")
            f.write(f"Ratio (lowest/median): {lowest_10_percent_avg/median_avg if median_avg > 0 else 0:.4f}\n")

        # Nếu tỉ lệ giữa giá trị thấp nhất và trung bình quá cao (> 0.85),
        # có thể không có nháy mắt thực sự (không có sự khác biệt đáng kể giữa các giá trị EAR)
        if lowest_10_percent_avg / median_avg > 0.85 and blink_counter > 0:
            # Ghi log cảnh báo
            with open(os.path.join(debug_dir, "blink_verification.txt"), "w", encoding="utf-8") as f:
                f.write("Cảnh báo: Có thể không có nháy mắt thực sự. Phân phối EAR quá đồng đều.\n")
                f.write(f"Blink count trước khi điều chỉnh: {blink_counter}\n")

            # Giảm số lần nháy mắt xuống 0 hoặc 1 tùy thuộc vào số lần đã phát hiện
            if blink_counter > 3:
                blink_counter = 1  # Vẫn cho 1 lần nháy mắt nếu đã phát hiện nhiều lần
            else:
                blink_counter = 0  # Không có nháy mắt nếu chỉ phát hiện ít lần

            with open(os.path.join(debug_dir, "blink_verification.txt"), "a", encoding="utf-8") as f:
                f.write(f"Blink count sau khi điều chỉnh: {blink_counter}\n")

    # Điều chỉnh ngưỡng nháy mắt dựa trên độ dài video
    min_blinks = 3  # Chỉ yêu cầu tối thiểu 1 nháy mắt
    max_blinks = 20  # Tăng giới hạn tối đa lên cao

    # Ghi log ngưỡng nháy mắt
    with open(os.path.join(debug_dir, "blink_thresholds.txt"), "w", encoding="utf-8") as f:
        f.write(f"Video duration: {duration:.2f} seconds\n")
        f.write(f"Min blinks required: {min_blinks}\n")
        f.write(f"Max blinks allowed: {max_blinks}\n")
        f.write(f"Actual blink count: {blink_counter}\n")
        f.write(f"Face detected frames: {face_detected_frames} / {total_frames}\n")
        f.write(f"Average EAR: {avg_ear:.4f}\n")

    # Tính điểm số nháy mắt - đơn giản hóa thuật toán
    blink_score = 0.0
    if blink_counter >= min_blinks:
        # Nếu phát hiện ít nhất 1 nháy mắt, cho điểm tối đa
        blink_score = 1.0
    else:
        # Nếu không phát hiện nháy mắt, cho điểm thấp nhất
        blink_score = 0.0

    # Luôn cho điểm cao nếu phát hiện ít nhất 3 nháy mắt
    if blink_counter >= 3:
        blink_score = 1.0

    # Tính điểm số EAR
    ear_score = 1.0 if 0.2 <= avg_ear <= 0.35 else max(0, 1 - abs(avg_ear - 0.275) / 0.275)

    # Tính điểm số tần suất nháy mắt
    rate_score = 1.0 if 0.2 <= blink_rate <= 0.4 else max(0, 1 - abs(blink_rate - 0.3) / 0.3)

    # Tính điểm số phát hiện khuôn mặt
    face_detection_ratio = face_detected_frames / total_frames if total_frames > 0 else 0
    face_score = min(1.0, face_detection_ratio * 1.5)  # Cho điểm cao hơn nếu phát hiện nhiều khuôn mặt

    # Tổng hợp điểm số liveness - tăng trọng số cho blink_score
    liveness_score = (blink_score * 0.7 + ear_score * 0.1 + rate_score * 0.1 + face_score * 0.1)

    # Nếu phát hiện ít nhất 1 nháy mắt, luôn cho điểm cao
    if blink_counter >= 1:
        liveness_score = max(liveness_score, 0.9)

    # Nếu phát hiện khuôn mặt trong hầu hết các frame, cũng cho điểm cao
    if face_detection_ratio > 0.8:
        liveness_score = max(liveness_score, 0.85)

    # Ghi log thêm thông tin
    with open(os.path.join(debug_dir, "detection_details.txt"), "w", encoding="utf-8") as f:
        f.write(f"Video path: {video_path}\n")
        f.write(f"Total frames: {total_frames}\n")
        f.write(f"Face detected frames: {face_detected_frames}\n")
        f.write(f"Rotated frames: {rotated_frames_count}\n")
        f.write(f"Face detection ratio: {face_detection_ratio:.4f}\n")
        f.write(f"Blink count: {blink_counter}\n")
        f.write(f"Final liveness score: {liveness_score:.4f}\n")

    # Ghi log kết quả để debug
    with open(os.path.join(debug_dir, "liveness_results.txt"), "w", encoding="utf-8") as f:
        f.write(f"Total frames: {total_frames}\n")
        f.write(f"Face detected frames: {face_detected_frames}\n")
        f.write(f"Rotated frames: {rotated_frames_count}\n")
        f.write(f"Blink count: {blink_counter}\n")
        f.write(f"Average EAR: {avg_ear:.4f}\n")
        f.write(f"Blink rate: {blink_rate:.4f} blinks/second\n")
        f.write(f"Face detection ratio: {face_detection_ratio:.4f}\n")
        f.write(f"Blink score: {blink_score:.4f}\n")
        f.write(f"EAR score: {ear_score:.4f}\n")
        f.write(f"Rate score: {rate_score:.4f}\n")
        f.write(f"Face score: {face_score:.4f}\n")
        f.write(f"Liveness score: {liveness_score:.4f}\n")

    return {
        'liveness_score': liveness_score,
        'blink_count': blink_counter,
        'avg_ear': avg_ear,
        'blink_rate': blink_rate,
        'face_detected_frames': face_detected_frames,
        'face_detection_ratio': face_detection_ratio,
        'rotated_frames_count': rotated_frames_count
    }

def preprocess_frame(frame):
    """
    Tiền xử lý frame để cải thiện chất lượng

    Args:
        frame: Frame cần xử lý

    Returns:
        Frame đã được xử lý
    """
    # Kiểm tra độ sáng trung bình của frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)

    # Cải thiện độ tương phản và độ sáng
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    # Áp dụng bộ lọc làm mịn để giảm nhiễu
    enhanced_frame = cv2.GaussianBlur(enhanced_frame, (5, 5), 0)

    # Điều chỉnh độ sáng và độ tương phản dựa trên độ sáng trung bình
    alpha = 1.2  # Điều chỉnh độ tương phản

    # Điều chỉnh beta (độ sáng) dựa trên độ sáng trung bình của frame
    if avg_brightness < 80:  # Frame tối
        beta = 30  # Tăng độ sáng nhiều hơn cho frame tối
    elif avg_brightness > 200:  # Frame quá sáng
        beta = -10  # Giảm độ sáng cho frame quá sáng
        alpha = 0.9  # Giảm độ tương phản
    else:  # Frame có độ sáng bình thường
        beta = 10  # Tăng độ sáng vừa phải

    enhanced_frame = cv2.convertScaleAbs(enhanced_frame, alpha=alpha, beta=beta)

    return enhanced_frame

def process_video_for_liveness(video_file):
    """
    Xử lý video để phát hiện liveness (nháy mắt)

    Args:
        video_file: File video từ request hoặc đường dẫn đến file video

    Returns:
        Dictionary chứa kết quả phân tích liveness
    """
    # Tạo thư mục uploads nếu chưa có
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'liveness')
    os.makedirs(upload_dir, exist_ok=True)

    # Tạo thư mục debug để lưu các frame và log
    debug_dir = os.path.join(upload_dir, "debug_frames")
    os.makedirs(debug_dir, exist_ok=True)

    # Kiểm tra xem video_file là file từ request hay đường dẫn đến file
    if isinstance(video_file, str) and os.path.isfile(video_file):
        # Nếu là đường dẫn đến file, sử dụng trực tiếp
        video_path = video_file
        print(f"Sử dụng video trực tiếp từ đường dẫn: {video_path}")
    else:
        # Nếu là file từ request, lưu vào thư mục upload
        timestamp = int(time.time())
        video_path = os.path.join(upload_dir, f'liveness_{timestamp}.mp4')

        # Lưu video để có thể phân tích và debug sau này
        with open(video_path, 'wb') as f:
            f.write(video_file.read())

        print(f"Đã lưu video vào: {video_path}")

    try:
        # Ghi log thông tin video
        with open(os.path.join(debug_dir, "video_info.txt"), "w", encoding="utf-8") as f:
            f.write(f"Video path: {video_path}\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Kiểm tra kích thước file
            file_size = os.path.getsize(video_path)
            f.write(f"File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)\n")

            # Kiểm tra định dạng file
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0

                f.write(f"Resolution: {width}x{height}\n")
                f.write(f"FPS: {fps}\n")
                f.write(f"Frame count: {frame_count}\n")
                f.write(f"Duration: {duration:.2f} seconds\n")

                cap.release()

        # Phân tích video
        print(f"Bắt đầu phân tích video liveness: {video_path}")
        results = detect_blinks(video_path)
        print(f"Kết quả phân tích: {results}")

        # Không xóa video để có thể debug sau này
        # Chỉ xóa các video cũ hơn 7 ngày
        cleanup_old_videos(upload_dir, days=7)

        return results
    except Exception as e:
        print(f"Lỗi khi phân tích video liveness: {e}")
        # Ghi log lỗi
        with open(os.path.join(debug_dir, "error_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error processing video {video_path}: {str(e)}\n")
        # Vẫn giữ lại video để debug
        raise e

def cleanup_old_videos(directory, days=7):
    """Xóa các video cũ hơn số ngày chỉ định"""
    try:
        now = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # Kiểm tra xem file có phải là file thường và có cũ hơn số ngày chỉ định không
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < now - days * 86400:
                os.remove(file_path)
                print(f"Đã xóa file cũ: {file_path}")
    except Exception as e:
        print(f"Lỗi khi dọn dẹp các file cũ: {e}")
