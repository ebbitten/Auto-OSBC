"""NRMining - Power mining bot using the Actions + Executor pattern.

This bot demonstrates the intent-based action architecture:
1. Actions analyze game state and return intents
2. Executor performs the actual side effects
3. Bot logic is pure and testable
"""

import time
from typing import List

import utilities.color as clr
from model.actions import interaction, inventory, safety, waiting
from model.actions.executor import Executor
from model.actions.intents import ClickIntent
from model.bot import BotStatus
from model.near_reality.nr_bot import NRBot
from utilities.geometry import Rectangle, RuneLiteObject


class NRMining(NRBot):
    def __init__(self):
        title = "Mining"
        description = (
            "This bot power-mines rocks. Equip a pickaxe, place your character between some rocks and mark "
            + "(Shift + Right-Click) the ones you want to mine."
        )
        super().__init__(bot_title=title, description=description)
        self.running_time = 2
        self.logout_on_friends = False

    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 360)
        self.options_builder.add_dropdown_option("logout_on_friends", "Logout when friends are nearby?", ["Yes", "No"])

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "logout_on_friends":
                self.logout_on_friends = options[option] == "Yes"
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f'Bot will {"" if self.logout_on_friends else "not"} logout when friends are nearby.')
        self.options_set = True

    def main_loop(self):
        """Main bot loop using Actions + Executor pattern."""
        # Create executor for performing side effects
        executor = Executor(self)

        # Setup - select inventory tab
        self.log_msg("Selecting inventory...")
        inventory_tab_point = self.win.cp_tabs[3].random_point()
        setup_click = ClickIntent(
            point=(inventory_tab_point.x, inventory_tab_point.y),
            speed="medium",
        )
        executor.execute(setup_click)

        mined = 0
        failed_searches = 0

        # Main loop with timed session
        start_time = time.time()
        end_time = self.running_time * 60

        while time.time() - start_time < end_time:
            # Check safety conditions
            safety_result = safety.check_and_logout_if_unsafe(
                self,
                logout_on_friends=self.logout_on_friends,
            )
            if safety_result.safety_stopped:
                # Execute the logout intent
                executor.execute(safety_result.data["intent"])
                return

            # Check if inventory is full and drop if needed
            inv_result = inventory.manage_if_full(self)
            if inv_result.success and "intent" in inv_result.data:
                executor.execute(inv_result.data["intent"])
                time.sleep(1)
                continue

            # Find and click a rock
            interact_result = interaction.find_and_interact(
                self,
                clr.PINK,
                mouse_speed="fastest",
            )

            if interact_result.failed:
                failed_searches += 1
                if failed_searches > 5:
                    logout_result = safety.safe_logout(
                        self,
                        "Failed to find a rock to mine. Logging out.",
                    )
                    executor.execute(logout_result.data["intent"])
                    return
                time.sleep(1)
                continue

            # Execute the click intent
            failed_searches = 0
            executor.execute(interact_result.data["intent"])

            # Wait for player to finish mining
            wait_result = waiting.wait_for_idle(self)
            executor.execute(wait_result.data["intent"])

            mined += 1
            self.log_msg(f"Rocks mined: {mined}")

            # Update progress
            self.update_progress((time.time() - start_time) / end_time)

        # Session complete
        self.update_progress(1)
        finish_result = safety.safe_logout(self, "Finished.")
        executor.execute(finish_result.data["intent"])
