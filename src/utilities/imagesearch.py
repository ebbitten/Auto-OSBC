from pathlib import Path
from typing import Union

import cv2
import numpy as np

from utilities.geometry import Point, Rectangle

# --- Confidence Thresholds for Template Matching ---
# Uses TM_SQDIFF_NORMED: lower values = stricter matching (0 = perfect match)
#
# CONFIDENCE_STRICT (0.15): Very strict matching. Use for:
#   - Unique UI elements with distinctive patterns
#   - High-stakes detection where false positives are costly
#   - Elements that rarely change appearance
#
# CONFIDENCE_MODERATE (0.3): Balanced matching. Use for:
#   - General UI buttons and icons
#   - Elements with minor variations (themes, lighting)
#   - Most production detection scenarios
#
# CONFIDENCE_LOOSE (0.8): Permissive matching. Use for:
#   - Login/welcome screens with varying backgrounds
#   - Elements that may be partially obscured
#   - Initial detection passes (with follow-up validation)
#   - WARNING: Higher risk of false positives, use with structural validation
#
CONFIDENCE_STRICT = 0.15
CONFIDENCE_MODERATE = 0.3
CONFIDENCE_LOOSE = 0.8

# --- Paths to Image folders ---
__PATH = Path(__file__).parent.parent
IMAGES = __PATH.joinpath("images")
BOT_IMAGES = IMAGES.joinpath("bot")

# --- Template Cache ---
# Cache loaded template images to avoid repeated disk I/O
_template_cache: dict[str, np.ndarray] = {}


def _load_template(path: Union[str, Path]) -> np.ndarray:
    """Load a template image with caching.

    Args:
        path: Path to the template image file.

    Returns:
        The loaded image as a numpy array with alpha channel (BGRA).
    """
    key = str(path)
    if key not in _template_cache:
        img = cv2.imread(key, cv2.IMREAD_UNCHANGED)
        if img is not None:
            _template_cache[key] = img
        else:
            raise FileNotFoundError(f"Template not found: {key}")
    return _template_cache[key]


def clear_template_cache() -> None:
    """Clear the template cache. Useful for testing or memory management."""
    _template_cache.clear()


def __imagesearcharea(template: Union[cv2.Mat, str, Path], im: cv2.Mat, confidence: float) -> Rectangle:
    """
    Locates an image within another image.
    Args:
        template: The image to search for.
        im: The image to search in.
        confidence: The confidence level of the search in range 0 to 1, where 0 is a perfect match.
    Returns:
        A Rectangle outlining the found template inside the image.
    """
    # If image doesn't have an alpha channel, convert it from BGR to BGRA
    if len(template.shape) < 3 or template.shape[2] != 4:
        template = cv2.cvtColor(template, cv2.COLOR_BGR2BGRA)
    # Get template dimensions
    hh, ww = template.shape[:2]
    # Extract base image and alpha channel
    base = template[:, :, 0:3]
    alpha = template[:, :, 3]
    alpha = cv2.merge([alpha, alpha, alpha])

    correlation = cv2.matchTemplate(im, base, cv2.TM_SQDIFF_NORMED, mask=alpha)
    min_val, _, min_loc, _ = cv2.minMaxLoc(correlation)
    if min_val < confidence:
        return Rectangle.from_points(Point(min_loc[0], min_loc[1]), Point(min_loc[0] + ww, min_loc[1] + hh))
    return None


def search_img_in_rect(image: Union[cv2.Mat, str, Path], rect: Union[Rectangle, cv2.Mat], confidence=0.15) -> Rectangle:
    """
    Searches for an image in a rectangle. This function works with images containing transparency (sprites).
    Args:
        image: The image to search for (can be a path or matrix).
        rect: The Rectangle to search in (can be a Rectangle or a matrix).
        confidence: The confidence level of the search in range 0 to 1, where 0 is a perfect match.
    Returns:
        A Rectangle outlining the found image relative to the container, or None.
    Notes:
        If a matrix is supplied for the `rect` argument instead of a Rectangle, and the image is found within this matrix,
        the returned Rectangle will be relative to the top-left corner of the matrix. In other words, the returned
        Rectangle is not suitable for use with mouse movement/clicks, as it will not be relative to the game window.
        However, you will still be able to confirm if the image was found or not. This is useful in cases where you take a static
        screenshot and want to search for a series of images to verify that they are present.
    Examples:
        >>> deposit_all_btn = search_img_in_rect(BOT_IMAGES.joinpath("bank", "deposit.png"), self.win.game_view)
        >>> if deposit_all_btn:
        >>>     # Deposit all button was found
    """
    if isinstance(image, (str, Path)):
        image = _load_template(image)
    im = rect.screenshot() if isinstance(rect, Rectangle) else rect

    if found_rect := __imagesearcharea(image, im, confidence):
        if isinstance(rect, Rectangle):
            found_rect.left += rect.left
            found_rect.top += rect.top
        return found_rect
    else:
        return None
