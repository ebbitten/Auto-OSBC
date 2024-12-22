import time

import utilities.api.animation_ids as animation_ids
import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.imagesearch as imsearch
from model.osrs.osrs_bot import OSRSBot
from utilities.game_launcher import Launchable
from utilities.geometry import Point


class FishingBot(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Fishing Bot"
        description = "Catches fish at fishing spots. Will search for fishing spot icons."
        super().__init__(bot_title=bot_title, description=description)
        # Set default values
        self.running_time = 360  # Default 360 minutes
        self.take_breaks = False
        self.fish_type = "Shark"  # Changed default back to Shark
        self.fishing_spot_img = imsearch.BOT_IMAGES.joinpath("fishing_spots/shark.png")  # Set default image

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 1000)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_dropdown_option("fish_type", "Fish type", ["Karam", "Shark", "Lobster"])  # Added Karam to options

    def save_options(self, options: dict):
        """
        For each option in the dictionary, save the value as a property of the bot.
        """
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "fish_type":
                self.fish_type = options[option]
                # Set the appropriate image based on fish type
                img_name = f"{self.fish_type.lower()}.png"
                self.fishing_spot_img = imsearch.BOT_IMAGES.joinpath(f"fishing_spots/{img_name}")
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks")
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
            self.log_msg(f"Error in main loop: {str(e)}")
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
            self.log_msg(f"Error checking thread status: {str(e)}")
            return True

    def find_fishing_spot(self) -> Point | None:
        """
        Find fishing spot using image recognition
        Returns Point if found, None otherwise
        Prioritizes spots closer to the center of the screen
        """
        # Get the center point of the game view
        center = self.win.game_view.get_center()

        # Find first fishing spot
        spot = imsearch.search_img_in_rect(self.fishing_spot_img, self.win.game_view, confidence=0.7)

        if not spot:
            return None

        # Calculate distance from center
        spot_center = spot.get_center()
        distance = (spot_center.x - center.x) ** 2 + (spot_center.y - center.y) ** 2

        # If it's close enough to center (within 100 pixels), use it
        if distance < 10000:  # 100 pixels squared
            return spot.random_point()

        # Otherwise, look for a potentially closer spot
        second_spot = imsearch.search_img_in_rect(self.fishing_spot_img, self.win.game_view, confidence=0.7)

        if second_spot:
            second_center = second_spot.get_center()
            second_distance = (second_center.x - center.x) ** 2 + (second_center.y - center.y) ** 2
            if second_distance < distance:
                return second_spot.random_point()

        # If no better spot found, use the first one
        return spot.random_point()

    def is_logged_in(self) -> bool:
        """
        Check if we're still logged into the game by looking for typical game UI elements
        """
        try:
            # You can customize these checks based on your UI setup
            # For example, look for the minimap, inventory, or other persistent UI elements
            inventory = imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("inventory_tab.png"), self.win.control_panel, confidence=0.7)
            return inventory is not None
        except Exception as e:
            self.log_msg(f"Error checking login status: {str(e)}")
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
            self.log_msg(f"Error taking debug screenshot: {str(e)}")
