"""
edge_area_improved.py
----------------------
An improved, organized version of the original edge_area.py / show_image.py
scripts. Detects shapes/objects in an image, classifies them, measures
their geometric properties, and reports what percentage of the image
area is covered by detected objects.

Run:
    python edge_area_improved.py

Requires:
    pip install opencv-python numpy
"""

import os
import csv
import math
import cv2
import numpy as np

# =====================================================================
# 1. CONFIGURATION  (change these instead of digging through the code)
# =====================================================================

IMAGE_FILENAME   = "test2.jpeg"   # just the filename; folder is handled for you
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]  # tried if exact name not found

BLUR_KSIZE       = (5, 5)     # Gaussian blur kernel size (must be odd numbers)

USE_AUTO_CANNY   = True       # auto-compute Canny thresholds from image statistics
CANNY_LOW        = 50         # used only if USE_AUTO_CANNY is False
CANNY_HIGH       = 150        # used only if USE_AUTO_CANNY is False

USE_OTSU_THRESH  = False      # use Otsu binary thresholding INSTEAD of Canny edges
USE_ADAPTIVE     = False      # use adaptive thresholding INSTEAD of Canny edges
                               # (only one of USE_OTSU_THRESH / USE_ADAPTIVE should be True;
                               #  if both are False, Canny edge detection is used)

MORPH_OPERATION  = "close"    # one of: "none", "close", "open", "dilate", "erode"
MORPH_KSIZE      = (3, 3)
MORPH_ITER       = 1

CONTOUR_MODE     = cv2.RETR_EXTERNAL   # see explanation below
MIN_CONTOUR_AREA = 50          # ignore contours smaller than this (noise)

SQUARE_ASPECT_TOLERANCE = 0.10   # |1 - w/h| below this => "Square", else "Rectangle"
CIRCLE_CIRCULARITY_MIN  = 0.80   # circularity above this (and enough vertices) => "Circle"

SAVE_OUTPUTS     = True        # save result images + CSV to an "output" folder
USE_TRACKBARS    = False       # set True to interactively tune Canny/area with sliders


# ---------------------------------------------------------------------
# Why RETR_EXTERNAL?
#
#   cv2.RETR_EXTERNAL -> only the outermost contour of each object.
#                         Best when you want to count/measure distinct
#                         objects sitting on a background, because it
#                         never double-reports a shape's inner edge as
#                         a second contour.
#   cv2.RETR_LIST      -> every contour, no parent/child relationship.
#                         Useful if you need ALL edges (including holes)
#                         but don't care how they're nested.
#   cv2.RETR_TREE      -> every contour PLUS full hierarchy info
#                         (which contour is inside which). Needed when
#                         you must distinguish a shape from a hole
#                         inside it (e.g. a donut vs a disk).
#
#   For this project (detecting and measuring whole objects/shapes on
#   a plain background) RETR_EXTERNAL is the most appropriate choice:
#   it avoids counting an object's outline and any internal texture
#   edges as separate "objects", which would inflate the object count
#   and corrupt the area percentage calculation.
# ---------------------------------------------------------------------


# =====================================================================
# 2. IMAGE LOADING
# =====================================================================

def load_image(filename):
    """
    Load an image reliably, regardless of the current working directory.
    Tries the exact filename first, then common extensions, always
    looking in the same folder as this script.

    Returns the loaded image (BGR numpy array).
    Exits with a clear error message if nothing could be found.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    candidates = [filename]
    name_no_ext, _ = os.path.splitext(filename)
    candidates += [name_no_ext + ext for ext in IMAGE_EXTENSIONS]

    tried_paths = []
    for candidate in candidates:
        full_path = os.path.join(script_dir, candidate)
        tried_paths.append(full_path)
        if os.path.isfile(full_path):
            img = cv2.imread(full_path)
            if img is not None:
                print(f"Loaded image: {full_path}")
                return img

    # Nothing worked -- give a genuinely useful error message
    print("ERROR: Could not load the image.")
    print(f"Looked for it in: {script_dir}")
    print("Tried these exact paths:")
    for p in tried_paths:
        print(f"   - {p}")
    print("\nFix: place your image file in the same folder as this script,")
    print(f"     and set IMAGE_FILENAME at the top of the script (currently '{filename}').")
    raise SystemExit(1)


# =====================================================================
# 3. PREPROCESSING  (grayscale -> blur -> binary/edge image)
# =====================================================================

def preprocess_image(img, blur_ksize=BLUR_KSIZE):
    """Convert to grayscale and blur to reduce noise before edge detection."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, blur_ksize, 0)
    return gray, blurred


def auto_canny_thresholds(image, sigma=0.33):
    """
    Compute good Canny thresholds automatically from the image's median
    intensity, instead of guessing fixed numbers. This makes the pipeline
    adapt to brighter/darker images automatically.
    """
    median_val = np.median(image)
    lower = int(max(0, (1.0 - sigma) * median_val))
    upper = int(min(255, (1.0 + sigma) * median_val))
    return lower, upper


def detect_edges(blurred, canny_low=CANNY_LOW, canny_high=CANNY_HIGH,
                  use_auto=USE_AUTO_CANNY, use_otsu=USE_OTSU_THRESH,
                  use_adaptive=USE_ADAPTIVE):
    """
    Produce a binary "edges" image that find_valid_contours() can use.
    Three strategies are supported (pick one via the CONFIG flags):
      1. Canny edge detection (default) - good for well-lit images with
         clear object boundaries.
      2. Otsu thresholding - good when objects are clearly darker/lighter
         than a fairly uniform background.
      3. Adaptive thresholding - good when lighting is uneven across
         the image.
    """
    if use_otsu:
        _, result = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif use_adaptive:
        result = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blockSize=11, C=2
        )
    else:
        if use_auto:
            canny_low, canny_high = auto_canny_thresholds(blurred)
        result = cv2.Canny(blurred, canny_low, canny_high)

    # Morphological cleanup: closes small gaps in edges / removes speckle noise
    result = apply_morphology(result)
    return result


def apply_morphology(binary_img, operation=MORPH_OPERATION,
                      ksize=MORPH_KSIZE, iterations=MORPH_ITER):
    """
    Optional morphological step to clean up the binary/edge image:
      - "close"  : fills small gaps in edges (dilate then erode) - most useful
                   after Canny, since edges can have tiny breaks.
      - "open"   : removes small noise specks (erode then dilate).
      - "dilate" : thickens edges/regions.
      - "erode"  : thins edges/regions.
      - "none"   : no-op.
    """
    if operation == "none":
        return binary_img
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize)
    if operation == "close":
        return cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    elif operation == "open":
        return cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel, iterations=iterations)
    elif operation == "dilate":
        return cv2.dilate(binary_img, kernel, iterations=iterations)
    elif operation == "erode":
        return cv2.erode(binary_img, kernel, iterations=iterations)
    return binary_img


# =====================================================================
# 4. CONTOUR DETECTION AND SHAPE CLASSIFICATION
# =====================================================================

def find_valid_contours(binary_img, min_area=MIN_CONTOUR_AREA, mode=CONTOUR_MODE):
    """Find contours and immediately discard tiny/noisy ones."""
    contours, _ = cv2.findContours(binary_img, mode, cv2.CHAIN_APPROX_SIMPLE)
    valid = [c for c in contours if cv2.contourArea(c) >= min_area]
    return contours, valid


def classify_shape(vertices, aspect_ratio, extent, circularity):
    """
    Classify a contour's shape using MULTIPLE features instead of vertex
    count alone:
      - vertices     : from polygon approximation
      - aspect_ratio  : width / height of the bounding box
      - extent        : contour area / bounding box area (how "filled in"
                        the bounding box is - low extent hints at a thin
                        or irregular shape)
      - circularity   : 4*pi*Area / Perimeter^2 (1.0 = perfect circle)
    """
    # High circularity + enough vertices from the polygon approximation
    # is a much more reliable circle test than "vertices > 8" alone,
    # because it also rejects blobby/irregular shapes that happen to
    # approximate to many vertices.
    if circularity >= CIRCLE_CIRCULARITY_MIN and vertices >= 6:
        return "Circle"

    if vertices == 3:
        return "Triangle"

    if vertices == 4:
        if abs(1.0 - aspect_ratio) <= SQUARE_ASPECT_TOLERANCE:
            return "Square"
        return "Rectangle"

    if vertices > 4:
        # Reasonably regular but not round enough to be a circle
        if extent >= 0.6:
            return "Polygon"
        return "Unknown/Irregular"

    return "Unknown/Irregular"


def analyze_contour(cnt):
    """Compute every measurement needed for one contour and classify it."""
    area = cv2.contourArea(cnt)
    perimeter = cv2.arcLength(cnt, True)
    x, y, w, h = cv2.boundingRect(cnt)

    aspect_ratio = w / float(h) if h != 0 else 0
    bbox_area = w * h
    extent = area / bbox_area if bbox_area != 0 else 0
    circularity = (4 * math.pi * area / (perimeter ** 2)) if perimeter != 0 else 0

    approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
    vertices = len(approx)

    shape_name = classify_shape(vertices, aspect_ratio, extent, circularity)

    return {
        "contour": cnt,
        "area": area,
        "perimeter": perimeter,
        "x": x, "y": y, "w": w, "h": h,
        "aspect_ratio": aspect_ratio,
        "extent": extent,
        "circularity": circularity,
        "vertices": vertices,
        "shape": shape_name,
    }


# =====================================================================
# 5. AREA COVERAGE CALCULATION
# =====================================================================

def calculate_detected_area(objects, img_shape):
    """
    Two ways to report how much of the image is "covered" by detections:

      1. sum_of_contour_areas: just add up each contour's cv2.contourArea().
         SIMPLE but WRONG if contours overlap - overlapping pixels get
         counted twice (or more), inflating the coverage percentage.

      2. unique_mask_area: draw every accepted contour FILLED onto a
         blank mask (same size as the image), then count non-zero pixels.
         Overlapping shapes just paint the same pixel more than once on
         the mask, but cv2.countNonZero() still only counts it ONCE.
         This gives the true, non-double-counted covered area.

    We report both, but treat unique_mask_area as the correct figure,
    since overlapping contours are a realistic possibility.
    """
    height, width = img_shape[:2]
    image_area = width * height

    sum_of_contour_areas = sum(obj["area"] for obj in objects)

    mask = np.zeros((height, width), dtype=np.uint8)
    for obj in objects:
        cv2.drawContours(mask, [obj["contour"]], -1, 255, thickness=cv2.FILLED)
    unique_mask_area = cv2.countNonZero(mask)

    percentage_detected = (unique_mask_area / image_area) * 100 if image_area else 0

    return {
        "image_width": width,
        "image_height": height,
        "image_area": image_area,
        "sum_of_contour_areas": sum_of_contour_areas,
        "unique_mask_area": unique_mask_area,
        "percentage_detected": percentage_detected,
    }


# =====================================================================
# 6. REPORTING (console table + CSV)
# =====================================================================

def print_results_table(objects):
    header = (f"{'#':<4}{'Shape':<18}{'Area':<10}{'Perim':<9}{'W':<6}{'H':<6}"
              f"{'AspRatio':<10}{'Extent':<9}{'Circ':<7}{'Verts':<6}")
    print("\n" + header)
    print("-" * len(header))
    for i, obj in enumerate(objects):
        print(f"{i:<4}{obj['shape']:<18}{obj['area']:<10.1f}{obj['perimeter']:<9.1f}"
              f"{obj['w']:<6}{obj['h']:<6}{obj['aspect_ratio']:<10.2f}"
              f"{obj['extent']:<9.2f}{obj['circularity']:<7.2f}{obj['vertices']:<6}")


def print_summary(objects, all_contours, area_stats):
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Image width               : {area_stats['image_width']} px")
    print(f"Image height              : {area_stats['image_height']} px")
    print(f"Total image area          : {area_stats['image_area']} px^2")
    print(f"Contours found (raw)      : {len(all_contours)}")
    print(f"Valid objects detected    : {len(objects)}")
    print(f"Sum of contour areas      : {area_stats['sum_of_contour_areas']:.1f} px^2  "
          f"(can double-count overlaps)")
    print(f"Unique detected area(mask): {area_stats['unique_mask_area']} px^2  "
          f"(overlap-safe)")
    print(f"Percentage of image area  : {area_stats['percentage_detected']:.2f}%")
    print("=" * 50)


def save_results_csv(objects, out_path):
    fieldnames = ["index", "shape", "area", "perimeter", "x", "y", "w", "h",
                  "aspect_ratio", "extent", "circularity", "vertices"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, obj in enumerate(objects):
            row = {"index": i, **{k: obj[k] for k in fieldnames if k != "index"}}
            writer.writerow(row)
    print(f"Saved object data to: {out_path}")


# =====================================================================
# 7. DRAWING / DISPLAY
# =====================================================================

def draw_annotations(img, objects, area_stats):
    """Draw contour outline, bounding box, and a label for each object,
    plus the overall detected-area percentage in a banner at the top."""
    output = img.copy()
    for i, obj in enumerate(objects):
        cv2.drawContours(output, [obj["contour"]], -1, (0, 0, 255), 2)
        cv2.rectangle(output, (obj["x"], obj["y"]),
                       (obj["x"] + obj["w"], obj["y"] + obj["h"]), (255, 0, 0), 1)
        label = f"#{i} {obj['shape']} A={obj['area']:.0f}"
        cv2.putText(output, label, (obj["x"], max(obj["y"] - 6, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

    banner = (f"Objects: {len(objects)}  |  "
              f"Detected area: {area_stats['percentage_detected']:.2f}%")
    cv2.putText(output, banner, (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (0, 128, 0), 2, cv2.LINE_AA)
    return output


def display_results(img, gray, processed, output, objects, area_stats):
    print_results_table(objects)
    print_summary(objects, objects, area_stats)  # objects list already filtered

    cv2.imshow("1 - Original", img)
    cv2.imshow("2 - Grayscale", gray)
    cv2.imshow("3 - Processed / Edges", processed)
    cv2.imshow("4 - Detected Objects", output)

    if SAVE_OUTPUTS:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(script_dir, "output")
        os.makedirs(out_dir, exist_ok=True)
        cv2.imwrite(os.path.join(out_dir, "edges.png"), processed)
        cv2.imwrite(os.path.join(out_dir, "detected_objects.png"), output)
        save_results_csv(objects, os.path.join(out_dir, "detected_objects.csv"))

    print("\nPress any key (with an image window focused) to close.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# =====================================================================
# 8. OPTIONAL: INTERACTIVE TRACKBAR TUNING
# =====================================================================

def interactive_tuning(blurred):
    """
    Opens a window with sliders for Canny thresholds and minimum contour
    area, so you can tune them visually. Press 'q' or ESC when you're
    happy with the result to lock in those values and continue.
    Only runs if USE_TRACKBARS = True.
    """
    window = "Tune Parameters (q to confirm)"
    cv2.namedWindow(window)
    cv2.createTrackbar("Canny Low", window, CANNY_LOW, 255, lambda x: None)
    cv2.createTrackbar("Canny High", window, CANNY_HIGH, 255, lambda x: None)
    cv2.createTrackbar("Min Area", window, MIN_CONTOUR_AREA, 5000, lambda x: None)

    while True:
        low = cv2.getTrackbarPos("Canny Low", window)
        high = cv2.getTrackbarPos("Canny High", window)
        min_area = cv2.getTrackbarPos("Min Area", window)

        edges = cv2.Canny(blurred, low, high)
        edges = apply_morphology(edges)
        cv2.imshow(window, edges)

        key = cv2.waitKey(50) & 0xFF
        if key == ord("q") or key == 27:  # 'q' or ESC
            break

    cv2.destroyWindow(window)
    return low, high, min_area


# =====================================================================
# 9. MAIN
# =====================================================================

def main():
    img = load_image(IMAGE_FILENAME)
    gray, blurred = preprocess_image(img)

    canny_low, canny_high, min_area = CANNY_LOW, CANNY_HIGH, MIN_CONTOUR_AREA
    if USE_TRACKBARS:
        canny_low, canny_high, min_area = interactive_tuning(blurred)

    processed = detect_edges(blurred, canny_low, canny_high,
                              use_auto=USE_AUTO_CANNY and not USE_TRACKBARS)

    all_contours, valid_contours = find_valid_contours(processed, min_area=min_area)
    objects = [analyze_contour(c) for c in valid_contours]

    area_stats = calculate_detected_area(objects, img.shape)
    output = draw_annotations(img, objects, area_stats)

    display_results(img, gray, processed, output, objects, area_stats)


if __name__ == "__main__":
    main()
