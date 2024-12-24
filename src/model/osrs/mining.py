import time
from typing import Union, Optional, List, Dict, Any
import os
import traceback

import cv2
import numpy as np

import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot, validate_types
from utilities.geometry import Point, Rectangle
from model.bot import BotStatus
from typing_extensions import TypeGuard
from utilities.type_utils import validate_module_attributes

class OSRSMining(OSRSBot):
    """
    Mining bot for OSRS.
    
    Attributes:
        running_time (int): How long to run in minutes
        take_breaks (bool): Whether to take random breaks
        rock_type (str): Type of rock to mine
        tag_color (Color): Color used for tagging rocks
        ores_mined (int): Counter for mined ores
        failed_searches (int): Counter for failed rock searches
        attempts_before_drop (int): Number of mining attempts before dropping inventory
        drop_chance (float): Chance to drop inventory
        debug_dir (str): Directory for debug screenshots
        debug_mode (bool): Whether debug mode is enabled
    """
    
    def __init__(self) -> None:
        bot_title: str = "Mining"
        description: str = "Mines rocks and drops inventory when full. Position near rocks and tag them."
        super().__init__(bot_title=bot_title, description=description)
        
        # Initialize default values with type hints
        self.running_time: int = 360
        self.take_breaks: bool = False
        self.rock_type: str = "Mithril"
        # Use the color object from clr module instead of raw RGB tuple
        self.tag_color = clr.PINK  # This should be a color object with lower/upper bounds
        self.ores_mined: int = 0
        self.failed_searches: int = 0
        self.attempts_before_drop: int = 22
        self.drop_chance: float = 0.1  # Default 10% chance to drop
        self.debug_mode: bool = False  # Default to False, can be enabled through options
        
        # Create debug directory if it doesn't exist
        self.debug_dir: str = "debug_screenshots/mining"
        os.makedirs(self.debug_dir, exist_ok=True)

    def create_options(self) -> None:
        """Set up the bot's options menu."""
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option("rock_type", "Rock type", ["Iron", "Coal", "Mithril", "Adamantite"])
        self.options_builder.add_slider_option("attempts_before_drop", "Mining attempts before inventory drop (23-27)", 23, 27)
        self.options_builder.add_slider_option("drop_chance", "Chance to drop inventory (0-100%)", 0, 100)
        self.options_builder.add_checkbox_option("debug_mode", "Enable debug mode?", [" "])

    @validate_types
    def save_options(self, options: Dict[str, Any]) -> None:
        """
        Save and validate the options.
        
        Args:
            options (Dict[str, Any]): Dictionary of option names and values
        """
        for option in options:
            if option == "running_time":
                self.running_time = int(options[option])
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "rock_type":
                if not isinstance(options[option], str):
                    raise TypeError(f"Rock type must be string, got {type(options[option])}")
                self.rock_type = options[option]
            elif option == "attempts_before_drop":
                self.attempts_before_drop = int(options[option])
            elif option == "drop_chance":
                self.drop_chance = float(options[option]) / 100.0  # Convert percentage to decimal
            elif option == "debug_mode":
                self.debug_mode = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks")
        self.log_msg(f"Rock type: {self.rock_type}")
        self.log_msg(f"Attempts before drop: {self.attempts_before_drop}")
        self.log_msg(f"Drop chance: {self.drop_chance*100:.1f}%")
        self.log_msg(f"Debug mode: {'enabled' if self.debug_mode else 'disabled'}")
        self.options_set = True

    @validate_types
    def main_loop(self) -> None:
        """Main bot loop implementation."""
        self.log_msg("Starting mining bot...")
        self.log_msg(f"Game view dimensions: {self.win.game_view.width}x{self.win.game_view.height}")
        
        if self.debug_mode:
            self.log_msg("Debug mode enabled - extra logging will be shown")
            self.debug_rock_detection()  # Initial debug visualization
        
        self.take_debug_screenshot("start_state")
        
        start_time: float = time.time()
        end_time: float = self.running_time * 60
        attempts: int = 0
        last_inventory_check: float = time.time()
        
        # Switch to inventory tab first
        self.log_msg("Switching to inventory tab...")
        self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()
        time.sleep(1)
        
        while time.time() - start_time < end_time:
            try:
                # Check if inventory needs managing
                if attempts >= self.attempts_before_drop:
                    self.log_msg(f"Inventory full! ({attempts}/{self.attempts_before_drop} attempts)")
                    
                    # Use drop_chance setting for inventory management decision
                    if rd.random_chance(self.drop_chance):
                        self.log_msg(f"Randomly chosen to drop inventory ({self.drop_chance*100:.1f}% chance)")
                        self.shift_drop_inventory()
                    else:
                        self.log_msg(f"Using banker's note ({(1-self.drop_chance)*100:.1f}% chance)")
                        self.use_bankers_note()
                        
                    attempts = 0
                    last_inventory_check = time.time()
                    continue
                
                self.log_msg(f"=== Starting rock search cycle ({attempts}/{self.attempts_before_drop} attempts) ===")
                if self.debug_mode:
                    self.log_msg("Calling find_nearest_rock...")
                    
                rock_point = self.find_nearest_rock()
                
                if self.debug_mode:
                    self.log_msg(f"find_nearest_rock returned: {rock_point}")
                    
                if rock_point:
                    assert isinstance(rock_point, Point), "find_nearest_rock returned non-Point type"
                    self.log_msg(f"Moving mouse to rock at: {rock_point}")
                    
                    # Move mouse to rock
                    self.mouse.move_to(rock_point, mouseSpeed="medium")
                    time.sleep(0.5)  # Wait after movement
                    
                    # Verify we can click
                    if not self.mouseover_text(contains="Mine"):
                        self.log_msg("No mine option found, skipping...")
                        time.sleep(1)
                        continue
                    
                    # Click and wait for mining
                    self.mouse.click()
                    attempts += 1
                    time.sleep(0.5)  # Wait after click
                    
                    if self.debug_mode:
                        self.log_msg("Mouse clicked, waiting for mining...")
                        
                    if self.wait_for_mining_completion():
                        self.ores_mined += 1
                        self.log_msg(f"Ores mined: {self.ores_mined} (attempts: {attempts}/{self.attempts_before_drop})")
                        if self.debug_mode:
                            self.log_msg(f"Debug: Mining successful, total attempts: {attempts}")
                        self.take_break()
                else:
                    self.log_msg("No valid rocks found this cycle")
                    if self.debug_mode:
                        self.debug_rock_detection()  # Run detection visualization on failures
                    time.sleep(1)
                
                progress: float = (time.time() - start_time) / end_time
                self.log_msg(f"Progress: {progress*100:.1f}%")
                self.update_progress(progress)
                
                if self.should_break():
                    self.log_msg("Break condition met, stopping...")
                    break
                    
            except Exception as e:
                self.log_msg(f"Error in main loop: {str(e)}")
                self.log_msg(f"Error type: {type(e).__name__}")
                self.log_msg(f"Error traceback: {traceback.format_exc()}")
                time.sleep(1)

    def is_rectangle(self, obj: object) -> TypeGuard[Rectangle]:
        """
        Type guard for Rectangle objects.
        
        Args:
            obj (object): Object to check
            
        Returns:
            TypeGuard[Rectangle]: True if obj is Rectangle
        """
        return isinstance(obj, Rectangle)

    @validate_types
    def shift_drop_inventory(self) -> None:
        """
        Drop inventory using shift-click, skipping first and last columns.
        Drops the middle 26 items (skips first column and last column).
        """
        try:
            self.log_msg("Dropping inventory...")
            
            # Get inventory slots from window
            slots = self.win.inventory_slots
            if not slots:
                self.log_msg("No inventory slots found")
                return
            
            # Drop middle 26 slots (skip first and last columns)
            for row in range(7):  # 7 rows
                for col in range(0, 4):  # Middle 2 columns (skip first and last)
                    if row == 0 and col == 0:
                        continue
                    if row == 6 and col == 3:
                        continue
                    slot_index = row * 4 + col  # 4 columns total
                    slot = slots[slot_index]
                    self.mouse.move_to(slot.random_point())
                    self.mouse.click(button="left", shift=True)
                    time.sleep(rd.random_float(0.1, 0.2))  # Small delay between drops
            
            self.log_msg("Inventory dropped")
            
        except Exception as e:
            self.log_msg(f"Error dropping inventory: {str(e)}")
            self.log_msg(f"Error type: {type(e).__name__}")
            self.log_msg(f"Error traceback: {traceback.format_exc()}")

    @validate_types
    def wait_for_mining_completion(self) -> bool:
        """
        Wait for mining animation to complete.
        
        Returns:
            bool: True if mining completed successfully, False if timeout or error
        """
        try:
            # Wait for animation to start
            time.sleep(0.5)  # Initial delay
            start_time = time.time()
            timeout = 5  # 5 second timeout
            
            # Wait for mining animation to start
            while not self.is_player_doing_action("Mining"):
                if time.time() - start_time > timeout:
                    self.log_msg("Mining didn't start")
                    return False
                time.sleep(0.1)
            
            self.log_msg("Mining started...")
            
            # Wait for mining to complete
            while self.is_player_doing_action("Mining"):
                time.sleep(0.1)
            
            self.log_msg("Mining completed")
            return True
            
        except Exception as e:
            self.log_msg(f"Error waiting for mining: {str(e)}")
            self.log_msg(f"Error type: {type(e).__name__}")
            self.log_msg(f"Error traceback: {traceback.format_exc()}")
            return False

    @validate_types
    @validate_module_attributes('rd.truncated_normal_sample', 'rd.random_chance')
    def take_break(self) -> None:
        """Take a random break between actions."""
        if not self.take_breaks:
            return

        if rd.random_chance(0.1):
            break_time: int = int(rd.truncated_normal_sample(1, 5, mean=3, std=1))
            self.log_msg(f"Taking a short break ({break_time}s)")
            time.sleep(break_time)

    @validate_types
    def take_debug_screenshot(self, reason: str) -> None:
        """
        Takes a screenshot for debugging purposes.
        
        Args:
            reason (str): Reason for taking screenshot, used in filename
        """
        try:
            timestamp: str = time.strftime("%Y%m%d_%H%M%S")
            filename: str = os.path.join(self.debug_dir, f"debug_{reason}_{timestamp}.png")
            screenshot = self.win.game_view.screenshot()
            if screenshot is not None:
                cv2.imwrite(filename, screenshot)
                self.log_msg(f"Debug screenshot saved: {filename}")
        except Exception as e:
            self.log_msg(f"Error taking debug screenshot: {str(e)}")

    def separate_rocks(self, mask: np.ndarray) -> np.ndarray:
        """
        Separate touching rocks using watershed segmentation.
        
        Args:
            mask (np.ndarray): Binary mask of tagged rocks
            
        Returns:
            np.ndarray: Labeled image where each rock has a unique label
        """
        try:
            self.log_msg("Starting watershed segmentation...")
            
            # Distance transform
            self.log_msg("Computing distance transform...")
            dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
            
            # Normalize for visualization
            self.log_msg("Normalizing distance transform...")
            cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
            
            # Threshold to get markers
            self.log_msg("Thresholding to get markers...")
            _, sure_fg = cv2.threshold(dist, 0.5, 1.0, 0)
            sure_fg = np.uint8(sure_fg)
            
            # Find background
            self.log_msg("Finding background...")
            sure_bg = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=3)
            
            # Unknown region
            self.log_msg("Computing unknown region...")
            unknown = cv2.subtract(sure_bg, sure_fg)
            
            # Label markers
            self.log_msg("Labeling markers...")
            _, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            
            # Apply watershed
            self.log_msg("Applying watershed...")
            markers = cv2.watershed(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), markers)
            
            if self.debug_mode:
                # Save watershed visualization
                watershed_vis = np.zeros_like(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))
                watershed_vis[markers > 1] = [0, 255, 0]  # Green for rock regions
                watershed_vis[markers == -1] = [0, 0, 255]  # Red for boundaries
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                watershed_filename = os.path.join(self.debug_dir, f"watershed_debug_{timestamp}.png")
                cv2.imwrite(watershed_filename, watershed_vis)
                self.log_msg(f"Saved watershed visualization to {watershed_filename}")
            
            self.log_msg("Watershed segmentation complete")
            return markers
            
        except Exception as e:
            self.log_msg(f"Error in separate_rocks: {str(e)}")
            self.log_msg(f"Error type: {type(e).__name__}")
            self.log_msg(f"Error traceback: {traceback.format_exc()}")
            # Return original mask as markers in case of error
            return np.array(mask > 0, dtype=np.int32)

    @validate_types
    def debug_rock_detection(self) -> None:
        """
        Debug method to visualize tagged rocks using HSV color detection.
        Takes a screenshot and draws rectangles around detected rocks.
        """
        try:
            self.log_msg("Starting rock detection debug...")
            game_view = self.win.game_view.screenshot()
            if game_view is None:
                self.log_msg("Failed to capture screenshot")
                return

            # Convert to HSV and create mask
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)
            lower_pink = np.array([145, 30, 180])
            upper_pink = np.array([175, 255, 255])
            pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)
            
            # Save original mask for debugging
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            mask_filename = os.path.join(self.debug_dir, f"debug_mask_{timestamp}.png")
            cv2.imwrite(mask_filename, pink_mask)
            
            # Clean up mask
            kernel = np.ones((5,5), np.uint8)
            pink_mask = cv2.morphologyEx(pink_mask, cv2.MORPH_CLOSE, kernel)
            pink_mask = cv2.morphologyEx(pink_mask, cv2.MORPH_OPEN, kernel)
            
            # Separate rocks using watershed
            markers = self.separate_rocks(pink_mask)
            
            # Get unique labels (excluding background -1 and 0)
            unique_labels = np.unique(markers)[2:]  # Skip -1 (watershed boundaries) and 0 (background)
            self.log_msg(f"Found {len(unique_labels)} potential rocks")
            
            # Draw debug visualization
            debug_img = game_view.copy()
            valid_rocks = 0
            
            for label in unique_labels:
                # Create mask for this rock
                rock_mask = np.uint8(markers == label)
                
                # Get contour for this rock
                contours, _ = cv2.findContours(rock_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    continue
                    
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contours[0])
                area = cv2.contourArea(contours[0])
                width_height_diff = abs(w - h)
                
                # Log detailed information about each rock
                self.log_msg(f"\nRock {label}:")
                self.log_msg(f"  Area: {area:.1f}")
                self.log_msg(f"  Size: {w}x{h} (diff: {width_height_diff})")
                self.log_msg(f"  Position: ({x}, {y})")
                
                # Check each criterion separately
                area_valid = 1000 < area < 70000
                shape_valid = width_height_diff < 100
                
                self.log_msg(f"  Area valid: {area_valid} (1000 < {area:.1f} < 70000)")
                self.log_msg(f"  Shape valid: {shape_valid} (diff: {width_height_diff} < 100)")
                
                if area_valid and shape_valid:
                    # Draw green rectangle for valid rocks
                    cv2.rectangle(
                        debug_img,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),  # Green
                        2
                    )
                    # Draw target point
                    target_x = x + w // 2
                    target_y = y + int(h * 0.6)
                    cv2.circle(debug_img, (target_x, target_y), 3, (0, 0, 255), -1)
                    valid_rocks += 1
                else:
                    # Draw red rectangle for invalid rocks
                    cv2.rectangle(
                        debug_img,
                        (x, y),
                        (x + w, y + h),
                        (0, 0, 255),  # Red
                        1
                    )
                
                # Add detailed rock info to image
                cv2.putText(
                    debug_img,
                    f"#{label} A:{int(area)} {w}x{h} d:{width_height_diff}",
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 255, 255),
                    1
                )
            
            self.log_msg(f"\nFound {valid_rocks} valid rocks out of {len(unique_labels)} potential rocks")
            
            # Save watershed result for debugging
            watershed_vis = np.zeros_like(game_view)
            watershed_vis[markers > 1] = [0, 255, 0]  # Green for rock regions
            watershed_vis[markers == -1] = [0, 0, 255]  # Red for boundaries
            watershed_filename = os.path.join(self.debug_dir, f"watershed_{timestamp}.png")
            cv2.imwrite(watershed_filename, watershed_vis)
            
            # Save debug visualization
            debug_filename = os.path.join(self.debug_dir, f"debug_visualization_{timestamp}.png")
            cv2.imwrite(debug_filename, debug_img)
            self.log_msg(f"Saved debug visualization to: {debug_filename}")

        except Exception as e:
            self.log_msg(f"Error in debug_rock_detection: {str(e)}")
            self.log_msg(f"Error type: {type(e).__name__}")
            self.log_msg(f"Error traceback: {traceback.format_exc()}")

    @validate_types
    def test_rock_detection(self, duration_seconds: int = 10) -> None:
        """
        Test rock detection for a specified duration.
        Takes debug screenshots every second.
        
        Args:
            duration_seconds (int): How long to run the test
        """
        self.log_msg(f"Starting rock detection test for {duration_seconds} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            self.debug_rock_detection()
            time.sleep(1)
            
        self.log_msg("Rock detection test complete") 

    @validate_types
    def visualize_tagged_rocks(self, tagged_rocks: List[Rectangle], screenshot: np.ndarray, prefix: str = "debug") -> None:
        """
        Helper method to visualize tagged rocks on a screenshot.
        
        Args:
            tagged_rocks (List[Rectangle]): List of tagged rocks to visualize
            screenshot (np.ndarray): Screenshot to draw on
            prefix (str): Prefix for the saved file name
        """
        try:
            debug_img = screenshot.copy()
            
            for i, rock in enumerate(tagged_rocks):
                cv2.rectangle(
                    debug_img,
                    (rock.x, rock.y),
                    (rock.x + rock.width, rock.y + rock.height),
                    (0, 255, 0),  # Green
                    2
                )
                self.log_msg(f"Rock {i+1} at: {rock}")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename: str = os.path.join(self.debug_dir, f"{prefix}_tagged_rocks_{timestamp}.png")
            cv2.imwrite(filename, debug_img)
            self.log_msg(f"Saved tagged rocks visualization to: {filename}")
            
        except Exception as e:
            self.log_msg(f"Error in visualize_tagged_rocks: {str(e)}")
            self.log_msg(f"Error type: {type(e).__name__}")
            self.log_msg(f"Error traceback: {traceback.format_exc()}") 

    @validate_types
    def should_break(self) -> bool:
        """Check if the bot should stop running"""
        try:
            if not self.thread:
                self.log_msg("Stop detected: Thread is None")
                return True
            if not self.thread.is_alive():
                self.log_msg("Stop detected: Thread is not alive")
                return True
            return False
        except Exception as e:
            self.log_msg(f"Error checking thread status: {str(e)}")
            return True

    @validate_types
    def find_nearest_rock(self) -> Optional[Point]:
        """
        Find nearest tagged rock.
        
        Returns:
            Optional[Point]: Click point for the rock if found, None if no rock found or error occurs
        """
        try:
            self.log_msg("Taking game view screenshot...")
            # Take screenshot of game view
            game_view = self.win.game_view.screenshot()
            
            if game_view is None:
                self.log_msg("Failed to get game view screenshot")
                return None
            
            self.log_msg("Converting to HSV...")
            # Convert to HSV for better pink detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)
            
            # Define pink color range
            lower_pink = np.array([145, 30, 180])
            upper_pink = np.array([175, 255, 255])
            
            self.log_msg("Creating pink mask...")
            # Create mask for pink color
            pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)
            
            # Clean up mask
            kernel = np.ones((5,5), np.uint8)
            pink_mask = cv2.morphologyEx(pink_mask, cv2.MORPH_CLOSE, kernel)
            pink_mask = cv2.morphologyEx(pink_mask, cv2.MORPH_OPEN, kernel)
            
            if self.debug_mode:
                # Save the mask for debugging
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                mask_filename = os.path.join(self.debug_dir, f"find_rock_mask_{timestamp}.png")
                cv2.imwrite(mask_filename, pink_mask)
                self.log_msg(f"Saved pink mask to {mask_filename}")
            
            self.log_msg("Separating rocks using watershed...")
            # Separate rocks using watershed
            markers = self.separate_rocks(pink_mask)
            
            # Get unique labels (excluding background -1 and 0)
            unique_labels = np.unique(markers)[2:]  # Skip -1 (watershed boundaries) and 0 (background)
            
            if self.debug_mode:
                self.log_msg(f"Found {len(unique_labels)} potential rocks in find_nearest_rock")
            
            if len(unique_labels) == 0:
                self.log_msg("No rocks found")
                return None
            
            self.log_msg("Getting game view center...")
            # Get center point of game view for distance calculation
            center = self.win.game_view.get_center()
            
            # Find closest valid rock
            closest_rock = None
            min_distance = float("inf")
            
            self.log_msg("Processing rock contours...")
            for label in unique_labels:
                try:
                    # Create mask for this rock
                    rock_mask = np.uint8(markers == label)
                    
                    # Get contour for this rock
                    contours, _ = cv2.findContours(rock_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if not contours:
                        continue
                    
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contours[0])
                    area = cv2.contourArea(contours[0])
                    
                    if self.debug_mode:
                        self.log_msg(f"Checking rock {label}:")
                        self.log_msg(f"  Area: {area}")
                        self.log_msg(f"  Size: {w}x{h}")
                        self.log_msg(f"  Position: ({x}, {y})")
                    
                    # Check if rock matches criteria - increased area range
                    if 1000 < area < 100000 and abs(w - h) < 100:  # Increased max area to 100000
                        # Calculate center point with slight offset below center
                        cx = x + w // 2
                        cy = y + int(h * 0.6)  # Aim slightly below center
                        distance = ((cx - center.x) ** 2 + (cy - center.y) ** 2) ** 0.5
                        
                        if self.debug_mode:
                            self.log_msg(f"  Distance from center: {distance}")
                            self.log_msg(f"  Valid rock: Yes")
                        
                        if distance < min_distance:
                            min_distance = distance
                            # Add some randomization to click point using truncated normal distribution
                            rand_x = int(rd.truncated_normal_sample(-10, 10, mean=0, std=5))
                            rand_y = int(rd.truncated_normal_sample(-5, 5, mean=0, std=2))
                            
                            # Translate coordinates relative to game window
                            game_view_rect = self.win.game_view
                            abs_x = game_view_rect.left + cx + rand_x
                            abs_y = game_view_rect.top + cy + rand_y
                            
                            closest_rock = Point(abs_x, abs_y)
                            
                            if self.debug_mode:
                                self.log_msg(f"  Game view offset: ({game_view_rect.left}, {game_view_rect.top})")
                                self.log_msg(f"  Relative coords: ({cx}, {cy})")
                                self.log_msg(f"  Absolute coords: ({abs_x}, {abs_y})")
                    elif self.debug_mode:
                        self.log_msg(f"  Valid rock: No (failed validation checks)")
                except Exception as e:
                    self.log_msg(f"Error processing rock {label}: {str(e)}")
                    continue
            
            if closest_rock:
                if self.debug_mode:
                    self.log_msg(f"Selected click point: ({closest_rock.x}, {closest_rock.y})")
                    # Draw debug visualization
                    debug_img = game_view.copy()
                    # Draw relative to game view coordinates
                    rel_x = closest_rock.x - self.win.game_view.left
                    rel_y = closest_rock.y - self.win.game_view.top
                    cv2.circle(debug_img, (rel_x, rel_y), 5, (0, 255, 0), -1)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    debug_filename = os.path.join(self.debug_dir, f"click_target_{timestamp}.png")
                    cv2.imwrite(debug_filename, debug_img)
                    self.log_msg("Returning closest rock point")
                return closest_rock
            
            self.log_msg("No valid rocks found")
            return None

        except Exception as e:
            self.log_msg(f"Error in find_nearest_rock: {str(e)}")
            self.log_msg(f"Error type: {type(e).__name__}")
            self.log_msg(f"Error traceback: {traceback.format_exc()}")
            return None 