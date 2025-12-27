"""
This class contains functions for interacting with the game client window. All Bot classes have a
Window object as a property. This class allows you to locate important points/areas on screen no
matter where the game client is positioned. This class can be extended to add more functionality
(See RuneLiteWindow within runelite_bot.py for an example).

At the moment, it only works for 2007-style interfaces. In the future, to accomodate other interface
styles, this class should be abstracted, then extended for each interface style.
"""
import time
from typing import List

import pywinctl
from deprecated import deprecated

import utilities.debug as debug
import utilities.imagesearch as imsearch
from utilities.geometry import Point, Rectangle
from utilities.machine_config import get_machine_config


class WindowInitializationError(Exception):
    """
    Exception raised for errors in the Window class.
    """

    def __init__(self, message=None):
        if message is None:
            message = (
                "Failed to initialize window. Make sure the client is NOT in 'Resizable-Modern' "
                "mode. Make sure you're using the default client configuration (E.g., Opaque UI, status orbs ON)."
            )
        super().__init__(message)


class Window:
    client_fixed: bool = None

    # CP Area
    control_panel: Rectangle = None  # https://i.imgur.com/BeMFCIe.png
    cp_tabs: List[Rectangle] = []  # https://i.imgur.com/huwNOWa.png
    inventory_slots: List[Rectangle] = []  # https://i.imgur.com/gBwhAwE.png
    spellbook_normal: List[Rectangle] = []  # https://i.imgur.com/vkKAfV5.png
    prayers: List[Rectangle] = []  # https://i.imgur.com/KRmC3YB.png

    # Chat Area
    chat: Rectangle = None  # https://i.imgur.com/u544ouI.png
    chat_tabs: List[Rectangle] = []  # https://i.imgur.com/2DH2SiL.png

    # Minimap Area
    compass_orb: Rectangle = None
    hp_orb_text: Rectangle = None
    minimap_area: Rectangle = None  # https://i.imgur.com/idfcIPU.png OR https://i.imgur.com/xQ9xg1Z.png
    minimap: Rectangle = None
    prayer_orb_text: Rectangle = None
    prayer_orb: Rectangle = None
    run_orb_text: Rectangle = None
    run_orb: Rectangle = None
    spec_orb_text: Rectangle = None
    spec_orb: Rectangle = None

    # Game View Area
    game_view: Rectangle = None
    mouseover: Rectangle = None
    total_xp: Rectangle = None

    def __init__(self, window_title: str, padding_top: int, padding_left: int) -> None:
        """
        Creates a Window object with various methods for interacting with the client window.
        Args:
            window_title: The title of the client window.
            padding_top: The height of the client window's header.
            padding_left: The width of the client window's left border.
        """
        self.window_title = window_title
        self.padding_top = padding_top
        self.padding_left = padding_left

    def _get_window(self):
        self._client = pywinctl.getWindowsWithTitle(self.window_title)
        if self._client:
            return self._client[0]
        else:
            raise WindowInitializationError("No client window found.")

    window = property(
        fget=_get_window,
        doc="A Win32Window reference to the game client and its properties.",
    )

    def focus(self) -> None:  # sourcery skip: raise-from-previous-error
        """
        Focuses the client window.
        """
        if client := self.window:
            try:
                client.activate()
            except Exception:
                raise WindowInitializationError("Failed to focus client window. Try bringing it to the foreground.")

    def position(self) -> Point:
        """
        Returns the origin of the client window as a Point.
        """
        if client := self.window:
            return Point(client.left, client.top)

    def rectangle(self) -> Rectangle:
        """
        Returns a Rectangle outlining the entire client window.
        """
        if client := self.window:
            return Rectangle(client.left, client.top, client.width, client.height)

    def resize(self, width: int, height: int) -> None:
        """
        Resizes the client window..
        Args:
            width: The width to resize the window to.
            height: The height to resize the window to.
        """
        if client := self.window:
            client.size = (width, height)

    def initialize(self):
        """
        Initializes the client window by locating critical UI regions.
        This function should be called when the bot is started or resumed (done by default).
        Returns:
            True if successful, False otherwise along with an error message.
        """
        start_time = time.time()
        client_rect = self.rectangle()
        a = self.__locate_minimap(client_rect)
        b = self.__locate_chat(client_rect)
        c = self.__locate_control_panel(client_rect)
        d = self.__locate_game_view(client_rect)
        if all([a, b, c, d]):  # if all templates found
            print(f"Window.initialize() took {time.time() - start_time} seconds.")
            return True
        raise WindowInitializationError()

    def __locate_chat(self, client_rect: Rectangle) -> bool:
        """
        Locates the chat area on the client.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if chat := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "chat.png"), client_rect):
            # Locate chat tabs
            self.chat_tabs = []
            x, y = 5, 143
            # Get chat tabs configuration from machine profile
            config = get_machine_config()
            chat_tabs_config = config.get_chat_tabs_config()
            
            if self.client_fixed and "fixed_mode" in chat_tabs_config and "positions" in chat_tabs_config["fixed_mode"]:
                # Use configured positions
                for pos in chat_tabs_config["fixed_mode"]["positions"]:
                    self.chat_tabs.append(Rectangle(
                        left=pos["x"] + chat.left,
                        top=pos["y"] + chat.top,
                        width=pos["width"],
                        height=pos["height"]
                    ))
            else:
                # Fallback to original logic
                for _ in range(7):
                    self.chat_tabs.append(Rectangle(left=x + chat.left, top=y + chat.top, width=52, height=19))
                    x += 62  # btn width is 52px, gap between each is 10px
            self.chat = chat
            return True
        print("Window.__locate_chat(): Failed to find chatbox.")
        return False

    def __locate_control_panel(self, client_rect: Rectangle) -> bool:
        """
        Locates the control panel area on the client.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if cp := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "inv.png"), client_rect):
            self.__locate_cp_tabs(cp)
            self.__locate_inv_slots(cp)
            self.__locate_prayers(cp)
            self.__locate_spells(cp)
            self.control_panel = cp
            return True
        print("Window.__locate_control_panel(): Failed to find control panel.")
        return False

    def __locate_cp_tabs(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each interface tab (inventory, prayer, etc.) relative to the control panel, storing it in the class property.
        """
        self.cp_tabs = []
        config = get_machine_config()
        cp_tabs_config = config.get_control_panel_tabs_config()
        
        # Use configuration if available
        if "rows" in cp_tabs_config:
            for row in cp_tabs_config["rows"]:
                for x_pos in row["positions"]:
                    self.cp_tabs.append(Rectangle(
                        left=x_pos + cp.left,
                        top=row["y"] + cp.top,
                        width=row["tab_width"],
                        height=row["height"]
                    ))
        else:
            # Fallback to original logic
            slot_w, slot_h = 29, 26  # top row tab dimensions
            gap = 4  # 4px gap between tabs
            y = 4  # 4px from top for first row
            for _ in range(2):
                x = 8 + cp.left
                for _ in range(7):
                    self.cp_tabs.append(Rectangle(left=x, top=y + cp.top, width=slot_w, height=slot_h))
                    x += slot_w + gap
                y = 303  # 303px from top for second row
                slot_h = 28  # slightly taller tab Rectangles for second row

    def __locate_inv_slots(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each inventory slot relative to the control panel, storing it in the class property.
        """
        self.inventory_slots = []
        
        # Get inventory configuration from machine profile
        config = get_machine_config()
        inv_config = config.get_inventory_config()
        
        slot_w = inv_config.get("slot_width", 36) - 5  # Subtract 5 for actual clickable area
        slot_h = inv_config.get("slot_height", 32) - 1  # Subtract 1 for actual clickable area
        gap_x = inv_config.get("gap_x", 6)
        gap_y = inv_config.get("gap_y", 4)
        start_x = inv_config.get("start_x", 40)
        start_y = inv_config.get("start_y", 44)
        
        y = start_y + cp.top
        for _ in range(7):
            x = start_x + cp.left
            for _ in range(4):
                self.inventory_slots.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y

    def __locate_prayers(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each prayer in the prayer book menu relative to the control panel, storing it in the class property.
        """
        self.prayers = []
        
        # Get prayers configuration from machine profile
        config = get_machine_config()
        prayer_config = config.get_prayers_config()
        
        slot_w = prayer_config.get("prayer_width", 33) + 1  # Add 1 to match original behavior
        slot_h = prayer_config.get("prayer_height", 33) + 1  # Add 1 to match original behavior
        gap_x = prayer_config.get("gap_x", 3)
        gap_y = prayer_config.get("gap_y", 3)
        start_x = prayer_config.get("start_x", 30)
        start_y = prayer_config.get("start_y", 46)
        rows = prayer_config.get("grid_rows", 6)
        cols = prayer_config.get("grid_cols", 5)
        
        y = start_y + cp.top
        for _ in range(rows):
            x = start_x + cp.left
            for _ in range(cols):
                self.prayers.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y
        del self.prayers[29]  # remove the last prayer (unused)

    def __locate_spells(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each magic spell relative to the control panel, storing it in the class property.
        Currently only populates the normal spellbook spells.
        """
        self.spellbook_normal = []
        
        # Get spellbook configuration from machine profile
        config = get_machine_config()
        spell_config = config.get_spellbook_config()
        
        slot_w = spell_config.get("spell_width", 23) - 1  # Subtract 1 to match original behavior
        slot_h = spell_config.get("spell_height", 23) - 1  # Subtract 1 to match original behavior
        gap_x = spell_config.get("gap_x", 4)
        gap_y = spell_config.get("gap_y", 2)
        start_x = spell_config.get("start_x", 30)
        start_y = spell_config.get("start_y", 37)
        rows = spell_config.get("grid_rows", 10)
        cols = spell_config.get("grid_cols", 7)
        
        y = start_y + cp.top
        for _ in range(rows):
            x = start_x + cp.left
            for _ in range(cols):
                self.spellbook_normal.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y

    def __locate_game_view(self, client_rect: Rectangle) -> bool:
        """
        Locates the game view while considering the client mode (Fixed/Resizable). https://i.imgur.com/uuCQbxp.png
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if self.minimap_area is None or self.chat is None or self.control_panel is None:
            print("Window.__locate_game_view(): Failed to locate game view. Missing minimap, chat, or control panel.")
            return False
        if self.client_fixed:
            # Uses the chatbox and known fixed size of game_view to locate it in fixed mode
            config = get_machine_config()
            game_view_config = config.get_ui_coordinates("fixed_mode", "game_view") or {"width": 517, "height": 337}
            self.game_view = Rectangle(
                left=self.chat.left,
                top=self.chat.top - game_view_config["height"],
                width=game_view_config["width"],
                height=game_view_config["height"]
            )
        else:
            # Uses control panel to find right-side bounds of game view in resizable mode
            self.game_view = Rectangle.from_points(
                Point(
                    client_rect.left + self.padding_left,
                    client_rect.top + self.padding_top,
                ),
                self.control_panel.get_bottom_right(),
            )
            # Locate the positions of the UI elements to be subtracted from the game_view, relative to the game_view
            minimap = self.minimap_area.to_dict()
            minimap["left"] -= self.game_view.left
            minimap["top"] -= self.game_view.top

            chat = self.chat.to_dict()
            chat["left"] -= self.game_view.left
            chat["top"] -= self.game_view.top

            control_panel = self.control_panel.to_dict()
            control_panel["left"] -= self.game_view.left
            control_panel["top"] -= self.game_view.top

            self.game_view.subtract_list = [minimap, chat, control_panel]
        config = get_machine_config()
        mouseover_config = config.get("ui_coordinates", "mouseover", default={"width": 407, "height": 26})
        self.mouseover = Rectangle(
            left=self.game_view.left,
            top=self.game_view.top,
            width=mouseover_config["width"],
            height=mouseover_config["height"]
        )
        return True

    def __locate_minimap(self, client_rect: Rectangle) -> bool:
        """
        Locates the minimap area on the clent window and all of its internal positions.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        # 'm' refers to minimap area
        config = get_machine_config()
        
        if m := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "minimap.png"), client_rect):
            self.client_fixed = False
            mode = "resizable_mode"
        elif m := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "minimap_fixed.png"), client_rect):
            self.client_fixed = True
            mode = "fixed_mode"
        else:
            m = None
        
        if m:
            # Helper function to get coordinates with defaults
            def get_coords(element_name: str, defaults: dict):
                coords = config.get_ui_coordinates(mode, element_name)
                if coords:
                    return Rectangle(
                        left=coords.get("left", defaults["left"]) + m.left,
                        top=coords.get("top", defaults["top"]) + m.top,
                        width=coords.get("width", defaults["width"]),
                        height=coords.get("height", defaults["height"])
                    )
                else:
                    return Rectangle(
                        left=defaults["left"] + m.left,
                        top=defaults["top"] + m.top,
                        width=defaults["width"],
                        height=defaults["height"]
                    )
            
            # Define defaults based on mode
            if self.client_fixed:
                defaults_map = {
                    "compass_orb": {"left": 31, "top": 7, "width": 24, "height": 25},
                    "hp_orb_text": {"left": 4, "top": 55, "width": 20, "height": 13},
                    "minimap": {"left": 52, "top": 4, "width": 147, "height": 160},
                    "prayer_orb": {"left": 30, "top": 80, "width": 19, "height": 20},
                    "prayer_orb_text": {"left": 4, "top": 89, "width": 20, "height": 13},
                    "run_orb": {"left": 40, "top": 112, "width": 19, "height": 20},
                    "run_orb_text": {"left": 14, "top": 121, "width": 20, "height": 13},
                    "spec_orb": {"left": 62, "top": 137, "width": 19, "height": 20},
                    "spec_orb_text": {"left": 36, "top": 146, "width": 20, "height": 13},
                    "total_xp": {"left": -104, "top": 6, "width": 104, "height": 21}
                }
            else:
                defaults_map = {
                    "compass_orb": {"left": 40, "top": 7, "width": 24, "height": 26},
                    "hp_orb_text": {"left": 4, "top": 60, "width": 20, "height": 13},
                    "minimap": {"left": 52, "top": 5, "width": 154, "height": 155},
                    "prayer_orb": {"left": 30, "top": 86, "width": 20, "height": 20},
                    "prayer_orb_text": {"left": 4, "top": 94, "width": 20, "height": 13},
                    "run_orb": {"left": 39, "top": 118, "width": 20, "height": 20},
                    "run_orb_text": {"left": 14, "top": 126, "width": 20, "height": 13},
                    "spec_orb": {"left": 62, "top": 144, "width": 18, "height": 20},
                    "spec_orb_text": {"left": 36, "top": 151, "width": 20, "height": 13},
                    "total_xp": {"left": -147, "top": 4, "width": 104, "height": 21}
                }
            
            # Create rectangles from configuration
            self.compass_orb = get_coords("compass_orb", defaults_map["compass_orb"])
            self.hp_orb_text = get_coords("hp_orb_text", defaults_map["hp_orb_text"])
            self.minimap = get_coords("minimap", defaults_map["minimap"])
            self.prayer_orb = get_coords("prayer_orb", defaults_map["prayer_orb"])
            self.prayer_orb_text = get_coords("prayer_orb_text", defaults_map["prayer_orb_text"])
            self.run_orb = get_coords("run_orb", defaults_map["run_orb"])
            self.run_orb_text = get_coords("run_orb_text", defaults_map["run_orb_text"])
            self.spec_orb = get_coords("spec_orb", defaults_map["spec_orb"])
            self.spec_orb_text = get_coords("spec_orb_text", defaults_map["spec_orb_text"])
            self.total_xp = get_coords("total_xp", defaults_map["total_xp"])
        if m:
            # Take a bite out of the bottom-left corner of the minimap to exclude orb's green numbers
            self.minimap.subtract_list = [{"left": 0, "top": self.minimap.height - 20, "width": 20, "height": 20}]
            self.minimap_area = m
            return True
        print("Window.__locate_minimap(): Failed to find minimap.")
        return False


class MockWindow(Window):
    def __init__(self):
        super().__init__(window_title="None", padding_left=0, padding_top=0)

    def _get_window(self):
        print("MockWindow._get_window() called.")

    window = property(
        fget=_get_window,
        doc="A Win32Window reference to the game client and its properties.",
    )

    def initialize(self) -> None:
        print("MockWindow.initialize() called.")

    def focus(self) -> None:
        print("MockWindow.focus() called.")

    def position(self) -> Point:
        print("MockWindow.position() called.")
