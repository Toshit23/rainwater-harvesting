"""
building_detection.py - OpenCV Building & Rooftop Coverage Detection.

Analyzes an aerial/drone image of a construction site:
  1. Preprocesses the image (grayscale, Gaussian blur)
  2. Detects edges via adaptive Canny edge detection
  3. Uses morphological closing to form solid building boundaries
  4. Finds external contours and filters out noise
  5. Computes overlap-safe mask area to get the exact building/rooftop percentage
  6. Generates and saves an annotated visual output

Returns the detected rooftop coverage percentage to be consumed by the
calculation module.
"""

import os
import cv2
import numpy as np
from typing import Union, Dict, Tuple


def auto_canny_thresholds(image: np.ndarray, sigma: float = 0.33) -> Tuple[int, int]:
    """Compute adaptive Canny thresholds from image median intensity."""
    median_val = np.median(image)
    lower = int(max(0, (1.0 - sigma) * median_val))
    upper = int(min(255, (1.0 + sigma) * median_val))
    return lower, upper


def detect_building_area_percentage(
    image_path: str,
    min_contour_area: int = 100,
    save_annotated: bool = True,
    output_dir: str = "output",
) -> Dict[str, Union[float, int, str]]:
    """Detect building/rooftop coverage percentage from an aerial image.

    Parameters
    ----------
    image_path : str
        Path to the aerial or drone image file.
    min_contour_area : int, optional
        Minimum contour area in pixels to count as a building (filters noise).
        Default is 100.
    save_annotated : bool, optional
        Whether to save an annotated visual detection image (default True).
    output_dir : str, optional
        Directory where annotated images will be saved.

    Returns
    -------
    dict
        {
            "rooftop_percentage": float,      # Coverage % of the image (0.0 to 100.0)
            "building_count": int,            # Number of building/rooftop segments detected
            "unique_building_pixels": int,    # Total pixels occupied by buildings
            "total_image_pixels": int,        # Total pixels in the image
            "image_dimensions": tuple,        # (height, width)
            "annotated_image_path": str,      # Path to saved annotated image (if saved)
            "status": "SUCCESS"
        }

    Raises
    ------
    FileNotFoundError
        If image_path does not exist.
    ValueError
        If the file cannot be decoded as an image by OpenCV.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not decode image at path: {image_path}. Ensure it is a valid image file.")

    height, width = img.shape[:2]
    total_image_pixels = width * height

    # 1. Grayscale & Blur
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2. Canny Edge Detection with Auto Thresholds
    lower, upper = auto_canny_thresholds(blurred)
    edges = cv2.Canny(blurred, lower, upper)

    # 3. Morphological Closing (joins broken edges into solid shape outlines)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    dilated = cv2.dilate(closed, kernel, iterations=1)

    # 4. Contour Detection (RETR_EXTERNAL to capture entire outer building footprints)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [c for c in contours if cv2.contourArea(c) >= min_contour_area]

    # 5. Unique Overlap-Safe Area Mask
    mask = np.zeros((height, width), dtype=np.uint8)
    for c in valid_contours:
        cv2.drawContours(mask, [c], -1, 255, thickness=cv2.FILLED)

    unique_building_pixels = int(cv2.countNonZero(mask))
    rooftop_percentage = (unique_building_pixels / total_image_pixels) * 100.0 if total_image_pixels > 0 else 0.0
    rooftop_percentage = round(rooftop_percentage, 2)

    annotated_path = ""
    if save_annotated:
        os.makedirs(output_dir, exist_ok=True)
        annotated = img.copy()

        # Draw green building footprints and blue bounding boxes
        for i, c in enumerate(valid_contours):
            cv2.drawContours(annotated, [c], -1, (0, 255, 0), 2)
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 1)

        # Header banner
        banner = f"Buildings: {len(valid_contours)} | Rooftop Coverage: {rooftop_percentage:.2f}%"
        cv2.putText(annotated, banner, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        annotated_path = os.path.join(output_dir, f"{base_name}_rooftop_detected.png")
        cv2.imwrite(annotated_path, annotated)

    return {
        "rooftop_percentage": rooftop_percentage,
        "building_count": len(valid_contours),
        "unique_building_pixels": unique_building_pixels,
        "total_image_pixels": total_image_pixels,
        "image_dimensions": (height, width),
        "annotated_image_path": annotated_path,
        "status": "SUCCESS",
    }
