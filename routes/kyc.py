from flask import Blueprint, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
from models import db, KYCVerification, User
from utils.auth import token_required
from utils.liveness import detect_blinks
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

kyc_bp = Blueprint('kyc', __name__)

@kyc_bp.route('/verify-liveness', methods=['POST'])
@token_required
def verify_liveness(current_user):
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
        
    video_file = request.files['video']
    temp_path = f"temp_{current_user.id}.mp4"
    video_file.save(temp_path)
    
    # Process video for blink detection
    blink_count, liveness_score = detect_blinks(temp_path)
    
    # Save verification attempt
    verification = KYCVerification(
        user_id=current_user.id,
        liveness_score=liveness_score
    )
    
    if liveness_score > 0.8:  # Threshold for passing
        verification.status = 'verified'
        current_user.kyc_status = 'verified'
        db.session.add(verification)
        db.session.commit()
        return jsonify({
            'message': 'Liveness verification successful',
            'blink_count': blink_count,
            'liveness_score': liveness_score
        })
    
    return jsonify({
        'error': 'Liveness verification failed',
        'blink_count': blink_count,
        'liveness_score': liveness_score
    }), 400
