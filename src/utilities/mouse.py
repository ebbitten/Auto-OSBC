import time
from typing import TYPE_CHECKING, Optional

import mss
import numpy as np
import pyautogui as pag
import pytweening
from pyclick import HumanCurve

import utilities.debug as debug
import utilities.imagesearch as imsearch
from utilities.geometry import Point, Rectangle
from utilities.random_util import truncated_normal_sample

if TYPE_CHECKING:
    from utilities.window import Window


class WindowFocusError(Exception):
    """Raised when window focus cannot be established for mouse operation."""
    pass


class Mouse:
    click_delay = True
    _window: Optional["Window"] = None
    _focus_before_action: bool = True

    @classmethod
    def set_window(cls, window: "Window") -> None:
        """
        Set the window reference for focus verification.
        Args:
            window: The Window object to use for focus checks.
        """
        cls._window = window

    @classmethod
    def set_focus_before_action(cls, enabled: bool) -> None:
        """
        Enable/disable automatic focus verification before actions.
        Args:
            enabled: Whether to check focus before mouse operations.
        """
        cls._focus_before_action = enabled

    def _ensure_focus(self) -> bool:
        """
        Ensure window is focused before performing mouse action.
        Returns:
            True if focus is ensured or checking is disabled, False if focus failed.
        """
        if not self._focus_before_action or self._window is None:
            return True
        return self._window.ensure_focus()

    def move_to(self, destination: tuple, **kwargs):
        """
        Use Bezier curve to simulate human-like mouse movements.
        Args:
            destination: x, y tuple of the destination point
            destination_variance: pixel variance to add to the destination point (default 0)
        Kwargs:
            knotsCount: number of knots to use in the curve, higher value = more erratic movements
                        (default determined by distance)
            mouseSpeed: speed of the mouse (options: 'slowest', 'slow', 'medium', 'fast', 'fastest')
                        (default 'fast')
            tween: tweening function to use (default easeOutQuad)
        Raises:
            WindowFocusError: if window focus cannot be established.
        """
        # Ensure window focus before moving
        if not self._ensure_focus():
            raise WindowFocusError("Cannot move mouse: window focus lost")

        offsetBoundaryX = kwargs.get("offsetBoundaryX", 100)
        offsetBoundaryY = kwargs.get("offsetBoundaryY", 100)
        knotsCount = kwargs.get("knotsCount", self.__calculate_knots(destination))
        distortionMean = kwargs.get("distortionMean", 1)
        distortionStdev = kwargs.get("distortionStdev", 1)
        distortionFrequency = kwargs.get("distortionFrequency", 0.5)
        tween = kwargs.get("tweening", pytweening.easeOutQuad)
        mouseSpeed = kwargs.get("mouseSpeed", "fast")
        mouseSpeed = self.__get_mouse_speed(mouseSpeed)

        dest_x = destination[0]
        dest_y = destination[1]

        start_x, start_y = pag.position()
        for curve_x, curve_y in HumanCurve(
            (start_x, start_y),
            (dest_x, dest_y),
            offsetBoundaryX=offsetBoundaryX,
            offsetBoundaryY=offsetBoundaryY,
            knotsCount=knotsCount,
            distortionMean=distortionMean,
            distortionStdev=distortionStdev,
            distortionFrequency=distortionFrequency,
            tween=tween,
            targetPoints=mouseSpeed,
        ).points:
            pag.moveTo((curve_x, curve_y))
            start_x, start_y = curve_x, curve_y

    def move_rel(self, x: int, y: int, x_var: int = 0, y_var: int = 0, **kwargs):
        """
        Use Bezier curve to simulate human-like relative mouse movements.
        Args:
            x: x distance to move
            y: y distance to move
            x_var: maxiumum pixel variance that may be added to the x distance (default 0)
            y_var: maxiumum pixel variance that may be added to the y distance (default 0)
        Kwargs:
            knotsCount: if right-click menus are being cancelled due to erratic mouse movements,
                        try setting this value to 0.
        """
        if x_var != 0:
            x += round(truncated_normal_sample(-x_var, x_var))
        if y_var != 0:
            y += round(truncated_normal_sample(-y_var, y_var))
        self.move_to((pag.position()[0] + x, pag.position()[1] + y), **kwargs)

    def click(self, button="left", force_delay=False, check_red_click=False) -> tuple:
        """
        Clicks on the current mouse position.
        Args:
            button: button to click (default left).
            force_delay: whether to force a delay between mouse button presses regardless of the Mouse property.
            check_red_click: whether to check if the click was red (i.e., successful action) (default False).
        Returns:
            None, unless check_red_click is True, in which case it returns a boolean indicating
            whether the click was red (i.e., successful action) or not.
        Raises:
            WindowFocusError: if window focus cannot be established.
        """
        # Ensure window focus before clicking
        if not self._ensure_focus():
            raise WindowFocusError("Cannot click: window focus lost")

        mouse_pos_before = pag.position()
        pag.mouseDown(button=button)
        mouse_pos_after = pag.position()
        if force_delay or self.click_delay:
            LOWER_BOUND_CLICK = 0.03  # Milliseconds
            UPPER_BOUND_CLICK = 0.2  # Milliseconds
            AVERAGE_CLICK = 0.06  # Milliseconds
            time.sleep(truncated_normal_sample(LOWER_BOUND_CLICK, UPPER_BOUND_CLICK, AVERAGE_CLICK))
        pag.mouseUp(button=button)
        if check_red_click:
            return self.__is_red_click(mouse_pos_before, mouse_pos_after)

    def right_click(self, force_delay=False):
        """
        Right-clicks on the current mouse position. This is a wrapper for click(button="right").
        Args:
            with_delay: whether to add a random delay between mouse down and mouse up (default True).
        """
        self.click(button="right", force_delay=force_delay)

    def __rect_around_point(self, mouse_pos: Point, pad: int) -> Rectangle:
        """
        Returns a rectangle around a Point with some padding.
        """
        # Get monitor dimensions
        max_x, max_y = pag.size()
        max_x, max_y = int(str(max_x)), int(str(max_y))

        # Get the rectangle around the mouse cursor with some padding, ensure it is within the screen.
        mouse_x, mouse_y = mouse_pos
        p1 = Point(max(mouse_x - pad, 0), max(mouse_y - pad, 0))
        p2 = Point(min(mouse_x + pad, max_x), min(mouse_y + pad, max_y))
        return Rectangle.from_points(p1, p2)

    def __is_red_click(self, mouse_pos_from: Point, mouse_pos_to: Point) -> bool:
        """
        Checks if a click was red, indicating a successful action.
        Args:
            mouse_pos_from: mouse position before the click.
            mouse_pos_to: mouse position after the click.
        Returns:
            True if the click was red, False if the click was yellow.
        """
        CLICK_SPRITE_WIDTH_HALF = 7
        rect1 = self.__rect_around_point(mouse_pos_from, CLICK_SPRITE_WIDTH_HALF)
        rect2 = self.__rect_around_point(mouse_pos_to, CLICK_SPRITE_WIDTH_HALF)

        # Combine two rects into a bigger rectangle
        top_left_pos = Point(min(rect1.get_top_left().x, rect2.get_top_left().x), min(rect1.get_top_left().y, rect2.get_top_left().y))
        bottom_right_pos = Point(max(rect1.get_bottom_right().x, rect2.get_bottom_right().x), max(rect1.get_bottom_right().y, rect2.get_bottom_right().y))
        cursor_sct = Rectangle.from_points(top_left_pos, bottom_right_pos).screenshot()

        for click_sprite in ["red_1.png", "red_3.png", "red_2.png", "red_4.png"]:
            try:
                if imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("mouse_clicks", click_sprite), cursor_sct):
                    return True
            except mss.ScreenShotError:
                print("Failed to take screenshot of mouse cursor. Please report this error to the developer.")
                continue
        return False

    def __calculate_knots(self, destination: tuple):
        """
        Calculate the knots to use in the Bezier curve based on distance.
        Args:
            destination: x, y tuple of the destination point.
        """
        # Calculate the distance between the start and end points
        distance = np.sqrt((destination[0] - pag.position()[0]) ** 2 + (destination[1] - pag.position()[1]) ** 2)
        res = round(distance / 200)
        return min(res, 3)

    def __get_mouse_speed(self, speed: str) -> int:
        """
        Converts a text speed to a numeric speed for HumanCurve (targetPoints).
        """
        if speed == "slowest":
            min, max = 85, 100
        elif speed == "slow":
            min, max = 65, 80
        elif speed == "medium":
            min, max = 45, 60
        elif speed == "fast":
            min, max = 20, 40
        elif speed == "fastest":
            min, max = 10, 15
        else:
            raise ValueError("Invalid mouse speed. Try 'slowest', 'slow', 'medium', 'fast', or 'fastest'.")
        return round(truncated_normal_sample(min, max))


if __name__ == "__main__":
    mouse = Mouse()
    from geometry import Point

    mouse.move_to((1, 1))
    time.sleep(0.5)
    mouse.move_to(destination=Point(765, 503), mouseSpeed="slowest")
    time.sleep(0.5)
    mouse.move_to(destination=(1, 1), mouseSpeed="slow")
    time.sleep(0.5)
    mouse.move_to(destination=(300, 350), mouseSpeed="medium")
    time.sleep(0.5)
    mouse.move_to(destination=(400, 450), mouseSpeed="fast")
    time.sleep(0.5)
    mouse.move_to(destination=(234, 122), mouseSpeed="fastest")
    time.sleep(0.5)
    mouse.move_rel(0, 100)
    time.sleep(0.5)
    mouse.move_rel(0, 100)
