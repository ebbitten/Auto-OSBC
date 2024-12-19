import time
import utilities.color as clr
import utilities.random_util as rd
from utilities.geometry import Point
from model.osrs.osrs_bot import OSRSBot
import utilities.imagesearch as imsearch
import utilities.game_launcher as launcher
import cv2
import numpy as np

class OSRSWoodcutter(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Woodcutter"
        description = "Chops trees and banks logs using Banker's Note (for now). Position near trees and tag them."
        super().__init__(bot_title=bot_title, description=description)
        
        # Initialize default values
        self.running_time = 60  # Default of 60 minutes
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
        self.options_builder.add_dropdown_option(
            "tree_type", 
            "Tree type", 
            ["Normal", "Oak", "Willow", "Maple", "Yew", "Magic", "Mahogany"]
        )

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
        Main bot loop.
        """
        # Start time tracking
        start_time = time.time()
        end_time = self.running_time * 60
        consecutive_failures = 0
        
        self.log_msg("Starting woodcutting bot...")
        
        # Make sure inventory tab is open at start
        self.log_msg("Opening inventory tab...")
        self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()
        time.sleep(0.5)
        
        # Main loop
        first_loop = True
        while time.time() - start_time < end_time:
            # Check if thread should stop
            if self.should_stop():
                self.log_msg("Stopping bot...")
                break

            try:
                # Take breaks between actions
                self.take_break()
                
                # Check if inventory is full
                if self.is_inventory_full():
                    self.log_msg("Inventory full, using banker's note...")
                    if not self.use_bankers_note():
                        self.log_msg("Failed to use banker's note!")
                        self.take_debug_screenshot("banking_failure")
                        consecutive_failures += 1
                        if consecutive_failures > 3:
                            self.log_msg("Too many banking failures, stopping bot...")
                            break
                        continue
                    consecutive_failures = 0
                    continue

                # Find and click tree
                tree = self.find_tagged_tree()
                if not tree:
                    self.failed_searches += 1
                    if self.failed_searches % 10 == 0:
                        self.log_msg("Searching for trees...")
                        self.take_debug_screenshot("no_trees")
                    if self.failed_searches > 60:
                        self.log_msg("No tagged trees found for too long, stopping bot...")
                        break
                    time.sleep(1)
                    continue
                self.failed_searches = 0  # Reset counter when tree found

                # Click the tree
                self.mouse.move_to(tree)
                if not self.mouseover_text(contains="Chop", color=clr.OFF_WHITE):
                    self.log_msg("No chop option found, retrying...")
                    self.take_debug_screenshot("no_chop_option")
                    continue
                self.mouse.click()
                
                # Wait for chopping to start
                self.log_msg("Checking if chopping started...")
                if not self.wait_for_chopping_to_start():
                    self.log_msg("Failed to start chopping!")
                    self.take_debug_screenshot("chop_start_failure")
                    consecutive_failures += 1
                    if consecutive_failures > 3:
                        self.log_msg("Failed to start chopping too many times, stopping bot...")
                        break
                    continue
                consecutive_failures = 0

                # While chopping, wait and check status
                while self.is_chopping():
                    if self.should_stop():
                        break
                    time.sleep(0.5)
                
                self.logs_chopped += 1
                self.log_msg(f"Logs chopped: {self.logs_chopped}")

                if first_loop:
                    # Wait a bit longer on first click to ensure woodcutting plugin activates
                    time.sleep(3)
                    first_loop = False

            except Exception as e:
                self.log_msg(f"Error in main loop: {e}")
                self.take_debug_screenshot("error")
                consecutive_failures += 1
                if consecutive_failures > 3:
                    self.log_msg("Too many consecutive errors, stopping bot...")
                    break
                time.sleep(1)

            # Update progress
            self.update_progress((time.time() - start_time) / end_time)

        self.log_msg(f"Finished. Total logs chopped: {self.logs_chopped}")
        self.stop()

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
        self.log_msg("Searching for tagged tree...")
        
        # Take screenshot of game view
        game_view = self.win.game_view.screenshot()
        
        if game_view is None:
            self.log_msg("Failed to get game view screenshot")
            return None
        
        try:
            # Convert to HSV for better pink detection
            hsv = cv2.cvtColor(game_view, cv2.COLOR_BGR2HSV)
            
            # Define pink color range (adjust these values based on the screenshot)
            lower_pink = np.array([150, 50, 200])  # More saturated pink
            upper_pink = np.array([170, 255, 255])
            
            # Create mask for pink color
            pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)
            
            # Dilate the mask to connect nearby pink pixels (for outlines)
            kernel = np.ones((3,3), np.uint8)
            dilated_mask = cv2.dilate(pink_mask, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                self.log_msg("No tagged trees found")
                return None
            
            # Get center point of game view for distance calculation
            center = self.win.game_view.get_center()
            
            # Find closest valid tree contour
            closest_tree = None
            min_distance = float('inf')
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter out very small contours (noise) and very large contours
                if 100 < area < 10000:  # Adjust these thresholds as needed
                    # Get center of contour
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        # Calculate distance from center
                        distance = ((cx - center.x) ** 2 + (cy - center.y) ** 2) ** 0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_tree = Point(cx, cy)
            
            if closest_tree:
                # Add some random offset
                offset_x = rd.random_int(-3, 3)
                offset_y = rd.random_int(-3, 3)
                
                self.log_msg(f"Found tree at: ({closest_tree.x}, {closest_tree.y})")
                return Point(closest_tree.x + offset_x, closest_tree.y + offset_y)
            
            return None
            
        except Exception as e:
            self.log_msg(f"Error finding tree: {e}")
            return None

    def is_inventory_full(self) -> bool:
        """
        Check if inventory is full by checking if any slots before the banker's note are empty.
        Returns: True if full, False otherwise
        """
        try:
            # Make sure inventory tab is open
            self.log_msg("Checking if inventory is full...")
            inventory = imsearch.search_img_in_rect(
                imsearch.BOT_IMAGES.joinpath("inventory_tab.png"),
                self.win.control_panel,
                confidence=0.7
            )
            
            if not inventory:
                self.log_msg("Opening inventory tab...")
                self.mouse.move_to(self.win.cp_tabs[3].random_point())
                self.mouse.click()
                time.sleep(0.5)
            
            # Check all slots except the last one (banker's note)
            for slot in self.win.inventory_slots[:-1]:
                slot_img = slot.screenshot()
                if slot_img is None:
                    continue
                if self.is_slot_empty(slot_img):
                    self.log_msg("Found empty slot - inventory not full")
                    return False
            
            self.log_msg("All slots before banker's note are full")
            return True
            
        except Exception as e:
            self.log_msg(f"Error checking inventory: {e}")
            return False

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

    def use_bankers_note(self) -> bool:
        """
        Use banker's note (assumed to be in last inventory slot) to bank logs.
        Returns: True if successful, False otherwise
        """
        try:
            self.log_msg("Attempting to use banker's note...")
            
            # Click banker's note in last slot
            last_slot = self.win.inventory_slots[-1]
            self.mouse.move_to(last_slot.random_point())
            self.mouse.click()
            time.sleep(0.5)
            
            # Find and click first log stack
            for slot in self.win.inventory_slots[:-1]:  # Skip last slot (banker's note)
                slot_img = slot.screenshot()
                if not self.is_slot_empty(slot_img):
                    self.mouse.move_to(slot.random_point())
                    self.mouse.click()
                    break
            
            # Wait for noting animation
            time.sleep(1)
            
            # Verify inventory is now empty except for note
            if self.is_inventory_full():
                self.log_msg("Failed to note logs - inventory still full")
                return False
            
            self.log_msg("Successfully noted logs")
            return True
            
        except Exception as e:
            self.log_msg(f"Error using banker's note: {e}")
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