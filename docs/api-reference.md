# Auto-OSBC API Reference

## Overview
This document provides comprehensive API reference for developing bots within the Auto-OSBC framework. The framework provides a rich set of APIs for computer vision, game interaction, and automation.

## Core Bot Framework

### Bot Class (Abstract Base)
**File**: `src/model/bot.py`

#### Constructor
```python
def __init__(self, game_title: str, bot_title: str, description: str, window: Window)
```
**Parameters**:
- `game_title`: The name of the game (used for UI organization)
- `bot_title`: Display name for the bot in the UI
- `description`: Description shown to users
- `window`: Window management object for game client interaction

#### Required Abstract Methods

##### main_loop()
```python
@abstractmethod
def main_loop(self) -> None
```
**Purpose**: Core bot logic executed in separate thread
**Implementation**: Must contain the primary automation logic

**Example**:
```python
def main_loop(self):
    start_time = time.time()
    end_time = self.running_time * 60
    
    while time.time() - start_time < end_time:
        if self.should_mine():
            self.mine_rock()
        elif self.should_drop_inventory():
            self.drop_all()
        
        self.update_progress((time.time() - start_time) / end_time)
        time.sleep(1)
```

##### create_options()
```python
@abstractmethod
def create_options(self) -> None
```
**Purpose**: Define bot configuration UI using OptionsBuilder
**Usage**: Called when user opens options panel

**Example**:
```python
def create_options(self):
    self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 360)
    self.options_builder.add_dropdown_option("logout_on_friends", "Logout when friends nearby?", ["Yes", "No"])
    self.options_builder.add_checkbox_option("items_to_keep", "Items to keep", ["Pickaxe", "Food", "Potions"])
```

##### save_options()
```python
@abstractmethod
def save_options(self, options: dict) -> None
```
**Purpose**: Process and store user configuration
**Parameters**: `options` - Dictionary of user selections

**Example**:
```python
def save_options(self, options: dict):
    for option in options:
        if option == "running_time":
            self.running_time = options[option]
        elif option == "logout_on_friends":
            self.logout_on_friends = options[option] == "Yes"
    self.options_set = True
```

#### Bot Control Methods

##### play()
```python
def play(self) -> None
```
**Purpose**: Start bot execution
**Behavior**: 
- Validates options are set
- Initializes game window
- Starts bot thread
- Updates UI status

##### stop()
```python
def stop(self) -> None
```
**Purpose**: Stop bot execution
**Behavior**:
- Sets status to STOPPED
- Terminates bot thread
- Updates UI

#### Status and Progress Management

##### update_progress()
```python
def update_progress(self, progress: float) -> None
```
**Parameters**: `progress` - Float between 0.0 and 1.0
**Purpose**: Update progress bar in UI

##### set_status()
```python
def set_status(self, status: BotStatus) -> None
```
**Parameters**: `status` - BotStatus enum value
**Purpose**: Update bot status in UI

##### log_msg()
```python
def log_msg(self, msg: str, overwrite: bool = False) -> None
```
**Parameters**: 
- `msg` - Message to display
- `overwrite` - Whether to replace last message
**Purpose**: Send message to UI log

#### Inventory Management

##### drop_all()
```python
def drop_all(self, skip_rows: int = 0, skip_slots: List[int] = None) -> None
```
**Parameters**:
- `skip_rows` - Number of top rows to skip
- `skip_slots` - List of slot indices to preserve
**Purpose**: Shift-click drop all inventory items

**Example**:
```python
# Drop everything except first row
self.drop_all(skip_rows=1)

# Drop everything except slots 0, 1, 27
self.drop_all(skip_slots=[0, 1, 27])
```

##### drop()
```python
def drop(self, slots: List[int]) -> None
```
**Parameters**: `slots` - List of inventory slot indices to drop
**Purpose**: Drop specific inventory slots

#### Player Status Methods

##### get_hp()
```python
def get_hp(self) -> int
```
**Returns**: Current hitpoints or -1 if failed
**Purpose**: Read HP from orb using OCR

##### get_prayer()
```python
def get_prayer(self) -> int
```
**Returns**: Current prayer points or -1 if failed

##### get_run_energy()
```python
def get_run_energy(self) -> int
```
**Returns**: Current run energy or -1 if failed

##### get_special_energy()
```python
def get_special_energy(self) -> int
```
**Returns**: Current special attack energy or -1 if failed

##### friends_nearby()
```python
def friends_nearby(self) -> bool
```
**Returns**: True if green dots detected on minimap
**Purpose**: Friend detection for logout safety

#### Game Interaction Methods

##### mouseover_text()
```python
def mouseover_text(self, contains: Union[str, List[str]] = None, color: Union[clr.Color, List[clr.Color]] = None) -> Union[bool, str]
```
**Parameters**:
- `contains` - Text to search for
- `color` - Colors to isolate for OCR
**Returns**: Boolean if text found, or full text if no search terms
**Purpose**: Read mouseover tooltip text

##### chatbox_text()
```python
def chatbox_text(self, contains: str = None) -> Union[bool, str]
```
**Purpose**: Read player chat text

##### get_game_message()
```python
def get_game_message(self, contains: str = None) -> Union[bool, str]
```
**Purpose**: Read game messages (black text) from chatbox

#### Camera and Client Control

##### set_compass_north()
```python
def set_compass_north(self) -> None
```
**Purpose**: Reset camera to face north

##### move_camera()
```python
def move_camera(self, horizontal: int = 0, vertical: int = 0) -> None
```
**Parameters**:
- `horizontal` - Degrees to rotate (-360 to 360)
- `vertical` - Degrees to tilt (-90 to 90)
**Purpose**: Programmatic camera movement

##### toggle_auto_retaliate()
```python
def toggle_auto_retaliate(self, toggle_on: bool) -> None
```
**Purpose**: Enable/disable auto retaliate in combat tab

##### toggle_run()
```python
def toggle_run(self, toggle_on: bool) -> None
```
**Purpose**: Enable/disable run mode

#### Utility Methods

##### take_break()
```python
def take_break(self, min_seconds: int = 1, max_seconds: int = 30, fancy: bool = False) -> None
```
**Parameters**:
- `min_seconds` - Minimum break duration
- `max_seconds` - Maximum break duration  
- `fancy` - Use advanced randomization
**Purpose**: Take randomized break with countdown

### RuneLiteBot Class (Extension)
**File**: `src/model/runelite_bot.py`
**Inherits**: Bot class with RuneLite-specific functionality

#### Object Detection Methods

##### get_nearest_tagged_NPC()
```python
def get_nearest_tagged_NPC(self, include_in_combat: bool = False) -> RuneLiteObject
```
**Parameters**: `include_in_combat` - Whether to include NPCs already in combat
**Returns**: Nearest tagged NPC or None
**Purpose**: Find closest cyan-outlined NPC

##### get_all_tagged_in_rect()
```python
def get_all_tagged_in_rect(self, rect: Rectangle, color: clr.Color) -> List[RuneLiteObject]
```
**Parameters**:
- `rect` - Screen region to search
- `color` - Color outline to detect
**Returns**: List of detected objects
**Purpose**: Find all objects with specific color outline

**Example**:
```python
# Find all pink-tagged mining rocks
rocks = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)

# Find all cyan NPCs in a specific area
npcs = self.get_all_tagged_in_rect(combat_area, clr.CYAN)
```

##### get_nearest_tag()
```python
def get_nearest_tag(self, color: clr.Color) -> RuneLiteObject
```
**Parameters**: `color` - Color to search for
**Returns**: Nearest object with specified color outline
**Purpose**: Find closest object of specific color

#### Loot and Interaction

##### pick_up_loot()
```python
def pick_up_loot(self, items: Union[str, List[str]], supress_warning: bool = True) -> bool
```
**Parameters**:
- `items` - Item name(s) to pick up
- `supress_warning` - Whether to suppress "not found" warnings
**Returns**: True if item was clicked
**Purpose**: Automatically pick up ground items

**Example**:
```python
# Pick up specific items
self.pick_up_loot(["Coins", "Dragon bones"])

# Pick up from comma-separated string
self.pick_up_loot("coins, bones, arrows")
```

##### is_player_doing_action()
```python
def is_player_doing_action(self, action: str) -> bool
```
**Parameters**: `action` - Action name to check (case sensitive)
**Returns**: True if player is performing the action
**Purpose**: Check current player activity via text detection

## Window Management API

### Window Class
**File**: `src/utilities/window.py`

#### Properties
All properties are Rectangle objects representing screen regions:

**Game Areas**:
- `game_view` - Main game viewport
- `minimap` - Minimap area (without orbs)
- `minimap_area` - Full minimap region including orbs
- `chat` - Chat area
- `control_panel` - Inventory/spells/prayers panel

**UI Elements**:
- `inventory_slots` - List[Rectangle] of 28 inventory slots
- `cp_tabs` - List[Rectangle] of control panel tabs
- `chat_tabs` - List[Rectangle] of chat tabs
- `prayers` - List[Rectangle] of prayer book slots
- `spellbook_normal` - List[Rectangle] of normal spellbook slots

**Orbs and Status**:
- `hp_orb_text` - HP text region
- `prayer_orb_text` - Prayer text region
- `run_orb_text` - Run energy text region
- `spec_orb_text` - Special attack text region
- `compass_orb` - Compass orb clickable area

#### Methods

##### initialize()
```python
def initialize(self) -> bool
```
**Returns**: True if successful
**Purpose**: Locate and map all UI elements
**Called**: Automatically when bot starts

##### focus()
```python
def focus(self) -> None
```
**Purpose**: Bring game window to foreground

##### resize()
```python
def resize(self, width: int, height: int) -> None
```
**Purpose**: Resize game client window

## Computer Vision API

### Image Search
**File**: `src/utilities/imagesearch.py`

##### search_img_in_rect()
```python
def search_img_in_rect(image: Union[cv2.Mat, str, Path], rect: Union[Rectangle, cv2.Mat], confidence: float = 0.15) -> Rectangle
```
**Parameters**:
- `image` - Image to search for (path or matrix)
- `rect` - Area to search in
- `confidence` - Match confidence (0.0 = perfect match)
**Returns**: Rectangle of found image or None
**Purpose**: Locate template image within screen region

**Example**:
```python
# Find deposit button in bank interface
deposit_btn = search_img_in_rect(
    BOT_IMAGES.joinpath("bank", "deposit_all.png"),
    self.win.control_panel,
    confidence=0.1
)
if deposit_btn:
    self.mouse.move_to(deposit_btn.random_point())
    self.mouse.click()
```

### Color Detection
**File**: `src/utilities/color.py`

#### Color Constants
```python
# Game colors
CYAN = Color([255, 255, 0])      # Tagged NPCs
PINK = Color([255, 0, 255])      # Tagged objects
PURPLE = Color([128, 0, 128])    # Ground items
GREEN = Color([0, 255, 0])       # Health bars
RED = Color([0, 0, 255])         # Damage/combat

# UI colors  
WHITE = Color([255, 255, 255])
BLACK = Color([0, 0, 0])
ORB_GREEN = Color([0, 252, 0])   # Orb text color
```

##### isolate_colors()
```python
def isolate_colors(image: np.ndarray, colors: Union[Color, List[Color]]) -> np.ndarray
```
**Parameters**:
- `image` - Input image
- `colors` - Color(s) to isolate
**Returns**: Filtered image with only specified colors
**Purpose**: Filter image to show only target colors

### OCR (Optical Character Recognition)
**File**: `src/utilities/ocr.py`

#### Font Constants
```python
PLAIN_11 = "Plain11"
PLAIN_12 = "Plain12" 
BOLD_12 = "Bold12"
QUILL = "Quill"
```

##### extract_text()
```python
def extract_text(image: Union[Rectangle, np.ndarray], font: str, colors: List[Color]) -> str
```
**Parameters**:
- `image` - Image or Rectangle to read
- `font` - Font type to use for recognition
- `colors` - Text colors to isolate
**Returns**: Extracted text string
**Purpose**: Extract text from image using bitmap font matching

##### find_text()
```python
def find_text(text: Union[str, List[str]], image: Union[Rectangle, np.ndarray], font: str, colors: List[Color]) -> List[Rectangle]
```
**Parameters**:
- `text` - Text to search for
- `image` - Image to search in
- `font` - Font type
- `colors` - Text colors
**Returns**: List of Rectangle objects where text was found
**Purpose**: Locate specific text in image

**Example**:
```python
# Read HP from orb
hp_text = ocr.extract_text(self.win.hp_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN])

# Find "Attack" option in right-click menu
attack_options = ocr.find_text("Attack", self.win.game_view, ocr.BOLD_12, [clr.WHITE])
if attack_options:
    self.mouse.move_to(attack_options[0].random_point())
    self.mouse.click()
```

## Game State APIs

### EventsAPI Client
**File**: `src/utilities/api/events_client.py`

#### Player Data Methods

##### get_hitpoints()
```python
@staticmethod
def get_hitpoints() -> Tuple[int, int]
```
**Returns**: (current_hp, max_hp) or (-1, -1) if failed

##### get_run_energy()
```python
@staticmethod
def get_run_energy() -> int
```
**Returns**: Current run energy percentage

##### get_animation()
```python
@staticmethod
def get_animation() -> int
```
**Returns**: Current animation ID

##### get_is_player_idle()
```python
@staticmethod
def get_is_player_idle() -> bool
```
**Returns**: True if player is idle (not animating)

#### World Data Methods

##### get_player_position()
```python
@staticmethod
def get_player_position() -> Tuple[int, int, int]
```
**Returns**: (x, y, plane) world coordinates

##### get_game_tick()
```python
@staticmethod
def get_game_tick() -> int
```
**Returns**: Current game tick number

##### get_is_in_combat()
```python
@staticmethod
def get_is_in_combat() -> bool
```
**Returns**: True if player is in combat

#### Inventory Methods

##### get_inv()
```python
@staticmethod
def get_inv() -> List[Dict[str, Any]]
```
**Returns**: List of inventory items with id, quantity, index

##### get_is_inv_full()
```python
@staticmethod
def get_is_inv_full() -> bool
```
**Returns**: True if all 28 slots occupied

##### get_if_item_in_inv()
```python
@staticmethod
def get_if_item_in_inv(item_id: Union[int, List[int]]) -> bool
```
**Parameters**: `item_id` - Item ID(s) to check for
**Returns**: True if item present in inventory

##### get_inv_item_indices()
```python
@staticmethod
def get_inv_item_indices(item_id: Union[int, List[int]]) -> List[int]
```
**Returns**: List of slot indices containing the item

#### Skill Methods

##### get_skill_level()
```python
@staticmethod
def get_skill_level(skill: str) -> int
```
**Parameters**: `skill` - Skill name (e.g., "Woodcutting")
**Returns**: Current skill level

##### get_skill_xp()
```python
@staticmethod
def get_skill_xp(skill: str) -> int
```
**Returns**: Total experience in skill

##### wait_til_gained_xp()
```python
@staticmethod
def wait_til_gained_xp(skill: str, timeout: int = 10) -> int
```
**Parameters**:
- `skill` - Skill to monitor
- `timeout` - Maximum wait time in seconds
**Returns**: New XP total or -1 if timeout
**Purpose**: Block until XP is gained in specified skill

### MorgHTTPSocket Client
**File**: `src/utilities/api/morg_http_client.py`

Similar functionality to EventsAPI but using HTTP requests. Provides inventory management, equipment detection, and player monitoring.

## Mouse Automation API

### Mouse Class
**File**: `src/utilities/mouse.py`

##### move_to()
```python
def move_to(self, point: Union[Point, Tuple[int, int]], mouseSpeed: str = "medium", **kwargs) -> None
```
**Parameters**:
- `point` - Target coordinates
- `mouseSpeed` - Speed preset ("fastest", "fast", "medium", "slow")
- `**kwargs` - Additional movement parameters
**Purpose**: Move mouse with human-like curves

##### click()
```python
def click(self) -> None
```
**Purpose**: Perform left mouse click

##### right_click()
```python
def right_click(self) -> None
```
**Purpose**: Perform right mouse click

##### move_rel()
```python
def move_rel(self, x_offset: int, y_offset: int, x_variance: int = 0, y_variance: int = 0, mouseSpeed: str = "medium") -> None
```
**Purpose**: Move mouse relative to current position with randomization

**Example**:
```python
# Click inventory slot with human-like movement
slot = self.win.inventory_slots[0]
self.mouse.move_to(slot.random_point(), mouseSpeed="fast")
self.mouse.click()

# Right-click and move to context menu option
self.mouse.right_click()
self.mouse.move_rel(0, 25, 3, 2)  # Move down with variance
self.mouse.click()
```

## Geometry API

### Point Class
**File**: `src/utilities/geometry.py`

```python
class Point:
    def __init__(self, x: int, y: int)
    
    # Properties
    x: int
    y: int
    
    # Methods
    def distance_to(self, other: Point) -> float
    def add(self, other: Point) -> Point
    def subtract(self, other: Point) -> Point
```

### Rectangle Class

```python
class Rectangle:
    def __init__(self, left: int, top: int, width: int, height: int)
    
    # Properties
    left: int
    top: int
    width: int
    height: int
    
    # Methods
    def get_center(self) -> Point
    def random_point(self) -> Point
    def contains_point(self, point: Point) -> bool
    def screenshot(self) -> np.ndarray
    def distance_from_center(self) -> float
```

### RuneLiteObject Class

```python
class RuneLiteObject(Rectangle):
    def __init__(self, contour: np.ndarray, color: Color)
    
    # Additional properties
    color: Color
    contour: np.ndarray
    
    # Methods
    def set_rectangle_reference(self, reference: Rectangle) -> None
    def distance_from_rect_center(self) -> float
```

**Example Usage**:
```python
# Get all tagged rocks
rocks = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)

# Sort by distance from center
rocks_sorted = sorted(rocks, key=RuneLiteObject.distance_from_rect_center)

# Click nearest rock
if rocks_sorted:
    nearest_rock = rocks_sorted[0]
    self.mouse.move_to(nearest_rock.random_point())
    self.mouse.click()
```

## Development Utilities

### Debug Module
**File**: `src/utilities/debug.py`

##### save_image()
```python
def save_image(filename: str, image: np.ndarray) -> None
```
**Purpose**: Save image to debug_screenshots/ directory

##### current_time()
```python
def current_time() -> str
```
**Returns**: Formatted timestamp string
**Purpose**: Generate timestamps for logging

### Settings Module
**File**: `src/utilities/settings.py`

##### get()
```python
def get(key: str) -> Any
```
**Purpose**: Retrieve setting value

##### set()
```python
def set(key: str, value: Any) -> None
```
**Purpose**: Store setting value

## Error Handling

### Common Exceptions

#### WindowInitializationError
**Raised when**: Game window cannot be found or initialized
**Handling**: Check game client is running and visible

#### SocketError
**Raised when**: API connection fails
**Handling**: Verify game client plugins are enabled

### Best Practices

1. **Always check return values** from detection methods
2. **Use try-catch** for API calls that may fail
3. **Validate visual detection** before acting on results
4. **Implement timeouts** for waiting operations
5. **Log errors** with descriptive messages

**Example Error Handling**:
```python
def main_loop(self):
    try:
        while self.should_continue():
            # Visual detection with validation
            targets = self.find_targets()
            if not targets:
                self.log_msg("No targets found, waiting...")
                time.sleep(5)
                continue
            
            # API call with error handling
            try:
                if not self.api_client.get_is_player_idle():
                    time.sleep(1)
                    continue
            except SocketError as e:
                self.log_msg(f"API error: {e}")
                time.sleep(5)
                continue
            
            # Perform action
            self.interact_with_target(targets[0])
            
    except Exception as e:
        self.log_msg(f"Bot error: {e}")
        self.stop()
```

## Performance Guidelines

### Detection Performance
- **Target**: < 100ms per detection operation
- **Optimization**: Cache detection results when appropriate
- **Monitoring**: Use debug timing to measure performance

### Memory Management
- **Screenshots**: Don't store large images unnecessarily
- **Caching**: Clear caches periodically
- **Monitoring**: Watch memory usage during long runs

### CPU Usage
- **Sleep intervals**: Include appropriate delays in main loop
- **Batch operations**: Group related operations together
- **Profiling**: Use profiling tools to identify bottlenecks