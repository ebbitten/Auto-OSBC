import time
import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.game_launcher as launcher
from utilities.geometry import Point
from utilities.game_launcher import Launchable
from model.osrs.osrs_bot import OSRSBot
import utilities.imagesearch as imsearch
import utilities.api.animation_ids as animation_ids

class FishingBot(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Fishing Bot"
        description = "Catches fish at fishing spots. Will search for fishing spot icons."
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
        self.take_breaks = False
        self.fishing_spot_img = imsearch.BOT_IMAGES.joinpath("fishing_spots/lobster.png")

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, save the value as a property of the bot.
        """
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.options_set = True

    def main_loop(self):
        """
        Main fishing loop:
        1. Find fishing spot
        2. Click it
        3. Wait for character to reach spot (5s timeout)
        4. Wait for fishing animation
        5. Keep fishing until animation stops (requires 2 consecutive non-fishing checks)
        """
        if not self.fishing_spot_img.exists():
            print(f"ERROR: Could not find fishing spot image at: {self.fishing_spot_img}")
            return
            
        self.log_msg("Starting fishing bot...")
        
        # Main loop timing
        start_time = time.time()
        end_time = self.running_time * 60
        fish_caught = 0
        
        while time.time() - start_time < end_time:
            # Try to find fishing spot
            spot = self.find_fishing_spot()
            if not spot:
                self.log_msg("No fishing spot found, searching...")
                time.sleep(1)
                continue
                
            # Click the spot
            self.log_msg("Found spot, clicking...")
            self.mouse.move_to(spot)
            self.mouse.click()
            
            # Wait for character to reach the spot (up to 5 seconds)
            self.log_msg("Walking to fishing spot...")
            reach_timeout = time.time() + 5
            while time.time() < reach_timeout:
                if self.is_player_doing_action("Fishing"):
                    self.log_msg("Started fishing!")
                    break
                time.sleep(0.5)
            else:  # If we didn't break from the loop (didn't start fishing)
                self.log_msg("Failed to reach fishing spot, trying again...")
                continue
            
            # Keep checking if we're still fishing
            fishing_timeout = time.time() + 30  # Maximum 30 seconds per spot
            not_fishing_count = 0  # Counter for consecutive non-fishing checks
            
            while time.time() < fishing_timeout:
                if self.is_player_doing_action("Fishing"):
                    not_fishing_count = 0  # Reset counter when we detect fishing
                    fish_caught += 1
                    self.log_msg(f"Still fishing... Fish caught: {fish_caught}")
                    time.sleep(2)
                else:
                    not_fishing_count += 1
                    if not_fishing_count >= 2:  # Only stop if we get 2 consecutive non-fishing checks
                        self.log_msg("No longer fishing, looking for new spot...")
                        break
                    time.sleep(1)  # Quick check for second verification
                    
            # Update progress
            self.update_progress((time.time() - start_time) / end_time)

    def find_fishing_spot(self) -> Point | None:
        """
        Find fishing spot using image recognition
        Returns Point if found, None otherwise
        """
        fishing_spot = imsearch.search_img_in_rect(
            self.fishing_spot_img, 
            self.win.game_view,
            confidence=0.7
        )
        
        if fishing_spot:
            return fishing_spot.random_point()
        return None