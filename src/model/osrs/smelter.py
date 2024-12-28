import time
from typing import Union, Optional

import cv2
import numpy as np
import os
import traceback

import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point, Rectangle


class OSRSSmelter(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Blast Furnace Smelter"
        description = "Smelts bars at the blast furnace using Banker's Note. Position near the conveyor belt."
        super().__init__(bot_title=bot_title, description=description)
        
        # Initialize default values
        self.running_time = 360  # Default of 60 minutes
        self.take_breaks = False
        self.ore_type = "Adamant"  # Default ore type
        self.bars_smelted = 0
        self.failed_searches = 0
        self.debug_mode = False  # Add debug mode flag
        
        # Define ore types and their properties
        self.ore_types = {
            "Bronze": {"coal_needed": 0, "xp": 6.2},
            "Iron": {"coal_needed": 0, "xp": 12.5},
            "Steel": {"coal_needed": 1, "xp": 17.5},
            "Mithril": {"coal_needed": 2, "xp": 30},
            "Adamant": {"coal_needed": 3, "xp": 37.5},
            "Rune": {"coal_needed": 4, "xp": 50},
        }
        
        # Add color constants
        self.BELT_COLOR = clr.PINK
        self.COLLECTION_COLOR = clr.RED
        
        # Create debug directory
        self.debug_dir = "debug_screenshots/smelting"
        os.makedirs(self.debug_dir, exist_ok=True)

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option("ore_type", "Ore type", ["Bronze", "Iron", "Steel", "Mithril", "Adamant", "Rune"])
        self.options_builder.add_checkbox_option("debug_mode", "Enable debug mode?", [" "])  # Add debug mode option

    def save_options(self, options: dict):
        """
        Save the options from the GUI.
        """
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "ore_type":
                self.ore_type = options[option]
            elif option == "debug_mode":  # Add debug mode handling
                self.debug_mode = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return
        
        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks")
        self.log_msg(f"Ore type: {self.ore_type}")
        self.log_msg(f"Debug mode: {'enabled' if self.debug_mode else 'disabled'}")
        self.options_set = True

    def main_loop(self):
        """
        Main bot loop for the blast furnace smelting process
        """
        self.log_msg("Starting blast furnace smelting bot...")
        
        # Main timing
        start_time = time.time()
        end_time = self.running_time * 60
        
        while time.time() - start_time < end_time:
            # Check if bot should stop
            if self.should_stop():
                self.log_msg("Bot stopped by user.")
                break
            
            try:
                # Main smelting cycle
                if not self.withdraw_ore():
                    continue
                    
                if not self.put_on_belt():  # Long delay after ore
                    continue
                    
                if self.ore_types[self.ore_type]["coal_needed"] > 0:
                    for i in range(self.ore_types[self.ore_type]["coal_needed"]):
                        if not self.withdraw_coal():
                            continue
                        if not self.put_coal_on_belt():  # Short delay for coal
                            continue
                
                if not self.collect_bars():
                    continue
                    
                if not self.deposit_bars():
                    continue
                    
                self.bars_smelted += 1
                self.log_msg(f"Successfully smelted {self.bars_smelted} sets of bars")
                
            except Exception as e:
                self.log_msg(f"Error in main loop: {e}")
                time.sleep(2)
                
        self.log_msg(f"Bot finished. Total runtime: {int((time.time() - start_time) / 60)} minutes")
        self.log_msg(f"Total bars smelted: {self.bars_smelted}")

    def withdraw_ore(self) -> bool:
        """
        Withdraws ore using banker's note in first inventory slot
        Returns: True if successful, False otherwise
        """
        try:
            first_slot = self.win.inventory_slots[0]
            if not first_slot:
                self.log_msg("Could not find first inventory slot")
                return False

            # Slower mouse movements
            self.mouse.move_to(first_slot.random_point(), duration=rd.truncated_normal_sample(0.5, 1.0))
            self.mouse.click()
            time.sleep(rd.truncated_normal_sample(0.4, 0.8))  # Longer delays

            bankers_note = self.win.inventory_slots[1]
            if not bankers_note:
                self.log_msg("Could not find banker's note")
                return False

            self.mouse.move_to(bankers_note.random_point(), duration=rd.truncated_normal_sample(0.5, 1.0))
            self.mouse.click()
            time.sleep(rd.truncated_normal_sample(0.4, 0.8))

            return True

        except Exception as e:
            self.log_msg(f"Error withdrawing ore: {e}")
            return False

    def withdraw_coal(self) -> bool:
        """
        Withdraws coal using banker's note in third inventory slot
        Returns: True if successful, False otherwise
        """
        try:
            third_slot = self.win.inventory_slots[2]
            if not third_slot:
                self.log_msg("Could not find third inventory slot")
                return False

            self.mouse.move_to(third_slot.random_point(), duration=rd.truncated_normal_sample(0.5, 1.0))
            self.mouse.click()
            time.sleep(rd.truncated_normal_sample(0.4, 0.8))

            bankers_note = self.win.inventory_slots[1]
            if not bankers_note:
                self.log_msg("Could not find banker's note")
                return False

            self.mouse.move_to(bankers_note.random_point(), duration=rd.truncated_normal_sample(0.5, 1.0))
            self.mouse.click()
            time.sleep(rd.truncated_normal_sample(0.4, 0.8))

            return True

        except Exception as e:
            self.log_msg(f"Error withdrawing coal: {e}")
            return False

    def put_on_belt(self) -> bool:
        """
        Puts ore on the conveyor belt and waits for character to run back
        Returns: True if successful, False otherwise
        """
        try:
            belt_point = self.find_conveyor_belt()
            if not belt_point:
                self.log_msg("Could not find conveyor belt")
                return False

            self.mouse.move_to(belt_point, duration=rd.truncated_normal_sample(0.5, 1.0))
            self.mouse.click()
            
            # Long delay for running back from ore deposit
            time.sleep(rd.truncated_normal_sample(4500, 6000) / 1000)

            return True

        except Exception as e:
            self.log_msg(f"Error putting ore on belt: {e}")
            return False

    def put_coal_on_belt(self) -> bool:
        """
        Puts coal on the conveyor belt with minimal delay (already next to belt)
        Returns: True if successful, False otherwise
        """
        try:
            belt_point = self.find_conveyor_belt()
            if not belt_point:
                self.log_msg("Could not find conveyor belt")
                return False

            self.mouse.move_to(belt_point, duration=rd.truncated_normal_sample(0.5, 1.0))
            self.mouse.click()
            
            # Short delay since we're already at the belt
            time.sleep(rd.truncated_normal_sample(600, 800) / 1000)

            return True

        except Exception as e:
            self.log_msg(f"Error putting coal on belt: {e}")
            return False

    def collect_bars(self) -> bool:
        """
        Collects smelted bars from the collection point
        Returns: True if successful, False otherwise
        """
        try:
            max_retries = 3
            for attempt in range(max_retries):
                # Find the collection point
                collection_point = self.find_collection_point()
                if not collection_point:
                    self.log_msg(f"Could not find collection point (attempt {attempt + 1}/{max_retries})")
                    time.sleep(1)
                    continue

                # Move mouse to collection point
                self.mouse.move_to(collection_point, mouseSpeed="medium")
                time.sleep(0.5)  # Wait after movement
                
                # Take debug screenshot
                if self.debug_mode:
                    self.take_debug_screenshot(f"collect_bars_attempt_{attempt}")
                    current_text = self.get_mouseover_text()  # Get current mouseover text for debugging
                    self.log_msg(f"Current mouseover text: '{current_text}'")
                
                # Verify we can click
                if not self.mouseover_text(contains="Take Bar"):
                    self.log_msg(f"No 'Take bar' option found (attempt {attempt + 1}/{max_retries})")
                    if attempt == max_retries - 1:
                        self.log_msg("Failed to find 'Take bar' option after all attempts. Stopping bot...")
                        self.stop()
                    time.sleep(1)
                    continue
                
                # Click the collection point
                self.mouse.click()
                
                # Wait for character to run to collection point (2-3 seconds)
                time.sleep(rd.truncated_normal_sample(4500, 6000) / 1000)
                
                # Press spacebar using pyautogui
                import pyautogui as pag
                pag.press('space')
                time.sleep(rd.truncated_normal_sample(200, 400) / 1000)  # Short delay after collection
                
                return True

            self.log_msg("Failed to collect bars after all attempts")
            return False

        except Exception as e:
            self.log_msg(f"Error collecting bars: {e}")
            return False

    def deposit_bars(self) -> bool:
        """
        Deposits bars using banker's note
        Returns: True if successful, False otherwise
        """
        try:
            # Get a bar slot (trying slots 4-7, which are 5th-8th slots)
            for slot_index in range(4, 8):
                bar_slot = self.win.inventory_slots[slot_index]
                if bar_slot:
                    # Click the bar
                    self.mouse.move_to(bar_slot.random_point())
                    self.mouse.click()
                    time.sleep(rd.truncated_normal_sample(200, 400) / 1000)  # 200-400ms delay

                    # Click banker's note (second slot)
                    bankers_note = self.win.inventory_slots[1]  # 0-based index, so 1 is second slot
                    if not bankers_note:
                        self.log_msg("Could not find banker's note")
                        return False

                    self.mouse.move_to(bankers_note.random_point())
                    self.mouse.click()
                    time.sleep(rd.truncated_normal_sample(200, 400) / 1000)  # 200-400ms delay

                    return True

            self.log_msg("Could not find bars in slots 5-8")
            return False

        except Exception as e:
            self.log_msg(f"Error depositing bars: {e}")
            return False

    def find_conveyor_belt(self) -> Optional[Point]:
        """
        Finds the conveyor belt using pink color detection
        Returns: Point if found, None otherwise
        """
        try:
            # Take screenshot of game view
            game_view = self.win.game_view.screenshot()
            if game_view is None:
                self.log_msg("Failed to get game view screenshot")
                return None

            # Create a mask to ignore the bottom portion of the screen
            height, width = game_view.shape[:2]
            bottom_cutoff = int(height * 0.7)  # Ignore bottom 30% of screen
            
            # Convert to HSV for better pink detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)
            
            # Define pink color range for the conveyor belt (bright pink/magenta)
            lower_pink = np.array([150, 100, 200])  # Increased brightness threshold
            upper_pink = np.array([165, 255, 255])
            
            # Create mask
            pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)
            
            # Mask out bottom portion
            pink_mask[bottom_cutoff:, :] = 0
            
            # Save debug mask and log color values
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(os.path.join(self.debug_dir, f"debug_belt_mask_{timestamp}.png"), pink_mask)
            self.log_msg(f"Using HSV pink range - Lower: {lower_pink}, Upper: {upper_pink}")
            
            # Find contours
            contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Create debug image
            debug_img = game_view.copy()
            cv2.line(debug_img, (0, bottom_cutoff), (width, bottom_cutoff), (0, 255, 0), 2)
            
            if contours:
                self.log_msg(f"Found {len(contours)} pink objects")
                
                # Filter and analyze contours
                valid_contours = []
                for i, contour in enumerate(contours):
                    area = cv2.contourArea(contour)
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w)/h if h != 0 else 0
                    
                    # Debug logging for each contour
                    self.log_msg(f"Contour {i}:")
                    self.log_msg(f"  Area: {area}")
                    self.log_msg(f"  Size: {w}x{h}")
                    self.log_msg(f"  Aspect ratio: {aspect_ratio:.2f}")
                    self.log_msg(f"  Position: ({x}, {y})")
                    
                    # Draw all contours in red first
                    cv2.drawContours(debug_img, [contour], -1, (0, 0, 255), 2)
                    
                    # More lenient size constraints
                    if 5000 < area < 25000:  # Much wider area range
                        self.log_msg(f"  Area check passed")
                        if 0.2 < aspect_ratio < 5.0:  # Much wider aspect ratio range
                            self.log_msg(f"  Aspect ratio check passed")
                            valid_contours.append(contour)
                            # Draw valid contours in green
                            cv2.drawContours(debug_img, [contour], -1, (0, 255, 0), 2)
                            self.log_msg(f"  Added as valid contour!")

                # Save debug image with all contours
                cv2.imwrite(os.path.join(self.debug_dir, f"debug_belt_all_contours_{timestamp}.png"), debug_img)
                
                self.log_msg(f"Found {len(valid_contours)} valid contours")
                
                if valid_contours:
                    # Get center point of game view
                    center = self.win.game_view.get_center()
                    
                    # Find closest valid pink square
                    closest_point = None
                    min_distance = float("inf")
                    
                    for contour in valid_contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        cx = x + w // 2
                        cy = y + h // 2
                        
                        distance = ((cx - center.x) ** 2 + (cy - center.y) ** 2) ** 0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_point = Point(cx, cy)
                    
                    if closest_point:
                        # Draw selected point on debug image
                        cv2.circle(debug_img, (closest_point.x, closest_point.y), 5, (255, 0, 0), -1)
                        cv2.imwrite(os.path.join(self.debug_dir, f"debug_belt_selected_{timestamp}.png"), debug_img)
                        
                        # Translate coordinates
                        game_view_rect = self.win.game_view
                        abs_x = game_view_rect.left + closest_point.x
                        abs_y = game_view_rect.top + closest_point.y
                        
                        self.log_msg(f"Found valid conveyor belt at: ({abs_x}, {abs_y})")
                        return Point(abs_x, abs_y)
                
                self.log_msg("No valid pink squares found")
                return None

            self.log_msg("No pink objects found")
            return None

        except Exception as e:
            self.log_msg(f"Error finding conveyor belt: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            return None

    def find_collection_point(self) -> Optional[Point]:
        """
        Finds the bar collection point using red color detection
        Returns: Point on the left half of the red rectangle if found, None otherwise
        """
        try:
            # Take screenshot of game view
            game_view = self.win.game_view.screenshot()
            if game_view is None:
                self.log_msg("Failed to get game view screenshot")
                return None

            height, width = game_view.shape[:2]

            # Convert to HSV for better red detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)

            # Define red color ranges (red wraps around in HSV)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])

            # Create masks for both red ranges and combine
            red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)

            # Save debug mask
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cv2.imwrite(os.path.join(self.debug_dir, f"debug_collection_mask_{timestamp}.png"), red_mask)

            # Find contours
            contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Create debug image
            debug_img = game_view.copy()

            if contours:
                self.log_msg(f"Found {len(contours)} red objects")

                # Filter and analyze contours
                valid_contours = []
                for i, contour in enumerate(contours):
                    area = cv2.contourArea(contour)
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w)/h if h != 0 else 0

                    # Debug logging for each contour
                    self.log_msg(f"Contour {i}:")
                    self.log_msg(f"  Area: {area}")
                    self.log_msg(f"  Size: {w}x{h}")
                    self.log_msg(f"  Aspect ratio: {aspect_ratio:.2f}")
                    self.log_msg(f"  Position: ({x}, {y})")

                    # Draw all contours in red
                    cv2.drawContours(debug_img, [contour], -1, (0, 0, 255), 2)

                    # More lenient size constraints
                    if 5000 < area < 50000:  # Much wider area range
                        self.log_msg(f"  Area check passed")
                        if 0.2 < aspect_ratio < 5.0:  # Much wider aspect ratio range
                            self.log_msg(f"  Aspect ratio check passed")
                            valid_contours.append(contour)
                            # Draw valid contours in green
                            cv2.drawContours(debug_img, [contour], -1, (0, 255, 0), 2)
                            self.log_msg(f"  Added as valid contour!")

                # Save debug image with all contours
                cv2.imwrite(os.path.join(self.debug_dir, f"debug_collection_all_contours_{timestamp}.png"), debug_img)

                self.log_msg(f"Found {len(valid_contours)} valid contours")

                if valid_contours:
                    # Get center point of game view for distance calculation
                    center = self.win.game_view.get_center()

                    # Find closest valid red rectangle
                    closest_point = None
                    min_distance = float("inf")

                    for contour in valid_contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        # Calculate point in the left quarter of the rectangle
                        cx = x + (w // 4)  # 1/4 of the way from the left
                        cy = y + (h // 2)  # Vertically centered

                        distance = ((cx - center.x) ** 2 + (cy - center.y) ** 2) ** 0.5

                        if distance < min_distance:
                            min_distance = distance
                            closest_point = Point(cx, cy)

                    if closest_point:
                        # Draw selected point on debug image
                        cv2.circle(debug_img, (closest_point.x, closest_point.y), 5, (255, 0, 0), -1)
                        cv2.imwrite(os.path.join(self.debug_dir, f"debug_collection_selected_{timestamp}.png"), debug_img)

                        # Translate coordinates relative to game window
                        game_view_rect = self.win.game_view
                        abs_x = game_view_rect.left + closest_point.x
                        abs_y = game_view_rect.top + closest_point.y

                        self.log_msg(f"Found collection point at: ({abs_x}, {abs_y})")
                        return Point(abs_x, abs_y)

                self.log_msg("No valid red rectangles found")
                return None

            self.log_msg("No red objects found")
            return None

        except Exception as e:
            self.log_msg(f"Error finding collection point: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            return None

    def take_break(self):
        """
        Takes a short break between actions
        """
        if not self.take_breaks:
            return

        if rd.random_chance(0.1):  # 10% chance to take break
            break_time = rd.random_int(1, 5)
            self.log_msg(f"Taking a short break ({break_time}s)")
            time.sleep(break_time)

    def should_stop(self) -> bool:
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