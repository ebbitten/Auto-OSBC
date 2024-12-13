import time

import src.utilities.color as clr
import src.utilities.random_util as rd
from src.model.osrs.osrs_bot import OSRSBot
from src.utilities.api import item_ids as ids
from src.utilities.api.events_client import EventsAPIClient
from src.utilities.api.events_server import start_server_thread
from src.utilities.geometry import RuneLiteObject


class OSRSWoodcutter(OSRSBot):
    def __init__(self):
        bot_title = "Woodcutter"
        description = "This bot power-chops wood. Position your character near some trees, tag them, and press Play.\nTHIS SCRIPT IS AN EXAMPLE, DO NOT USE LONGTERM."
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
        self.take_breaks = False
        self.server_thread = None
        self.api_started = False

    def start_api_server(self):
        if not self.api_started:
            self.server_thread = start_server_thread()
            # Wait for the server to start
            time.sleep(2)
            self.api_started = True
            self.log_msg("EventsAPI server started.")

    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print(
                    "Developer: ensure that the option keys are correct, and that options are being unpacked correctly."
                )
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        # Start the API server if it hasn't been started yet
        if not self.api_started:
            self.start_api_server()

        # Check if the API is ready
        retry_count = 0
        while not EventsAPIClient.get_player_status():
            if retry_count >= 10:
                self.log_msg("Error: EventsAPI is not ready. Please check the RuneLite plugin and try again.")
                return
            self.log_msg(f"Waiting for EventsAPI to be ready... (Attempt {retry_count + 1}/10)")
            time.sleep(2)
            retry_count += 1

        self.log_msg("EventsAPI is ready. Starting main loop...")

        self.log_msg("Selecting inventory...")
        self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()

        self.logs = 0
        failed_searches = 0

        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=30, fancy=True)

            # 2% chance to drop logs early
            if rd.random_chance(probability=0.02):
                self.__drop_logs()

            # If inventory is full, drop logs
            if EventsAPIClient.get_is_inv_full():
                self.__drop_logs()

            # If our mouse isn't hovering over a tree, and we can't find another tree...
            if (
                not self.mouseover_text(contains="Chop", color=clr.OFF_WHITE)
                and not self.__move_mouse_to_nearest_tree()
            ):
                failed_searches += 1
                if failed_searches % 10 == 0:
                    self.log_msg("Searching for trees...")
                if failed_searches > 60:
                    # If we've been searching for a whole minute...
                    self.__logout("No tagged trees found. Logging out.")
                time.sleep(1)
                continue
            failed_searches = 0  # If code got here, a tree was found

            # Click if the mouseover text assures us we're clicking a tree
            if not self.mouseover_text(contains="Chop", color=clr.OFF_WHITE):
                continue
            self.mouse.click()
            time.sleep(0.5)

            # While the player is chopping (or moving), wait
            probability = 0.10
            last_position = EventsAPIClient.get_player_position()
            while True:
                current_position = EventsAPIClient.get_player_position()
                if current_position != last_position:
                    break
                # Every second there is a chance to move the mouse to the next tree, lessen the chance as time goes on
                if rd.random_chance(probability):
                    self.__move_mouse_to_nearest_tree(next_nearest=True)
                    probability /= 2
                time.sleep(1)

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    def __move_mouse_to_nearest_tree(self, next_nearest=False):
        """
        Locates the nearest tree and moves the mouse to it. This code is used multiple times in this script,
        so it's been abstracted into a function.
        Args:
            next_nearest: If True, will move the mouse to the second nearest tree. If False, will move the mouse to the
                          nearest tree.
        Returns:
            True if success, False otherwise.
        """
        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        if next_nearest:
            self.mouse.move_to(tree.random_point(), mouseSpeed="slow", knotsCount=2)
        else:
            self.mouse.move_to(tree.random_point())
        return True

    def __drop_logs(self):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        """
        slots = EventsAPIClient.get_inv_item_indices(ids.logs)
        self.drop(slots)
        self.logs += len(slots)
        self.log_msg(f"Logs cut: ~{self.logs}")
        time.sleep(1)

    def stop(self):
        self.log_msg("Stopping bot...")
        if self.server_thread:
            # Implement a way to stop the server gracefully
            self.log_msg("Stopping EventsAPI server...")
            # You might need to implement a stop method in your server
        super().stop()
        self.log_msg("Bot stopped.")
