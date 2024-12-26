import time
from typing import Union

import cv2
import numpy as np

import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point


class OSRSWoodcutter(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Woodcutter"
        description = "Chops trees and banks logs using Banker's Note (for now). Position near trees and tag them."
        super().__init__(bot_title=bot_title, description=description)

        # Initialize default values
        self.running_time = 360  # Default of 60 minutes
        self.take_breaks = False
        self.tree_type = "Oak"  # Default tree type
        self.tag_color = clr.PINK  # Default tag color
        self.logs_chopped = 0
        self.failed_searches = 0

        # Define tree types and their properties
        self.tree_types = {
            "Normal": {"level": 1, "xp": 25},
            "Oak": {"level": 15, "xp": 37.5},
            "Willow": {"level": 30, "xp": 67.5},
            "Maple": {"level": 45, "xp": 100},
            "Yew": {"level": 60, "xp": 175},
            "Magic": {"level": 75, "xp": 250},
            "Mahogany": {"level": 50, "xp": 125},
        }

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option("tree_type", "Tree type", ["Normal", "Oak", "Willow", "Maple", "Yew", "Magic", "Mahogany"])

    def save_options(self, options: dict):
        """
        Save the options from the GUI.
        """
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "tree_type":
                self.tree_type = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks")
        self.log_msg(f"Tree type: {self.tree_type}")
        self.options_set = True

    def main_loop(self):
        """
        Main bot loop with time and tree-count based inventory management
        """
        self.log_msg("Starting woodcutting bot...")
        self.use_bankers_note()
        self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()
        time.sleep(1)

        # Main timing
        start_time = time.time()
        end_time = self.running_time * 60

        # Inventory management tracking
        successful_chops = 0
        last_note_time = time.time()
        
        while time.time() - start_time < end_time:
            try:
                # Check if we need to note items based on time
                if time.time() - last_note_time >= 180:  # 3 minutes
                    self.log_msg("3 minutes passed, using banker's note...")
                    if self.use_bankers_note():
                        successful_chops = 0
                        last_note_time = time.time()
                    time.sleep(2)
                    continue

                # Check if we need to note items based on chops
                if successful_chops >= 3:
                    self.log_msg("3 successful chops, using banker's note...")
                    if self.use_bankers_note():
                        successful_chops = 0
                        last_note_time = time.time()
                    time.sleep(2)
                    continue

                # Find and click tree
                tree = self.find_tagged_tree()
                if not tree:
                    self.log_msg("No tree found, waiting...")
                    time.sleep(2)
                    continue
                
                # Click tree and verify chop option
                self.mouse.move_to(tree)
                time.sleep(0.5)
                
                if not self.mouseover_text(contains="Chop"):
                    self.log_msg("No chop option, waiting...")
                    if not self.mouseover_text(contains="Cut"):
                        self.log_msg("No cut option either, waiting...")
                        time.sleep(1.5)
                        continue
                    
                self.mouse.click()
                time.sleep(3)

                # Wait for chopping to finish using not_woodcutting counter
                not_woodcutting_count = 0
                last_action_check = time.time()

                while True:
                    if time.time() - last_action_check >= 1.5:
                        if self.is_player_doing_action("Woodcutting"):
                            not_woodcutting_count = 0
                            self.log_msg("Still chopping...")
                        else:
                            not_woodcutting_count += 1
                            self.log_msg(f"Not chopping check #{not_woodcutting_count}")
                            if not_woodcutting_count >= 2:
                                self.log_msg("No longer chopping, looking for new tree...")
                                break
                        last_action_check = time.time()
                    time.sleep(0.1)

                # If we got here, we successfully chopped a tree
                successful_chops += 1
                self.log_msg(f"Successful chops this cycle: {successful_chops}")
                time.sleep(1)

            except Exception as e:
                self.log_msg(f"Error in main loop: {e}")
                time.sleep(2)

        self.log_msg(f"Bot finished. Total runtime: {int((time.time() - start_time) / 60)} minutes")

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

    def find_tagged_tree(self) -> Point | None:
        """
        Find nearest tagged tree using color detection.
        Returns: Point if found, None otherwise
        """
        try:
            # Take screenshot of game view
            game_view = self.win.game_view.screenshot()

            if game_view is None:
                self.log_msg("Failed to get game view screenshot")
                return None

            # Log image dimensions
            h, w = game_view.shape[:2]
            self.log_msg(f"Game view dimensions: {w}x{h}")

            # Convert to HSV for better pink detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)

            # Define pink color range
            lower_pink = np.array([145, 30, 180])
            upper_pink = np.array([175, 255, 255])

            # Create mask for pink color
            pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)

            # Count pink pixels
            pink_pixels = cv2.countNonZero(pink_mask)
            self.log_msg(f"Total pink pixels detected: {pink_pixels}")

            # Find contours
            contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            self.log_msg(f"Number of contours found: {len(contours)}")

            if not contours:
                self.log_msg("No pink contours found")
                return None

            # Get center point of game view for distance calculation
            center = self.win.game_view.get_center()
            self.log_msg(f"Game view center: ({center.x}, {center.y})")

            # Find closest valid tree contour
            closest_tree = None
            min_distance = float("inf")

            # Log details for each contour
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h != 0 else 0

                self.log_msg(f"Contour {i}:")
                self.log_msg(f"  Area: {area}")
                self.log_msg(f"  Perimeter: {perimeter}")
                self.log_msg(f"  Bounding box: x={x}, y={y}, w={w}, h={h}")
                self.log_msg(f"  Aspect ratio: {aspect_ratio}")

                # Check if contour matches tree criteria
                if 5000 < area < 30000 and 0.8 < aspect_ratio < 1.2 and abs(w - h) < 50:
                    # Calculate center point - move slightly towards the trunk
                    cx = x + w // 2
                    cy = y + int(h * 0.6)  # Aim 60% down from the top
                    distance = ((cx - center.x) ** 2 + (cy - center.y) ** 2) ** 0.5

                    self.log_msg(f"  Distance from center: {distance}")
                    self.log_msg(f"  Valid contour: Yes")

                    if distance < min_distance:
                        min_distance = distance
                        # Store more info about the tree
                        closest_tree = {"center": Point(cx, cy), "width": w, "height": h, "area": area}
                else:
                    self.log_msg(f"  Valid contour: No (failed validation checks)")

            if closest_tree:
                import random

                # Calculate random point inside the tree (avoiding edges)
                w_offset = closest_tree["width"] // 4
                h_offset = closest_tree["height"] // 4
                offset_x = random.randint(-w_offset, w_offset)
                offset_y = random.randint(-h_offset, h_offset)

                final_point = Point(closest_tree["center"].x + offset_x, closest_tree["center"].y + offset_y)

                self.log_msg(f"Selected tree center at: ({closest_tree['center'].x}, {closest_tree['center'].y})")
                self.log_msg(f"Click target: ({final_point.x}, {final_point.y})")
                return final_point

            return None

        except Exception as e:
            self.log_msg(f"Error finding tree: {e}")
            import traceback

            self.log_msg(f"Traceback: {traceback.format_exc()}")
            return None

    def is_inventory_full(self) -> bool:
        """
        Check if inventory is full by looking for the "Your inventory is full" message
        in black game text
        """
        try:
            # Check for the inventory full message in game text
            if self.get_game_message("Your inventory is too full"):
                self.log_msg("Inventory full message found!")
                return True

            # Also check if all inventory slots are filled as backup
            inventory = self.win.inventory
            if inventory and inventory.is_full():
                self.log_msg("All inventory slots are filled!")
                return True

            return False

        except Exception as e:
            self.log_msg(f"Error checking inventory: {e}")
            return False

    def get_chat_text(self) -> str | None:
        """
        Get text from the chat area using OCR
        """
        try:
            # Take screenshot of chat area
            chat_area = self.win.chat_area.screenshot()

            if chat_area is None:
                return None

            # Convert to grayscale
            gray = cv2.cvtColor(chat_area, cv2.COLOR_BGR2GRAY)

            # Threshold to get black text
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

            # Use OCR to get text
            text = pytesseract.image_to_string(thresh)

            return text

        except Exception as e:
            self.log_msg(f"Error getting chat text: {e}")
            return None

    def get_empty_inventory_slots(self) -> list:
        """
        Get list of empty inventory slots by checking slot colors.
        Returns: List of empty slot indices
        """
        empty_slots = []

        for i, slot in enumerate(self.win.inventory_slots):
            # Take small screenshot of slot
            slot_img = slot.screenshot()

            # Check if slot has the inventory background color
            if self.is_slot_empty(slot_img):
                empty_slots.append(i)

        return empty_slots

    def is_slot_empty(self, slot_img) -> bool:
        """
        Check if an inventory slot is empty by looking for the background color.
        Args:
            slot_img: Screenshot of the inventory slot
        Returns: True if slot is empty, False otherwise
        """
        if slot_img is None:
            return False

        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(slot_img, cv2.COLOR_BGR2HSV)

            # Define inventory background color range in HSV
            lower = np.array([0, 0, 20])  # Dark grey
            upper = np.array([180, 30, 80])

            # Create mask for background color
            mask = cv2.inRange(hsv, lower, upper)

            # Calculate percentage of background color
            total_pixels = slot_img.shape[0] * slot_img.shape[1]
            if total_pixels == 0:
                return False

            background_pixels = cv2.countNonZero(mask)
            background_percentage = (background_pixels / total_pixels) * 100

            return background_percentage > 90  # Slot is empty if >90% matches background

        except Exception as e:
            self.log_msg(f"Error checking slot: {e}")
            return False

    def is_chopping(self) -> bool:
        """
        Check if the player is currently chopping by looking for the woodcutting animation.
        Returns: True if chopping, False otherwise
        """
        return self.is_player_doing_action("Woodcutting")

    def wait_for_chopping_to_start(self, timeout: int = 10) -> bool:
        """
        Wait for the chopping animation to start.
        Args:
            timeout: Maximum time to wait in seconds
        Returns: True if chopping started, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_chopping():
                return True
            time.sleep(0.1)
        return False

    def take_break(self):
        """
        Takes a short break between actions.
        """
        if not self.take_breaks:
            return

        if rd.random_chance(0.1):  # 10% chance to take break
            break_time = rd.random_int(1, 5)
            self.log_msg(f"Taking a short break ({break_time}s)")
            time.sleep(break_time)

    def take_debug_screenshot(self, reason: str):
        """
        Takes a screenshot and saves it with timestamp and reason
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"debug_{reason}_{timestamp}.png"

            # Save screenshot of game view
            screenshot = self.win.game_view.screenshot()
            if screenshot is not None:
                import cv2

                cv2.imwrite(filename, screenshot)
                self.log_msg(f"Debug screenshot saved: {filename}")
        except Exception as e:
            self.log_msg(f"Error taking debug screenshot: {str(e)}")

    def chatbox_text(self, contains: str = None) -> Union[bool, str]:
        """
        Examines the chatbox for text. Currently only captures player chat text.
        Args:
            contains: The text to search for (single word or phrase). Case sensitive. If left blank,
                      returns all text in the chatbox.
        Returns:
            True if exact string is found, False otherwise.
            If args are left blank, returns the text in the chatbox.
        """
        if contains is None:
            return ocr.extract_text(self.win.chat, ocr.PLAIN_12, clr.BLUE)
        if ocr.find_text(contains, self.win.chat, ocr.PLAIN_12, clr.BLUE):
            return True
