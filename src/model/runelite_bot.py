"""
The RuneLiteBot class contains properties and functions that are common across all RuneLite-based clients. This class
can be inherited by additional abstract classes representing all bots for a specific game (E.g., OSRSBot, etc.).

To determine Thresholds for finding contours: https://pinetools.com/threshold-image

For converting RGB to HSV:
    https://stackoverflow.com/questions/10948589/choosing-the-correct-upper-and-lower-hsv-boundaries-for-color-detection-withcv/48367205#48367205

Item ID Database:
    https://www.runelocus.com/tools/osrs-item-id-list/
"""
import time
from abc import ABCMeta
from typing import List, Union

import pyautogui as pag
from deprecated import deprecated

import utilities.color as clr
import utilities.debug as debug
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
import utilities.runelite_cv as rcv
from model.bot import Bot, BotStatus
from utilities.geometry import Point, Rectangle, RuneLiteObject
from utilities.window import Window
from utilities.machine_config import get_machine_config


class RuneLiteWindow(Window):
    current_action: Rectangle = None  # https://i.imgur.com/fKXuIyO.png
    hp_bar: Rectangle = None  # https://i.imgur.com/2lCovGV.png
    prayer_bar: Rectangle = None

    def __init__(self, window_title: str) -> None:
        """
        RuneLiteWindow is an extensions of the Window class, which allows for locating and interacting with key
        UI elements on screen.
        """
        # Get padding from machine configuration
        config = get_machine_config()
        padding_top, padding_left = config.get_window_padding()
        super().__init__(window_title, padding_top=padding_top, padding_left=padding_left)

    # Override
    def initialize(self) -> bool:
        """
        Overrirde of Window.initialize(). This function is called when the bot is started.
        """
        if not super().initialize():
            return False
        self.__locate_hp_prayer_bars()
        # Get current action coordinates from config
        config = get_machine_config()
        ca_config = config.get("ui_coordinates", "current_action", default={
            "left": 10, "top": 25, "width": 128, "height": 20
        })
        self.current_action = Rectangle(
            left=ca_config["left"] + self.game_view.left,
            top=ca_config["top"] + self.game_view.top,
            width=ca_config["width"],
            height=ca_config["height"],
        )
        return True

    def __locate_hp_prayer_bars(self) -> None:
        """
        Creates Rectangles for the HP and Prayer bars on either side of the control panel, storing it in the
        class property.
        """
        config = get_machine_config()
        
        # Get HP bar configuration
        hp_config = config.get("ui_coordinates", "hp_bar", default={
            "left": 7, "top": 42, "width": 18, "height": 250
        })
        self.hp_bar = Rectangle(
            left=self.control_panel.left + hp_config["left"],
            top=self.control_panel.top + hp_config["top"],
            width=hp_config["width"],
            height=hp_config["height"],
        )
        
        # Get prayer bar configuration
        prayer_config = config.get("ui_coordinates", "prayer_bar", default={
            "left": 217, "top": 42, "width": 18, "height": 250
        })
        self.prayer_bar = Rectangle(
            left=self.control_panel.left + prayer_config["left"],
            top=self.control_panel.top + prayer_config["top"],
            width=prayer_config["width"],
            height=prayer_config["height"],
        )

    # Override
    def resize(self, width: int = None, height: int = None) -> None:
        """
        Resizes the client window. Uses machine config defaults if not specified.
        Args:
            width: The width to resize the window to.
            height: The height to resize the window to.
        """
        if width is None or height is None:
            config = get_machine_config()
            default_width, default_height = config.get_window_default_size()
            width = width or default_width
            height = height or default_height
        
        if client := self.window:
            client.size = (width, height)


class RuneLiteBot(Bot, metaclass=ABCMeta):
    win: RuneLiteWindow = None

    def __init__(self, game_title, bot_title, description, window: Window = RuneLiteWindow("RuneLite")) -> None:
        super().__init__(game_title, bot_title, description, window)

    # --- OCR Functions ---
    @deprecated(reason="This is a slow way of checking if you are in combat. Consider using an API function instead.")
    def is_in_combat(self) -> bool:
        """
        Returns whether the player is in combat. This is achieved by checking if text exists in the RuneLite opponent info
        section in the game view, and if that text indicates an NPC is out of HP.
        """
        if ocr.extract_text(self.win.current_action, ocr.PLAIN_12, clr.WHITE):
            return True

    def is_player_doing_action(self, action: str):
        """
        Returns whether the player character is doing a given action. This works by checking the text in the current action
        region of the game view.
        Args:
            action: The action to check for (E.g., "Woodcutting" - case sensitive).
        Returns:
            True if the player is doing the given action, False otherwise.
        """
        return ocr.find_text(action, self.win.current_action, ocr.PLAIN_12, clr.GREEN)

    def pick_up_loot(self, items: Union[str, List[str]], supress_warning=True) -> bool:
        """
        Attempts to pick up a single purple loot item off the ground. It is your responsibility to ensure you have
        enough inventory space to pick up the item. The item closest to the game view center is picked up first.
        Args:
            item: The name(s) of the item(s) to pick up (E.g. -> "Coins", or "coins, bones", or ["Coins", "Dragon bones"]).
        Returns:
            True if the item was clicked, False otherwise.
        """
        # Capitalize each item name
        if isinstance(items, list):
            for i, item in enumerate(items):
                item = item.capitalize()
                items[i] = item
        else:
            items = self.capitalize_loot_list(items, to_list=True)
        # Locate Ground Items text
        if item_text := ocr.find_text(items, self.win.game_view, ocr.PLAIN_11, clr.PURPLE):
            for item in item_text:
                item.set_rectangle_reference(self.win.game_view)
            sorted_by_closest = sorted(item_text, key=Rectangle.distance_from_center)
            start_pos = sorted_by_closest[0].get_center()
            self.mouse.move_to(start_pos)
            for offset in range(5):
                if self.mouseover_text(contains=["Take"] + items, color=[clr.OFF_WHITE, clr.OFF_ORANGE]):
                    break
                # Use absolute positioning instead of move_rel
                target_pos = Point(start_pos.x, start_pos.y + (offset + 1) * 3)
                self.mouse.move_to(target_pos, mouseSpeed="fastest")
            self.mouse.right_click()
            # search the right-click menu
            if take_text := ocr.find_text(
                items,
                self.win.game_view,
                ocr.BOLD_12,
                [clr.WHITE, clr.PURPLE, clr.ORANGE],
            ):
                self.mouse.move_to(take_text[0].random_point(), mouseSpeed="medium")
                self.mouse.click()
                return True
            else:
                self.log_msg(f"Could not find 'Take {items}' in right-click menu.")
                return False
        elif not supress_warning:
            self.log_msg(f"Could not find {items} on the ground.")
            return False

    def capitalize_loot_list(self, loot: str, to_list: bool):
        """
        Takes a comma-separated string of loot items and capitalizes each item.
        Args:
            loot_list: A comma-separated string of loot items.
            to_list: Whether to return a list of capitalized loot items (or keep it as a string).
        Returns:
            A list of capitalized loot items.
        """
        if not loot:
            return ""
        phrases = loot.split(",")
        capitalized_phrases = []
        for phrase in phrases:
            stripped_phrase = phrase.strip()
            capitalized_phrase = stripped_phrase.capitalize()
            capitalized_phrases.append(capitalized_phrase)
        return capitalized_phrases if to_list else ", ".join(capitalized_phrases)

    # --- NPC/Object Detection ---
    def get_nearest_tagged_NPC(self, include_in_combat: bool = False) -> RuneLiteObject:
        # sourcery skip: use-next
        """
        Locates the nearest tagged NPC, optionally including those in combat.
        Args:
            include_in_combat: Whether to include NPCs that are already in combat.
        Returns:
            A RuneLiteObject object or None if no tagged NPCs are found.
        """
        game_view = self.win.game_view
        img_game_view = game_view.screenshot()
        # Isolate colors in image
        img_npcs = clr.isolate_colors(img_game_view, clr.CYAN)
        img_fighting_entities = clr.isolate_colors(img_game_view, [clr.GREEN, clr.RED])
        # Locate potential NPCs in image by determining contours
        objs = rcv.extract_objects(img_npcs)
        if not objs:
            print("No tagged NPCs found.")
            return None
        for obj in objs:
            obj.set_rectangle_reference(self.win.game_view)
        # Sort shapes by distance from player
        objs = sorted(objs, key=RuneLiteObject.distance_from_rect_center)
        if include_in_combat:
            return objs[0]
        for obj in objs:
            if not rcv.is_point_obstructed(obj._center, img_fighting_entities):
                return obj
        return None

    def get_all_tagged_in_rect(self, rect: Rectangle, color: clr.Color) -> List[RuneLiteObject]:
        """
        Finds all contours on screen of a particular color and returns a list of Shapes.
        Args:
            rect: A reference to the Rectangle that this shape belongs in (E.g., Bot.win.control_panel).
            color: The clr.Color to search for.
        Returns:
            A list of RuneLiteObjects or empty list if none found.
        """
        img_rect = rect.screenshot()
        isolated_colors = clr.isolate_colors(img_rect, color)
        objs = rcv.extract_objects(isolated_colors)
        for obj in objs:
            obj.set_rectangle_reference(rect)
        return objs

    def get_nearest_tag(self, color: clr.Color) -> RuneLiteObject:
        """
        Finds the nearest outlined object of a particular color within the game view and returns it as a RuneLiteObject.
        Args:
            color: The clr.Color to search for.
        Returns:
            The nearest outline to the character as a RuneLiteObject, or None if none found.
        """
        if shapes := self.get_all_tagged_in_rect(self.win.game_view, color):
            shapes_sorted = sorted(shapes, key=RuneLiteObject.distance_from_rect_center)
            return shapes_sorted[0]
        else:
            return None

    # --- Client Settings ---
    @deprecated(reason="This method is no longer needed for RuneLite games that can launch with arguments through the OSBC client.")
    def logout_runelite(self):
        """
        Identifies the RuneLite logout button and clicks it.
        """
        self.log_msg("Logging out of RuneLite...")
        rl_login_icon = imsearch.search_img_in_rect(
            imsearch.BOT_IMAGES.joinpath("settings", "runelite_logout.png"),
            self.win.rectangle(),
            confidence=0.9,
        )
        if rl_login_icon is not None:
            self.mouse.move_to(rl_login_icon.random_point())
            self.mouse.click()
            time.sleep(0.2)
            # Use safe key press to ensure window is focused
            if not self._safe_key_press("enter"):
                self.log_msg("Warning: Could not press enter - focus lost")
            time.sleep(1)
