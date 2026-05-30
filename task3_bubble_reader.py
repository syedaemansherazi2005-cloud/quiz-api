"""
Task 3 — Bubble Sheet Reading
Auto-detects bubble grid for any image size.
"""

import cv2
import numpy as np
from dataclasses import dataclass, field

OPTIONS = ["A", "B", "C", "D"]


@dataclass
class StudentAnswers:
    part1: dict = field(default_factory=dict)
    part2: dict = field(default_factory=dict)

    def to_dict(self):
        return {"part1": self.part1, "part2": self.part2}


def _get_darkness(gray, cx, cy, r=12):
    """Get average pixel darkness in circle."""
    mask = np.zeros_like(gray)
    cv2.circle(mask, (cx, cy), r, 255, -1)
    region = cv2.bitwise_and(gray, gray, mask=mask)
    pixels = region[mask > 0]
    if len(pixels) == 0:
        return 255
    return float(np.mean(pixels))


def _detect_bubbles(gray):
    """Detect all bubble circles in image."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try HoughCircles with different parameters
    circles = None
    for param2 in [30, 25, 20, 15]:
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=15,
            param1=50,
            param2=param2,
            minRadius=8,
            maxRadius=25
        )
        if circles is not None and len(circles[0]) >= 16:
            break

    if circles is None:
        return []

    return [(int(x), int(y), int(r)) for x, y, r in circles[0]]


def _group_into_grid(circles, n_questions=8, n_options=4):
    """Group circles into rows and columns."""
    if not circles:
        return []

    # Sort by y position
    circles_sorted = sorted(circles, key=lambda c: c[1])

    # Group into rows
    rows = []
    current_row = [circles_sorted[0]]

    for circle in circles_sorted[1:]:
        if abs(circle[1] - np.mean([c[1] for c in current_row])) < 20:
            current_row.append(circle)
        else:
            if len(current_row) >= 2:
                rows.append(sorted(current_row, key=lambda c: c[0]))
            current_row = [circle]

    if len(current_row) >= 2:
        rows.append(sorted(current_row, key=lambda c: c[0]))

    # Filter rows with at least 3 circles
    rows = [r for r in rows if len(r) >= 3]

    return rows[:n_questions]


def _read_answers_from_grid(gray, rows):
    """Read filled bubble from each row."""
    answers = {}

    for idx, row in enumerate(rows):
        q_key = f"Q{idx+1:02d}"
        bubbles = row[:4]

        if len(bubbles) < 2:
            answers[q_key] = None
            continue

        # Get darkness for each bubble
        darkness_values = []
        for cx, cy, r in bubbles:
            d = _get_darkness(gray, cx, cy, r)
            darkness_values.append(d)

        min_d = min(darkness_values)
        max_d = max(darkness_values)
        dark_range = max_d - min_d

        if dark_range < 8:
            answers[q_key] = None
            continue

        threshold = min_d + dark_range * 0.35
        filled = [i for i, d in enumerate(darkness_values)
                  if d < threshold]

        if len(filled) == 0:
            answers[q_key] = None
        elif len(filled) == 1:
            if filled[0] < len(OPTIONS):
                answers[q_key] = OPTIONS[filled[0]]
            else:
                answers[q_key] = None
        else:
            # Multiple filled - pick darkest
            best = int(np.argmin(darkness_values))
            answers[q_key] = OPTIONS[best] if best < len(OPTIONS) else None

    # Fill missing
    for i in range(len(rows) + 1, 9):
        answers[f"Q{i:02d}"] = None

    return answers


def _resize_to_standard(image):
    """Resize image to standard size for consistent processing."""
    target_h, target_w = 1100, 900
    h, w = image.shape[:2]

    # Only resize if significantly different
    if abs(h - target_h) > 100 or abs(w - target_w) > 100:
        image = cv2.resize(image, (target_w, target_h),
                          interpolation=cv2.INTER_CUBIC)
    return image


def read_bubble_sheet(image: np.ndarray) -> StudentAnswers:
    # Resize to standard size
    image = _resize_to_standard(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) \
        if len(image.shape) == 3 else image

    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    h, w = gray.shape
    top = int(h * 0.20)  # Skip top 20% (header area)

    # Split into left and right halves
    part1_region = gray[top:h-50, :w//2]
    part2_region = gray[top:h-50, w//2:]

    # Try auto-detect first
    circles1 = _detect_bubbles(part1_region)
    circles2 = _detect_bubbles(part2_region)

    rows1 = _group_into_grid(circles1)
    rows2 = _group_into_grid(circles2)

    # If auto-detect fails use fixed grid
    if len(rows1) < 4:
        part1 = _read_fixed_grid(gray, x_start=101, y_start=266)
    else:
        part1 = _read_answers_from_grid(part1_region, rows1)

    if len(rows2) < 4:
        part2 = _read_fixed_grid(gray, x_start=541, y_start=266)
    else:
        part2 = _read_answers_from_grid(part2_region, rows2)

    return StudentAnswers(part1=part1, part2=part2)


def _read_fixed_grid(gray, x_start, y_start,
                     col_w=50, row_h=52, n_questions=8):
    """Fallback fixed grid reading."""
    answers = {}
    for q in range(n_questions):
        cy = y_start + q * row_h
        darkness_values = []
        for opt in range(4):
            cx = x_start + opt * col_w
            d = _get_darkness(gray, cx, cy)
            darkness_values.append(d)

        min_d = min(darkness_values)
        max_d = max(darkness_values)
        dark_range = max_d - min_d

        q_key = f"Q{q+1:02d}"
        if dark_range < 8:
            answers[q_key] = None
        else:
            threshold = min_d + dark_range * 0.35
            filled = [i for i, d in enumerate(darkness_values)
                      if d < threshold]
            if len(filled) == 0:
                answers[q_key] = None
            elif len(filled) == 1:
                answers[q_key] = OPTIONS[filled[0]]
            else:
                answers[q_key] = OPTIONS[int(np.argmin(darkness_values))]

    return answers


if __name__ == "__main__":
    import sys
    img = cv2.imread(sys.argv[1]) if len(sys.argv) > 1 else None
    if img is None:
        print("Usage: python task3_bubble_reader.py <image_path>")
        sys.exit(1)
    answers = read_bubble_sheet(img)
    print(answers.to_dict())