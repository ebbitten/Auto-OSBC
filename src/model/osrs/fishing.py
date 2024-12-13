import os
import time

import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import Point


class FishingBot(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Fishing Bot"
        description = "Catches fish at fishing spots. Will search for fishing spot icons."
        super().__init__(bot_title=bot_title, description=description)
        # Set default values
        self.running_time = 360  # Default 360 minutes
        self.take_breaks = False
        self.fish_type = "Karam"  # Changed default to Karam
        self.fishing_spot_img = imsearch.BOT_IMAGES.joinpath("fishing_spots/karam.png")  # Set default image
        self.debug_mode = False  # Add debug mode flag

        # Create debug folder if it doesn't exist
        self.debug_folder = os.path.join(os.getcwd(), "fishing_debug")
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 1000)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [""])
        self.options_builder.add_checkbox_option("debug_mode", "Enable debug mode?", ["Enable Debug"])
        self.options_builder.add_dropdown_option("fish_type", "Fish type", ["Karam", "Angler", "Shark", "Lobster"])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, save the value as a property of the bot.
        """
        self.log_msg(f"Raw options received: {options}")  # Debug line
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = bool(options[option])
            elif option == "debug_mode":
                self.log_msg(f"Debug mode option value: {options[option]}")
                self.debug_mode = "Enable Debug" in options[option]
                self.log_msg(f"Debug mode set to: {self.debug_mode}")
            elif option == "fish_type":
                self.fish_type = options[option]
                img_name = f"{self.fish_type.lower()}.png"
                self.fishing_spot_img = imsearch.BOT_IMAGES.joinpath(f"fishing_spots/{img_name}")
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks")
        self.log_msg(f"Debug mode is {'ENABLED' if self.debug_mode else 'DISABLED'}")
        self.log_msg(f"Fish type: {self.fish_type}")
        self.options_set = True

    def main_loop(self):
        """
        Main fishing loop with improved spot searching and timeout handling
        """
        start_time = time.time()
        fish_caught = 0
        last_interaction_time = time.time()
        consecutive_failures = 0
        last_activity_time = time.time()  # Track when we last did something

        try:
            if not self.fishing_spot_img.exists():
                print(f"ERROR: Could not find fishing spot image at: {self.fishing_spot_img}")
                return

            self.log_msg("Starting fishing bot...")

            # Main loop timing
            end_time = self.running_time * 60
            failed_spot_searches = 0

            while time.time() - start_time < end_time:
                # Check if thread should stop
                if self.should_stop():
                    self.log_msg("Stopping bot - received stop signal")
                    return

                # Try to find fishing spot
                self.log_msg("Searching for fishing spot...")
                spot = self.find_fishing_spot()
                if not spot:
                    failed_spot_searches += 1
                    consecutive_failures += 1
                    self.log_msg(f"No fishing spot found (attempt #{failed_spot_searches})")

                    # Take screenshot after 5 consecutive failures
                    if consecutive_failures >= 5:
                        self.take_debug_screenshot("fishing_failure")
                        consecutive_failures = 0

                    if failed_spot_searches >= 10:
                        self.log_msg("Failed to find spots for too long, resetting search...")
                        failed_spot_searches = 0
                        time.sleep(2)
                    time.sleep(1)
                    continue

                # Reset failure counters on success
                consecutive_failures = 0
                failed_spot_searches = 0

                # Click the spot
                self.log_msg("Found spot, clicking...")
                self.mouse.move_to(spot)
                self.mouse.click()
                last_activity_time = time.time()  # Reset timer when we click#

                # Initial wait for character to start moving
                time.sleep(2)

                # Wait for character to reach the spot and start fishing (up to 8 seconds)
                self.log_msg("Walking to fishing spot...")
                reach_timeout = time.time() + 8
                started_fishing = False
                seconds_waited = 0
                while time.time() < reach_timeout:
                    if self.is_player_doing_action("Fishing"):
                        self.log_msg("Started fishing!")
                        started_fishing = True
                        break
                    time.sleep(0.5)
                    seconds_waited += 0.5
                    if seconds_waited % 2 == 0:
                        self.log_msg(f"Still walking... ({int(seconds_waited)} seconds)")

                if not started_fishing:
                    self.log_msg("Failed to reach fishing spot in time, trying again...")
                    continue

                # Keep checking if we're still fishing
                not_fishing_count = 0
                last_action_check = time.time()

                while True:
                    if self.should_stop():
                        self.log_msg("Stopping bot - received stop signal")
                        return

                    # Force a new spot search every ~4 minutes to prevent logout
                    if time.time() - last_activity_time > 240:  # 240 seconds = 4 minutes
                        self.log_msg("Been a while, searching for new spot to prevent logout...")
                        break  # Break inner loop to find new spot

                    if time.time() - last_action_check >= 1.5:
                        if self.is_player_doing_action("Fishing"):
                            last_interaction_time = time.time()
                            not_fishing_count = 0
                            fish_caught += 1
                            self.log_msg(f"Still fishing... Fish caught: {fish_caught}")
                        else:
                            not_fishing_count += 1
                            self.log_msg(f"Not fishing check #{not_fishing_count}")
                            if not_fishing_count >= 2:
                                self.log_msg("No longer fishing, looking for new spot...")
                                break
                        last_action_check = time.time()
                    time.sleep(0.1)

                # Small delay before looking for new spot
                time.sleep(0.5)

                # Update progress
                self.update_progress((time.time() - start_time) / end_time)

        except Exception as e:
            self.log_msg(f"Error in main loop: {e!s}")
            self.log_msg("Stack trace:", str(e.__traceback__))
        finally:
            elapsed_time = (time.time() - start_time) / 60
            self.log_msg(f"Bot stopped after running for {elapsed_time:.1f} minutes")
            self.log_msg(f"Total fish caught: {fish_caught}")
            self.stop()

    def should_stop(self):
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
            self.log_msg(f"Error checking thread status: {e!s}")
            return True

    def find_fishing_spot(self) -> Point | None:
        """
        Find fishing spot using image recognition
        Returns Point if found, None otherwise
        Prioritizes spots closer to the center of the screen
        """
        try:
            center = self.win.game_view.get_center()

            # Set confidence level based on fish type
            confidence = 0.7
            if self.fish_type == "Angler":
                confidence = 0.85
            elif self.fish_type == "Karam":
                confidence = 0.75

            self.log_msg("Weve reached the check for debug mode")
            self.log_msg(f"Debug mode is {self.debug_mode}")

            # Add more debug logging
            self.log_msg(f"Debug mode status in find_fishing_spot: {self.debug_mode}")

            if self.debug_mode:
                try:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")

                    # Save the template image we're looking for
                    template_path = os.path.join(self.debug_folder, f"debug_template_{timestamp}.png")
                    import shutil

                    shutil.copy(str(self.fishing_spot_img), template_path)
                    self.log_msg(f"Saved template image to: {template_path}")

                    # Take and save screenshot of current game view
                    screen_path = os.path.join(self.debug_folder, f"debug_screen_{timestamp}.png")
                    screen = self.win.game_view.screenshot()
                    screen.save(screen_path)
                    self.log_msg(f"Saved screen capture to: {screen_path}")

                    # Convert to CV2 format for drawing
                    import cv2
                    import numpy as np

                    debug_img_cv = np.array(screen)

                    # Search for the spot
                    spot = imsearch.search_img_in_rect(self.fishing_spot_img, self.win.game_view, confidence=confidence)

                    # Draw results (or lack thereof) on debug image
                    if spot:
                        cv2.rectangle(
                            debug_img_cv,
                            (spot.left, spot.top),
                            (spot.right, spot.bottom),
                            (0, 255, 0),  # Green for found
                            2,
                        )
                        self.log_msg(f"Spot detected at: ({spot.left}, {spot.top}) to ({spot.right}, {spot.bottom})")
                    else:
                        # Draw red X in center if nothing found
                        h, w = debug_img_cv.shape[:2]
                        cv2.line(debug_img_cv, (w // 2 - 20, h // 2 - 20), (w // 2 + 20, h // 2 + 20), (0, 0, 255), 2)
                        cv2.line(debug_img_cv, (w // 2 - 20, h // 2 + 20), (w // 2 + 20, h // 2 - 20), (0, 0, 255), 2)
                        self.log_msg(f"No spot found with confidence {confidence}")

                    # Save the annotated image
                    detection_path = os.path.join(self.debug_folder, f"debug_detection_{timestamp}.png")
                    cv2.imwrite(detection_path, cv2.cvtColor(debug_img_cv, cv2.COLOR_RGB2BGR))
                    self.log_msg(f"Saved detection visualization to: {detection_path}")

                except Exception as e:
                    self.log_msg(f"Error in debug image saving: {e!s}")
            else:
                # Normal search without debug
                spot = imsearch.search_img_in_rect(self.fishing_spot_img, self.win.game_view, confidence=confidence)

            if not spot:
                return None

            spot_center = spot.get_center()
            distance = (spot_center.x - center.x) ** 2 + (spot_center.y - center.y) ** 2

            if distance < 10000:
                return spot.random_point()

            second_spot = imsearch.search_img_in_rect(self.fishing_spot_img, self.win.game_view, confidence=confidence)

            if second_spot:
                second_center = second_spot.get_center()
                second_distance = (second_center.x - center.x) ** 2 + (second_center.y - center.y) ** 2
                if second_distance < distance:
                    return second_spot.random_point()

            return spot.random_point()

        except Exception as e:
            self.log_msg(f"Error in find_fishing_spot: {e!s}")
            return None

    def is_logged_in(self) -> bool:
        """
        Check if we're still logged into the game by looking for typical game UI elements
        """
        try:
            # You can customize these checks based on your UI setup
            # For example, look for the minimap, inventory, or other persistent UI elements
            inventory = imsearch.search_img_in_rect(
                imsearch.BOT_IMAGES.joinpath("inventory_tab.png"), self.win.control_panel, confidence=0.7
            )
            return inventory is not None
        except Exception as e:
            self.log_msg(f"Error checking login status: {e!s}")
            return False

    def take_debug_screenshot(self, reason: str):
        """
        Takes a screenshot and saves it with timestamp and reason
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"debug_{reason}_{timestamp}.png"

            # Save screenshot of game view
            self.win.game_view.screenshot().save(filename)
            self.log_msg(f"Debug screenshot saved: {filename}")
        except Exception as e:
            self.log_msg(f"Error taking debug screenshot: {e!s}")
