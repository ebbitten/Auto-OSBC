# Auto-OSBC Current State Documentation

## Overview
Auto-OSBC is a sophisticated game automation framework designed for RuneScape-like games. It uses computer vision, OCR, and HTTP APIs to interact with game clients without code injection or modification.

## Data Flow Architecture

### Visual Automation Pipeline
```
Game Client Window → Screenshot Capture → Visual Detection → Decision Logic → Action Execution
        ↓                    ↓                ↓               ↓              ↓
   [RuneLite]        [Window.screenshot()]  [Color/OCR]   [Bot Logic]   [Mouse/Click]
        ↑                    ↑                ↑               ↑              ↑
   Game State ←── API Polling ←── Game Events ←── State Check ←── Validation
   [EventsAPI]      [HTTP Client]      [Plugin Data]    [Idle Check]    [Safety]
```

### Detailed Data Flow Steps

**1. Input Capture**
```
Window Management → Screenshot → Region Extraction
     ↓                ↓             ↓
[Window.initialize()] → [region.screenshot()] → [game_view, inventory, etc.]
```

**2. Visual Processing**
```
Raw Screenshot → Color Isolation → Object Detection → Validation
       ↓              ↓               ↓              ↓
   [CV2 Image] → [clr.isolate_colors()] → [rcv.extract_objects()] → [size/position check]
```

**3. Game State Integration**
```
Visual Data + API Data → State Assessment → Decision Making
     ↓           ↓            ↓              ↓
[Detection] + [EventsAPI] → [game_state] → [next_action]
```

**4. Action Execution**
```
Decision → Movement Planning → Safety Check → Execution → Validation
    ↓           ↓                ↓             ↓           ↓
[target] → [bezier_curve] → [friends_check] → [click] → [idle_wait]
```

### Component Interaction Flow

**Bot Lifecycle**:
1. **Initialization**: `Window.initialize()` → UI element mapping
2. **Main Loop**: Continuous cycle of detect → decide → act
3. **Safety Monitoring**: Friend detection, error handling, progress tracking
4. **Cleanup**: Graceful shutdown and resource cleanup

**Visual Detection Chain**:
1. **Screenshot**: `window.game_view.screenshot()` captures current state
2. **Color Detection**: `clr.isolate_colors()` filters for target colors
3. **Object Extraction**: `rcv.extract_objects()` finds contours and shapes
4. **Validation**: Size, position, and context validation
5. **Sorting**: `distance_from_center()` prioritizes nearest objects

**API Integration Chain**:
1. **HTTP Polling**: `EventsAPI` or `MorgHTTPSocket` queries game state
2. **Data Processing**: Parse inventory, player status, world data
3. **State Caching**: Cache results to reduce API load
4. **Safety Checks**: Validate game state before actions

**Mouse Automation Chain**:
1. **Target Selection**: Choose click target from detection results
2. **Path Planning**: Generate human-like movement with Bezier curves
3. **Safety Validation**: Ensure target is valid and reachable
4. **Execution**: Perform click with randomization
5. **Confirmation**: Wait for action completion via API or visual feedback

### Error Handling and Recovery

**Visual Detection Failures**:
```
No Objects Found → Fallback Detection → Alternative Methods → Safe Wait
       ↓                ↓                    ↓               ↓
[empty list] → [different colors] → [image search] → [timeout]
```

**API Communication Failures**:
```
API Timeout → Retry Logic → Fallback to Visual → Continue or Stop
     ↓           ↓              ↓                    ↓
[exception] → [retry 3x] → [ocr fallback] → [graceful_degradation]
```

**Safety System Flow**:
```
Continuous Monitoring → Threat Detection → Safety Action → Recovery
        ↓                    ↓               ↓             ↓
[friends_nearby()] → [logout_trigger] → [safe_logout] → [session_end]
```

## Architecture Components

### 1. Core Application (OSBC.py)
**Purpose**: Main GUI application that manages bot discovery, configuration, and execution.

**Key Features**:
- Dynamic bot discovery via Python imports
- CustomTkinter-based UI with dark theme
- Bot lifecycle management (start/stop/configure)
- Settings management and keybind support
- Game selection and script organization

**Bot Discovery Process**:
1. Scans `model/` directory for Bot subclasses
2. Automatically creates UI buttons for each bot
3. Organizes bots by game title
4. Supports launchable games with rocket icons

### 2. Bot Framework

#### Abstract Bot Class (`model/bot.py`)
**Core Properties**:
- `game_title`: Game the bot targets
- `bot_title`: Display name in UI
- `description`: Bot functionality description
- `options_builder`: Dynamic options UI generator
- `win`: Window management object
- `mouse`: Mouse automation utility
- `thread`: BotThread for async execution

**Required Methods**:
- `main_loop()`: Core bot logic
- `create_options()`: Define bot configuration UI
- `save_options()`: Process user configuration

**Built-in Functionality**:
- Inventory management (drop_all, drop specific slots)
- Player status monitoring (HP, prayer, run energy)
- Combat detection and auto-retaliate control
- Camera and compass control
- Logout and break taking
- Progress tracking and logging

#### RuneLiteBot Extension (`model/runelite_bot.py`)
**Additional Features**:
- RuneLite-specific UI element detection
- Color-based object detection (cyan NPCs, purple loot)
- Advanced OCR for game text
- Contour-based object extraction
- Combat state detection
- Loot pickup automation

### 3. Window Management (`utilities/window.py`)

#### Window Class
**Responsibilities**:
- Game client window detection and focus
- UI element mapping and location
- Screenshot capture for specific regions
- Support for both fixed and resizable modes

**Key Regions Mapped**:
- `game_view`: Main game area
- `control_panel`: Inventory/spells/prayers panel
- `chat`: Chat area and tabs
- `minimap_area`: Minimap and orbs
- `inventory_slots`: 28 inventory slot rectangles
- `cp_tabs`: Control panel tabs (inventory, prayer, etc.)
- `prayers`: Prayer book slot rectangles
- `spellbook_normal`: Normal spellbook slot rectangles

#### RuneLiteWindow Extension
**Additional Features**:
- HP/Prayer bar tracking
- Current action text detection
- RuneLite-specific UI elements

### 4. Computer Vision & Image Processing

#### Image Search (`utilities/imagesearch.py`)
**Capabilities**:
- OpenCV-based template matching
- Transparency support for game sprites
- Confidence-based matching
- Rectangle-based search areas

#### Color Detection (`utilities/color.py`)
**Features**:
- Color isolation for object detection
- HSV color space operations
- Game-specific color constants
- Multi-color filtering

#### OCR (`utilities/ocr.py`)
**Functionality**:
- Custom bitmap font recognition
- Multiple font support (Plain11, Plain12, Bold12, Quill)
- Color-based text extraction
- Game text parsing and detection

### 5. Game State APIs

#### EventsAPI (`utilities/api/events_client.py`)
**Real-time Game Data**:
- Player stats (HP, prayer, run energy)
- Animation and idle detection
- Player position and world data
- Inventory state monitoring
- Combat detection
- Skill levels and XP tracking

#### MorgHTTPSocket (`utilities/api/morg_http_client.py`)
**HTTP-based Game Interface**:
- Inventory management
- Equipment detection
- Skill monitoring
- XP gain tracking
- Player position data

### 6. Automation Utilities

#### Mouse Control (`utilities/mouse.py`)
**Features**:
- Human-like movement with Bezier curves
- Configurable speed and patterns
- Click distribution randomization
- Movement boundary constraints

#### Geometry (`utilities/geometry.py`)
**Classes**:
- `Point`: 2D coordinate representation
- `Rectangle`: Screen region management
- `RuneLiteObject`: Game object representation with color detection

### 7. Bot Implementations

#### Example: NRMining (`model/near_reality/mining.py`)
**Functionality**:
- Rock detection via color tagging
- Inventory management (drop when full)
- Friend detection and logout
- Progress tracking
- API integration for game state

**Pattern**:
1. Configure options (runtime, logout behavior)
2. Initialize game state API
3. Main loop: detect → interact → wait → repeat
4. Handle edge cases (full inventory, friends nearby)
5. Update progress and log actions

### 8. Development Infrastructure

#### Type Checking
- **mypy**: Strict type checking configuration
- **Type hints**: Required for all functions
- **Runtime validation**: Type checking decorators

#### Code Quality
- **flake8**: Code linting
- **Automated formatting**: Black formatter configuration
- **Pre-commit hooks**: Quality gate enforcement

## Current Testing State

### Existing Tests
- `EventAPI_test.py`: Manual API testing script
- `morg_http_client.py`: HTTP client test functions
- No formal test framework or automated testing

### Testing Challenges
1. **Visual Testing**: Game state changes require screenshot comparison
2. **Timing Dependencies**: Game interactions have variable timing
3. **External Dependencies**: Requires running game client
4. **State Management**: Game state affects test outcomes

## Development Workflow

### Current Process
1. Create bot class inheriting from Bot/RuneLiteBot
2. Implement required methods (main_loop, create_options, save_options)
3. Test manually using GUI application
4. Debug using print statements and screenshots
5. Deploy by placing in appropriate model subdirectory

### Areas for Improvement
1. **Automated Testing**: No test framework for visual interactions
2. **Visual Debugging**: Ad-hoc screenshot debugging
3. **State Validation**: No systematic game state verification
4. **Regression Testing**: No automated regression detection
5. **API Testing**: Manual API testing only

## Dependencies and Libraries

### Core Dependencies
- **OpenCV**: Computer vision and image processing
- **PyAutoGUI**: Mouse and keyboard automation
- **CustomTkinter**: Modern GUI framework
- **Pillow**: Image manipulation
- **NumPy**: Numerical operations
- **Requests**: HTTP API communication

### Game-Specific Libraries
- **PyWinCtl**: Window management
- **MSS**: Fast screenshot capture
- **PyTweening**: Animation curves for mouse movement

## Configuration and Settings

### Settings Management
- **Pickle-based**: Settings stored in `settings.pickle`
- **JSON configs**: RuneLite settings in `runelite_settings/`
- **Keybind support**: Configurable hotkeys
- **Profile management**: Multiple game profiles

### Image Assets
- **Template images**: UI element detection templates
- **Bot-specific images**: Game object recognition sprites
- **Debug assets**: Screenshot storage for debugging

## Security and Safety

### Safety Features
- **Friend detection**: Automatic logout when friends nearby
- **Human-like patterns**: Randomized timing and movement
- **Break taking**: Configurable rest periods
- **Error handling**: Graceful degradation on failures

### Limitations
- **Detection-based**: Relies on visual detection, can break with UI changes
- **Timing-dependent**: Game lag can affect reliability
- **Manual configuration**: Requires user setup and marking
- **Game-specific**: Tied to specific game client versions

## Future Improvements

### Testing Infrastructure
- Automated visual testing framework
- Mock game client for testing
- Regression test suite
- Performance benchmarking

### Bot Development
- Bot template generator
- Visual bot designer
- Real-time debugging interface
- Performance profiling tools

### Framework Enhancements
- Plugin system for extensions
- Advanced AI decision making
- Multi-threading support
- Cloud-based bot management