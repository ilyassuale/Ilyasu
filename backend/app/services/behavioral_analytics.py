"""Behavioral analytics using OpenCV and MediaPipe (placeholder API)."""
from __future__ import annotations

import base64
import os
from typing import Any

import cv2
import numpy as np


def analyze_video_frame(frame_b64: str) -> dict[str, Any]:
    """Analyze a single base64-encoded frame.

    Returns heuristic metrics when MediaPipe is not installed.
    """
    try:
        header, data = frame_b64.split(",", 1)
    except ValueError:
        data = frame_b64
    try:
        img_bytes = base64.b64decode(data, validate=True)
    except Exception:
        return {"error": "Invalid base64 frame"}
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"error": "Could not decode frame"}

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _detect_faces(gray)
    if not faces:
        return {
            "eye_contact_score": None,
            "head_pose_score": None,
            "expression_score": None,
            "confidence": None,
            "engagement": None,
            "face_detected": False,
        }

    # Placeholder heuristics based on face position and size
    x, y, w, h = faces[0]
    center_x = x + w / 2
    center_y = y + h / 2
    frame_cx = frame.shape[1] / 2
    frame_cy = frame.shape[0] / 2

    eye_contact_score = int(100 - min(100, abs(center_x - frame_cx) / (frame.shape[1] / 2) * 100))
    head_pose_score = int(100 - min(100, abs(center_y - frame_cy) / (frame.shape[0] / 2) * 100))
    expression_score = 75
    confidence = int((eye_contact_score + head_pose_score + expression_score) / 3)
    engagement = int(confidence * 0.9)

    return {
        "eye_contact_score": eye_contact_score,
        "head_pose_score": head_pose_score,
        "expression_score": expression_score,
        "confidence": confidence,
        "engagement": engagement,
        "face_detected": True,
    }


def _detect_faces(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    cv2_data = getattr(cv2, "data", None)
    if cv2_data is None:
        return []
    cascade_dir = cv2_data.haarcascades
    cascade_path = cascade_dir + "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        return []
    classifier = cv2.CascadeClassifier(cascade_path)
    faces = classifier.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    return [(int(row[0]), int(row[1]), int(row[2]), int(row[3])) for row in faces]


def analyze_video_clip(frames_b64: list[str]) -> dict[str, Any]:
    results = [analyze_video_frame(f) for f in frames_b64 if f]
    valid = [r for r in results if r.get("face_detected")]
    if not valid:
        return {"error": "No faces detected in clip."}

    averages = {}
    for key in ["eye_contact_score", "head_pose_score", "expression_score", "confidence", "engagement"]:
        values = [r[key] for r in valid if key in r and r[key] is not None]
        if values:
            averages[key] = int(sum(values) / len(values))
    averages["frames_analyzed"] = len(results)
    averages["faces_detected"] = len(valid)
    return averages
