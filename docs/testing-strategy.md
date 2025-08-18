# Visual Testing Strategy for Game Automation

## Overview
Testing game automation requires specialized approaches due to the visual, timing-dependent, and interactive nature of game clients. This document outlines comprehensive testing strategies for Auto-OSBC bot development.

## Testing Pyramid for Game Automation

### 1. Unit Tests (Foundation)
**Purpose**: Test individual components in isolation
**Scope**: Utilities, calculations, data processing
**Tools**: PyTest, unittest

**Examples**:
- Color detection algorithms
- Geometry calculations (Point, Rectangle operations)
- OCR text extraction
- API response parsing
- Mouse movement calculations

**Implementation**:
```python
# test_geometry.py
def test_rectangle_center():
    rect = Rectangle(10, 10, 100, 100)
    center = rect.get_center()
    assert center.x == 60
    assert center.y == 60

def test_color_isolation():
    # Test with known color patterns
    test_image = create_test_image_with_colors()
    isolated = clr.isolate_colors(test_image, [clr.CYAN])
    assert isolated is not None
```

### 2. Integration Tests (Core)
**Purpose**: Test component interactions without full game client
**Scope**: API integration, window management, image processing
**Tools**: PyTest with mocking

**Examples**:
- API client responses
- Window initialization without game
- Image search algorithms
- OCR with test images
- Mouse automation patterns

**Implementation**:
```python
# test_api_integration.py
def test_events_api_inventory():
    # Mock the HTTP response
    mock_response = {"inventory": [{"id": 1355, "quantity": 1}]}
    with patch('requests.get', return_value=mock_response):
        client = EventsAPIClient()
        inventory = client.get_inv()
        assert len(inventory) == 1
        assert inventory[0]["id"] == 1355
```

### 3. Visual Tests (Specialized)
**Purpose**: Test visual detection and interaction with game elements
**Scope**: Screenshot comparison, object detection, UI element recognition
**Tools**: PyTest + OpenCV + Custom framework

**Key Challenges**:
- Game state variability
- Timing dependencies
- Visual element changes
- Screen resolution differences

**Implementation Approaches**:

#### A. Screenshot Comparison Testing
```python
# test_visual_detection.py
def test_inventory_slot_detection():
    # Load reference screenshot
    reference = cv2.imread("tests/fixtures/inventory_full.png")
    
    # Test inventory detection
    bot = create_test_bot()
    bot.win.initialize_from_image(reference)
    
    # Verify all 28 slots are detected
    assert len(bot.win.inventory_slots) == 28
    
    # Test first slot position
    first_slot = bot.win.inventory_slots[0]
    expected_pos = Point(40, 44)  # Relative to control panel
    assert abs(first_slot.left - expected_pos.x) < 5
```

#### B. Object Detection Testing
```python
def test_npc_detection():
    # Load test image with tagged NPCs
    test_image = cv2.imread("tests/fixtures/npcs_tagged.png")
    
    bot = create_test_bot()
    # Mock the screenshot method
    bot.win.game_view.screenshot = lambda: test_image
    
    # Test NPC detection
    npcs = bot.get_all_tagged_in_rect(bot.win.game_view, clr.CYAN)
    assert len(npcs) > 0
    assert all(isinstance(npc, RuneLiteObject) for npc in npcs)
```

#### C. OCR Testing
```python
def test_hp_ocr():
    # Load test image with HP text
    hp_image = cv2.imread("tests/fixtures/hp_orb_99.png")
    
    # Test OCR extraction
    hp_text = ocr.extract_text(hp_image, ocr.PLAIN_11, [clr.ORB_GREEN])
    assert "99" in hp_text
```

### 4. End-to-End Tests (Limited)
**Purpose**: Test complete bot workflows with game client
**Scope**: Full bot execution, game interaction, state management
**Tools**: PyTest + Game client automation

**Implementation**:
```python
# test_mining_bot_e2e.py
@pytest.mark.slow
@pytest.mark.requires_game_client
def test_mining_bot_basic_workflow():
    # Setup test environment
    bot = NRMining()
    bot.save_options({"running_time": 1, "logout_on_friends": "No"})
    
    # Start bot and run for short duration
    bot.play()
    time.sleep(60)  # Run for 1 minute
    bot.stop()
    
    # Verify bot executed without errors
    assert bot.status == BotStatus.STOPPED
    # Additional assertions based on expected behavior
```

## Visual Testing Framework Design

### 1. Test Image Management
**Structure**:
```
tests/
├── fixtures/
│   ├── screenshots/
│   │   ├── inventory_full.png
│   │   ├── inventory_empty.png
│   │   └── game_view_mining.png
│   ├── ui_elements/
│   │   ├── hp_orb_99.png
│   │   ├── prayer_orb_43.png
│   │   └── minimap_north.png
│   └── reference_images/
│       ├── mining_rock_tagged.png
│       └── bank_interface.png
```

**Image Versioning**: 
- Use game version in filename: `inventory_full_v1.2.3.png`
- Separate by resolution: `1080p/`, `720p/`
- Include metadata: `image_metadata.json`

### 2. Mock Game Client
**Purpose**: Enable testing without running actual game
**Components**:
- Mock Window class that loads from screenshots
- Simulated mouse interactions
- Fake API responses
- Controlled timing

**Implementation**:
```python
class MockGameClient:
    def __init__(self, scenario_name: str):
        self.scenario = load_test_scenario(scenario_name)
        self.current_frame = 0
        
    def get_screenshot(self) -> np.ndarray:
        return self.scenario.frames[self.current_frame]
    
    def simulate_click(self, point: Point):
        # Update scenario state based on click
        self.scenario.handle_click(point)
        self.current_frame += 1
```

### 3. Visual Regression Testing
**Purpose**: Detect when UI changes break bot functionality
**Approach**:
1. Capture reference images during known-good states
2. Compare current detection with reference
3. Alert on significant differences

**Implementation**:
```python
def test_visual_regression():
    # Load reference detection results
    reference_npcs = load_reference_detection("npcs_mining_area.json")
    
    # Current detection
    current_npcs = bot.get_all_tagged_in_rect(bot.win.game_view, clr.CYAN)
    
    # Compare results
    assert len(current_npcs) == len(reference_npcs)
    for current, reference in zip(current_npcs, reference_npcs):
        assert current.distance_to(reference) < 10  # pixels
```

## Test Data Management

### 1. Test Scenarios
**Structure**:
```python
# tests/scenarios/mining_scenario.py
class MiningScenario:
    def __init__(self):
        self.initial_state = {
            "inventory": "empty",
            "location": "mining_area",
            "rocks_available": 3,
            "character_position": Point(100, 100)
        }
        
    def frames(self):
        return [
            "mining_start.png",
            "mining_in_progress.png",
            "mining_complete.png",
            "inventory_full.png"
        ]
```

### 2. Game State Simulation
**Purpose**: Simulate game state changes for testing
**Implementation**:
```python
class GameStateSimulator:
    def __init__(self):
        self.inventory = [{"id": -1, "quantity": 0}] * 28
        self.player_hp = 99
        self.animation_id = 808  # Idle
        
    def mine_rock(self):
        # Simulate mining animation
        self.animation_id = 625  # Mining animation
        time.sleep(2)  # Mining duration
        
        # Add ore to inventory
        first_empty = next(i for i, item in enumerate(self.inventory) if item["id"] == -1)
        self.inventory[first_empty] = {"id": 1355, "quantity": 1}
        
        self.animation_id = 808  # Back to idle
```

## Test Execution Framework

### 1. Test Categories
**Fast Tests** (< 1 second):
- Unit tests
- Mock-based integration tests
- Static image analysis

**Medium Tests** (1-10 seconds):
- Visual detection with test images
- API integration tests
- Screenshot comparison

**Slow Tests** (> 10 seconds):
- End-to-end with game client
- Performance benchmarks
- Long-running scenarios

### 2. Test Configuration
```python
# pytest.ini
[tool:pytest]
markers =
    fast: marks tests as fast (< 1s)
    medium: marks tests as medium (1-10s)
    slow: marks tests as slow (> 10s)
    requires_game_client: marks tests requiring game client
    visual: marks tests that use visual detection
    api: marks tests that use game APIs
```

### 3. Continuous Integration
**Test Stages**:
1. **Fast Tests**: Run on every commit
2. **Medium Tests**: Run on pull requests
3. **Slow Tests**: Run nightly
4. **Visual Regression**: Run on UI changes

## Visual Testing Best Practices

### 1. Test Image Quality
- Use consistent resolution (1080p recommended)
- Capture in consistent lighting conditions
- Include various game states (day/night, different areas)
- Update images when game client updates

### 2. Timing Considerations
- Account for game tick timing (0.6s intervals)
- Add appropriate waits for animations
- Test with various latency conditions
- Use polling for state changes

### 3. Error Handling
- Test with corrupted/partial screenshots
- Handle missing UI elements gracefully
- Test with different window sizes
- Verify behavior with game client crashes

### 4. Performance Testing
- Measure detection speed (target: < 100ms)
- Test with high CPU load
- Monitor memory usage during long runs
- Benchmark against reference implementations

## Tools and Utilities

### 1. Visual Test Generator
```python
# generate_visual_test.py
def generate_test_from_recording():
    """Generate test cases from recorded bot sessions"""
    recording = load_bot_recording("mining_session.json")
    
    # Extract key frames
    key_frames = extract_decision_points(recording)
    
    # Generate test cases
    for frame in key_frames:
        generate_test_case(frame)
```

### 2. Screenshot Comparison Tools
```python
# visual_diff.py
def compare_screenshots(reference_path: str, current_path: str) -> float:
    """Compare screenshots and return similarity score"""
    ref_img = cv2.imread(reference_path)
    cur_img = cv2.imread(current_path)
    
    # Structural similarity
    similarity = ssim(ref_img, cur_img, multichannel=True)
    return similarity
```

### 3. Test Data Factory
```python
# test_data_factory.py
class TestDataFactory:
    @staticmethod
    def create_full_inventory():
        return [{"id": 1355, "quantity": 1}] * 28
    
    @staticmethod
    def create_mining_scenario():
        return {
            "game_state": "mining_area",
            "inventory": TestDataFactory.create_empty_inventory(),
            "npcs": [create_test_npc("Rock", Point(100, 100))]
        }
```

## Debugging Visual Tests

### 1. Debug Screenshots
- Capture screenshots at each test step
- Save intermediate processing results
- Include detection overlays
- Store in organized debug folder

### 2. Test Failure Analysis
- Compare expected vs actual detection
- Analyze timing issues
- Check for UI element changes
- Review game state consistency

### 3. Performance Profiling
- Profile detection algorithms
- Measure screenshot capture speed
- Monitor memory usage
- Identify bottlenecks

## Integration with Development Workflow

### 1. TDD for Visual Features
1. **Write failing visual test** with expected detection
2. **Implement minimum detection** to pass test
3. **Refactor and optimize** detection algorithm
4. **Add edge case tests** for robustness

### 2. Pre-commit Hooks
- Run fast visual tests
- Check for test image updates
- Validate detection performance
- Ensure consistent formatting

### 3. Documentation Updates
- Update test documentation with new features
- Maintain test image catalog
- Document known issues and workarounds
- Keep performance benchmarks current