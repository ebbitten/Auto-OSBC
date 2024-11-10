"""
A bot that completes agility courses in OSRS.
"""
import time
from model.bot import BotStatus
import utilities.color as clr
import utilities.random_util as rd
from utilities.geometry import Point, Rectangle
from model.osrs.osrs_bot import OSRSBot
import utilities.imagesearch as imsearch
from utilities.window import Window
from utilities.options_builder import OptionsBuilder
import cv2

class AgilityBot(OSRSBot):
    def __init__(self):
        bot_title = "Agility Bot"
        description = "Completes agility courses automatically."
        super().__init__(bot_title=bot_title, description=description)
        
        self.obstacle_color = clr.GREEN
        self.mark_color = clr.RED  # Color for mark of grace
        self.stuck_counter = 0
        self.last_position = None
        self.no_obstacle_count = 0
        
    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_dropdown_option("course", "Agility Course", ["Gnome", "Draynor", "Al Kharid", "Varrock", "Canifis"])
        self.options_builder.add_slider_option("min_breaks", "Minimum break time (seconds)", 1, 30)
        self.options_builder.add_slider_option("max_breaks", "Maximum break time (seconds)", 31, 120)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks between laps", ["Yes"])

    def save_options(self, options: dict):
        """
        Save the options from the GUI
        """
        self.options = options
        self.course = options["course"]
        self.min_breaks = options["min_breaks"] 
        self.max_breaks = options["max_breaks"]
        self.take_breaks = options["take_breaks"]
        self.log_msg(f"Running {self.course} agility course")
        self.options_set = True

    def cast_camelot_teleport(self):
        """
        Casts Camelot teleport spell
        """
        self.log_msg("Casting Camelot Teleport...")
        # Open spellbook if not already open
        self.mouse.move_to(self.win.cp_tabs[6].random_point())
        self.mouse.click()
        time.sleep(1)
        
        # Use exact coordinates for Camelot teleport
        teleport_point = Point(1751, 870)
        self.log_msg(f"Clicking Camelot teleport at: {teleport_point}")
        self.mouse.move_to(teleport_point)
        self.mouse.click()
        
        time.sleep(4)  # Wait for teleport animation
        self.stuck_counter = 0
        self.no_obstacle_count = 0

    def is_character_moving(self):
        """
        Checks if the character is currently moving by comparing screenshots
        Returns: True if character is moving, False otherwise
        """
        # Take first screenshot
        screenshot1 = self.win.game_view.screenshot()
        time.sleep(0.3)  # Wait briefly
        # Take second screenshot
        screenshot2 = self.win.game_view.screenshot()
        
        # Compare the two screenshots
        diff = cv2.absdiff(screenshot1, screenshot2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Calculate total area of changes
        total_change = sum(cv2.contourArea(c) for c in contours)
        self.log_msg(f"Movement detection - change area: {total_change}")
        
        return total_change > 1000  # Adjust threshold as needed

    def wait_for_movement_to_stop(self, timeout=10):
        """
        Waits for character movement to stop
        Args:
            timeout: Maximum time to wait in seconds
        """
        start_time = time.time()
        consecutive_still = 0
        
        while time.time() - start_time < timeout:
            if not self.is_character_moving():
                consecutive_still += 1
                if consecutive_still >= 2:  # Need 2 consecutive still checks
                    self.log_msg("Character stopped moving")
                    return True
            else:
                consecutive_still = 0
            time.sleep(0.5)
        
        self.log_msg("Movement wait timed out")
        return False

    def is_at_course_end(self):
        """
        Checks if we're at the end of the course by looking for specific landmarks
        Returns: True if at course end, False otherwise
        """
        # Take screenshot of game view
        game_view = self.win.game_view.screenshot()
        
        # Look for red carpet (specific to course end)
        red_mask = clr.isolate_colors(game_view, [clr.RED])
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Calculate total red area (carpet)
        total_red_area = sum(cv2.contourArea(c) for c in contours)
        self.log_msg(f"Course end detection - red area: {total_red_area}")
        
        # Look for dark interior area (church)
        gray = cv2.cvtColor(game_view, cv2.COLOR_BGR2GRAY)
        _, dark_mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        dark_contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_dark_area = sum(cv2.contourArea(c) for c in dark_contours)
        self.log_msg(f"Course end detection - dark area: {total_dark_area}")
        
        # Save debug images
        cv2.imwrite("debug_end_red.png", red_mask)
        cv2.imwrite("debug_end_dark.png", dark_mask)
        
        # Check for course end conditions:
        # 1. Large red area (carpet)
        # 2. Large dark area (church interior)
        # 3. No green obstacles
        if total_red_area > 2000 and total_dark_area > 10000:
            green_mask = clr.isolate_colors(game_view, [self.obstacle_color])
            green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not any(cv2.contourArea(c) > 100 for c in green_contours):
                self.log_msg("Detected course end (red carpet, church interior, no obstacles)")
                return True
            else:
                self.log_msg("Found red carpet and church but also found obstacles")
        
        return False

    def find_mark_of_grace(self):
        """
        Finds a mark of grace on screen
        Returns: Rectangle containing the mark, or None if not found
        """
        self.log_msg("Searching for mark of grace...")
        game_view = self.win.game_view.screenshot()
        
        red_mask = clr.isolate_colors(game_view, [self.mark_color])
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            self.log_msg(f"Found {len(contours)} red objects")
            
            # Filter and sort contours by area
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w)/h
                self.log_msg(f"Red object - Area: {area}, Size: {w}x{h}, Aspect ratio: {aspect_ratio:.2f}")
                
                # More lenient size range for marks (adjusted based on logs)
                if 25 < area < 2000 and 0.5 < aspect_ratio < 2.0:  # Increased upper limit, added aspect ratio check
                    valid_contours.append((area, contour))
                    self.log_msg(f"Valid mark of grace candidate found with area: {area}")
            
            if valid_contours:
                # Sort by area and get the most likely mark
                valid_contours.sort(key=lambda x: x[0])  # Sort by area
                area, mark_contour = valid_contours[0]  # Get smallest valid contour
                
                x, y, w, h = cv2.boundingRect(mark_contour)
                
                # Translate coordinates relative to game window
                game_view_rect = self.win.game_view
                abs_x = game_view_rect.left + x
                abs_y = game_view_rect.top + y
                
                self.log_msg(f"Found mark of grace at: ({abs_x}, {abs_y}) with size: {w}x{h}")
                return Rectangle(abs_x, abs_y, w, h)
            else:
                self.log_msg("No contours passed the size/shape filters")
            
        self.log_msg("No valid marks of grace found")
        return None

    def main_loop(self):
        """
        Main bot loop. 
        """
        self.log_msg("Starting Agility Bot...")
        self.setup_camera()
        last_obstacle_pos = None
        fails = 0
        
        while self.status == BotStatus.RUNNING:
            try:
                # Check if we're at course end
                if self.is_at_course_end():
                    self.log_msg("Reached end of course, teleporting...")
                    time.sleep(1)  # Wait a moment to ensure we're fully stopped
                    self.cast_camelot_teleport()
                    continue
                
                # First check for mark of grace
                mark = self.find_mark_of_grace()
                if mark:
                    self.log_msg("Found mark of grace - collecting...")
                    self.mouse.move_to(mark.random_point(), mouseSpeed="medium")
                    self.mouse.click()
                    self.wait_for_movement_to_stop()
                
                # Then find next obstacle
                obstacle = self.find_next_obstacle()
                
                if obstacle:
                    self.log_msg("Found obstacle...")
                    self.no_obstacle_count = 0
                    
                    # Check if we're stuck on same obstacle
                    current_pos = (obstacle.left, obstacle.top)
                    if last_obstacle_pos == current_pos:
                        self.stuck_counter += 1
                        self.log_msg(f"Same obstacle detected {self.stuck_counter} times")
                    else:
                        self.stuck_counter = 0
                    last_obstacle_pos = current_pos
                    
                    # If stuck for too long, teleport out
                    if self.stuck_counter > 5:
                        self.log_msg("Stuck on same obstacle for too long!")
                        self.cast_camelot_teleport()
                        continue
                    
                    # Click the obstacle with some randomization
                    click_point = obstacle.random_point()
                    self.log_msg(f"Clicking obstacle at: {click_point}")
                    self.mouse.move_to(click_point, mouseSpeed="medium")
                    self.mouse.click()
                    
                    # Wait for movement to complete
                    self.wait_for_movement_to_stop()
                    
                else:
                    self.log_msg(f"No obstacle found (count: {self.no_obstacle_count})")
                    self.no_obstacle_count += 1
                    if self.no_obstacle_count > 10:
                        self.log_msg("No obstacles found for too long!")
                        self.cast_camelot_teleport()
                    time.sleep(1.5)

                self.update_progress(0.5)
                
            except Exception as e:
                self.log_msg(f"Error in main loop: {str(e)}")
                fails += 1
                if fails > 5:
                    self.log_msg("Too many errors, attempting to teleport...")
                    self.cast_camelot_teleport()
                    fails = 0
                time.sleep(1.5)

    def find_next_obstacle(self):
        """
        Finds the next green highlighted obstacle on screen
        Returns: Rectangle containing the obstacle, or None if not found
        """
        self.log_msg("Searching for next obstacle...")
        game_view = self.win.game_view.screenshot()
        
        # Isolate green color
        green_mask = clr.isolate_colors(game_view, [self.obstacle_color])
        cv2.imwrite("debug_obstacle_mask.png", green_mask)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            self.log_msg(f"Found {len(contours)} green objects")
            
            # Filter contours by area
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                self.log_msg(f"Found green object with area: {area}")
                # Adjusted area range to include larger obstacles
                if 100 < area < 20000:  # Increased upper limit
                    valid_contours.append(contour)
                    self.log_msg(f"Valid green object found with area: {area}")
            
            if not valid_contours:
                self.log_msg("No valid obstacles found (all objects were wrong size)")
                return None
                
            # Get the largest valid contour
            largest_contour = max(valid_contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Additional shape filtering (more lenient)
            aspect_ratio = float(w)/h
            self.log_msg(f"Selected obstacle - Area: {area}, Size: {w}x{h}, Aspect ratio: {aspect_ratio:.2f}")
            
            # More lenient aspect ratio filtering
            if aspect_ratio < 0.1 or aspect_ratio > 10:
                self.log_msg("Obstacle rejected - bad aspect ratio")
                return None
                
            # Add some padding
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = w + padding * 2
            h = h + padding * 2
            
            # Translate coordinates relative to game window
            game_view_rect = self.win.game_view
            abs_x = game_view_rect.left + x
            abs_y = game_view_rect.top + y
            
            self.log_msg(f"Found valid obstacle at: ({abs_x}, {abs_y}) with size: {w}x{h}")
            return Rectangle(abs_x, abs_y, w, h)
            
        self.log_msg("No green objects found")
        return None

    def is_lap_complete(self):
        """
        Checks if a lap was completed by looking for XP drop
        Returns: True if lap complete, False otherwise
        """
        # Look for agility XP drop in the chat
        return bool(self.mouseover_text(contains="You completed a lap", color=clr.BLUE))

    def setup_camera(self):
        """
        Sets up the camera angle for optimal obstacle detection
        """
        self.log_msg("Setting up camera...")
        # Set compass North
        self.set_compass_north()
        # Set camera to highest angle
        self.move_camera(vertical=90) 
    