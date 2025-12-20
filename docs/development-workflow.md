# TDD Development Workflow for Game Automation

## Overview
This document outlines the Test-Driven Development (TDD) process specifically adapted for game automation development in Auto-OSBC. The workflow integrates visual testing, API mocking, and game client interaction patterns.

## Pre-Development Setup

### 1. Environment Preparation
**Required Tools**:
- Python 3.10 virtual environment
- Game client (RuneLite) for testing
- Visual testing framework
- API testing tools

**Setup Commands**:

Use the automated installation scripts:

```bash
# Windows
install-windows.bat

# Ubuntu/Linux
./install-ubuntu.sh

# Cross-platform (Python)
python install.py
```

These scripts automatically:
- Detect/install Python 3.10
- Install UV package manager (10-100x faster than pip)
- Create virtual environment
- Install all dependencies from `pyproject.toml`

**Manual Installation** (if automated scripts fail):
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install all dependencies (includes dev/testing tools)
pip install -e ".[dev]"
```

### 2. Documentation Review
**Required Reading**:
1. `docs/current-state.md` - Understand system architecture
2. `docs/testing-strategy.md` - Learn visual testing approaches
3. `docs/api-reference.md` - Review available APIs
4. `docs/debugging-guide.md` - Debug tools and techniques

### 3. Development Environment Validation
```bash
# Verify type checking
mypy src/

# Run existing tests
pytest tests/ -v

# Test game client connection
pytest tests/ -v  # Run test suite
```

## TDD Workflow for Game Automation

### Phase 1: Feature Specification

#### Step 1: Create Feature Specification
**Location**: `tests/specs/{feature-name}.spec.md`

**Template**:
```markdown
# Feature: {Feature Name}

## Objective
Clear description of what the feature should accomplish.

## Acceptance Criteria
- [ ] Criterion 1: Specific, measurable outcome
- [ ] Criterion 2: Visual detection requirement
- [ ] Criterion 3: API integration requirement
- [ ] Criterion 4: Error handling behavior

## Visual Requirements
- **Detection targets**: What visual elements to find
- **Color requirements**: Specific colors to isolate
- **OCR requirements**: Text to extract
- **Screenshot fixtures**: Required test images

## API Integration
- **Required endpoints**: StatusSocket methods
- **Game state dependencies**: Required game conditions
- **Timing constraints**: Response time requirements

## Game Client Setup
- **Prerequisites**: Required game state
- **Manual setup**: Player positioning, inventory setup
- **Test environment**: Specific game area or conditions

## Edge Cases
- **Visual variations**: Different lighting, zoom levels
- **Timing issues**: Lag, animation delays
- **Error conditions**: Missing elements, API failures
```

#### Step 2: Test Data Preparation
**Create Test Assets**:
```bash
# Actual test directory structure:
# tests/
# ├── api/           # API integration tests
# ├── dependencies/  # Import dependency tests
# ├── integration/   # Integration tests (window, screenshot)
# ├── platform/      # Platform detection tests
# ├── smoke/         # Installation smoke tests
# ├── specs/         # Bot specifications
# └── tools/         # Testing utilities (visual_regression.py)
```

**Capture Test Images**:
```python
# scripts/capture_test_images.py
def capture_feature_images(feature_name: str):
    """Capture screenshots for feature testing"""
    bot = create_test_bot()
    
    # Capture initial state
    initial_screenshot = bot.win.game_view.screenshot()
    cv2.imwrite(f"tests/fixtures/{feature_name}/initial_state.png", initial_screenshot)
    
    # Capture target detection
    target_screenshot = bot.win.game_view.screenshot()
    cv2.imwrite(f"tests/fixtures/{feature_name}/target_detected.png", target_screenshot)
    
    # Capture completion state
    completion_screenshot = bot.win.game_view.screenshot()
    cv2.imwrite(f"tests/fixtures/{feature_name}/completion_state.png", completion_screenshot)
```

### Phase 2: Test Creation (Red Phase)

#### Step 3: Write Failing Unit Tests
**Focus**: Individual components without game client

```python
# tests/unit/test_{feature}_unit.py
import pytest
from unittest.mock import Mock, patch
from src.model.your_bot import YourBot

class TestYourBotUnit:
    def test_color_detection_algorithm(self):
        """Test color detection without game client"""
        # Create test image with known colors
        test_image = create_test_image_with_colors()
        
        # Test color isolation
        result = isolate_target_colors(test_image)
        
        # Verify expected colors found
        assert len(result) > 0
        assert result[0].color == expected_color
    
    def test_inventory_management_logic(self):
        """Test inventory logic with mocked data"""
        mock_inventory = [{"id": 1355, "quantity": 1}] * 28
        
        bot = YourBot()
        result = bot.should_drop_inventory(mock_inventory)
        
        assert result == True
    
    def test_game_state_decision_making(self):
        """Test decision logic with mocked game state"""
        mock_game_state = {
            "player_idle": True,
            "inventory_full": False,
            "target_available": True
        }
        
        bot = YourBot()
        next_action = bot.determine_next_action(mock_game_state)
        
        assert next_action == "interact_with_target"
```

#### Step 4: Write Failing Integration Tests
**Focus**: Component interactions with mocked game client

```python
# tests/integration/test_{feature}_integration.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.model.your_bot import YourBot

class TestYourBotIntegration:
    def test_api_integration(self):
        """Test API integration with mocked responses"""
        mock_api_response = {
            "inventory": [{"id": -1, "quantity": 0}] * 28,
            "animation": 808,  # Idle
            "health": "99/99"
        }
        
        with patch('src.utilities.api.status_socket.StatusSocket') as mock_client:
            mock_client.return_value.get_inv.return_value = mock_api_response["inventory"]
            mock_client.return_value.get_is_player_idle.return_value = True
            
            bot = YourBot()
            bot.api_client = mock_client.return_value
            
            # Test API usage
            result = bot.check_ready_for_action()
            assert result == True
    
    def test_window_interaction(self):
        """Test window interaction with mock window"""
        mock_window = create_mock_window()
        
        bot = YourBot()
        bot.win = mock_window
        
        # Test window method calls
        bot.click_inventory_slot(0)
        
        mock_window.inventory_slots[0].random_point.assert_called_once()
```

#### Step 5: Write Failing Visual Tests
**Focus**: Visual detection with test images

```python
# tests/visual/test_{feature}_visual.py
import pytest
import cv2
from src.model.your_bot import YourBot
from tests.helpers.visual_test_helpers import create_mock_bot_with_image

class TestYourBotVisual:
    def test_target_detection_with_test_image(self):
        """Test visual target detection"""
        # Load test image
        test_image = cv2.imread("tests/fixtures/your_feature/target_present.png")
        
        # Create bot with mock window
        bot = create_mock_bot_with_image(test_image)
        
        # Test detection
        targets = bot.find_targets()
        
        # Verify detection
        assert len(targets) > 0
        assert targets[0].color == expected_color
        assert targets[0].distance_from_center < 100
    
    def test_ocr_extraction(self):
        """Test OCR text extraction"""
        test_image = cv2.imread("tests/fixtures/your_feature/text_sample.png")
        
        # Test OCR
        extracted_text = ocr.extract_text(test_image, ocr.PLAIN_11, [clr.WHITE])
        
        # Verify text extraction
        assert "Expected Text" in extracted_text
    
    def test_ui_element_detection(self):
        """Test UI element detection"""
        test_image = cv2.imread("tests/fixtures/your_feature/ui_state.png")
        
        bot = create_mock_bot_with_image(test_image)
        
        # Test UI element finding
        element = bot.find_ui_element("target_button")
        
        assert element is not None
        assert element.width > 0
        assert element.height > 0
```

#### Step 6: Write Failing End-to-End Tests
**Focus**: Complete workflow with game client (limited)

```python
# tests/e2e/test_{feature}_e2e.py
import pytest
import time
from src.model.your_bot import YourBot

@pytest.mark.slow
@pytest.mark.requires_game_client
class TestYourBotE2E:
    def test_complete_workflow(self):
        """Test complete bot workflow with game client"""
        # Setup bot
        bot = YourBot()
        bot.save_options({"running_time": 1, "test_mode": True})
        
        # Verify initial state
        assert bot.status == BotStatus.STOPPED
        
        # Start bot
        bot.play()
        
        # Allow execution
        time.sleep(30)  # Run for 30 seconds
        
        # Stop bot
        bot.stop()
        
        # Verify completion
        assert bot.status == BotStatus.STOPPED
        # Additional assertions based on expected behavior
```

### Phase 3: Implementation (Green Phase)

#### Step 7: Implement Minimum Code to Pass Tests
**Principle**: Write the simplest code that makes tests pass

```python
# src/model/your_bot.py
from model.runelite_bot import RuneLiteBot
import utilities.color as clr
from utilities.geometry import RuneLiteObject
from typing import List

class YourBot(RuneLiteBot):
    def __init__(self):
        super().__init__(
            game_title="Your Game",
            bot_title="Your Bot",
            description="Bot description"
        )
        self.running_time = 1
        self.test_mode = False
    
    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 360)
        self.options_builder.add_checkbox_option("test_mode", "Test mode", ["Yes", "No"])
    
    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "test_mode":
                self.test_mode = options[option] == "Yes"
        self.options_set = True
    
    def main_loop(self):
        """Main bot logic - implement minimum functionality"""
        start_time = time.time()
        end_time = self.running_time * 60
        
        while time.time() - start_time < end_time:
            # Implement core logic step by step
            if self.should_perform_action():
                self.perform_action()
            
            time.sleep(1)  # Basic timing
    
    def should_perform_action(self) -> bool:
        """Determine if bot should act - implement to pass tests"""
        # Start with simple logic
        return True
    
    def perform_action(self):
        """Perform bot action - implement to pass tests"""
        # Minimal implementation
        self.log_msg("Performing action...")
    
    def find_targets(self) -> List[RuneLiteObject]:
        """Find visual targets - implement to pass visual tests"""
        # Minimal detection
        return self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
```

#### Step 8: Verify Tests Pass
```bash
# Run unit tests
pytest tests/unit/test_your_feature_unit.py -v

# Run integration tests  
pytest tests/integration/test_your_feature_integration.py -v

# Run visual tests
pytest tests/visual/test_your_feature_visual.py -v

# Run all tests for feature
pytest tests/ -k "your_feature" -v
```

### Phase 4: Refactoring (Blue Phase)

#### Step 9: Refactor for Quality
**Focus**: Improve code quality while maintaining test passage

**Areas for Improvement**:
1. **Performance**: Optimize detection algorithms
2. **Reliability**: Add error handling and retries
3. **Maintainability**: Extract common patterns
4. **Extensibility**: Design for future features

```python
# Refactored implementation
class YourBot(RuneLiteBot):
    def __init__(self):
        super().__init__(
            game_title="Your Game",
            bot_title="Your Bot",
            description="Bot description"
        )
        self.running_time = 1
        self.test_mode = False
        self.performance_metrics = {}
    
    def find_targets(self) -> List[RuneLiteObject]:
        """Optimized target detection"""
        start_time = time.time()
        
        # Improved detection with caching
        if hasattr(self, '_cached_targets') and self._should_use_cache():
            return self._cached_targets
        
        # Enhanced detection algorithm
        targets = self._detect_targets_with_validation()
        
        # Cache results
        self._cached_targets = targets
        self._cache_time = time.time()
        
        # Performance tracking
        detection_time = time.time() - start_time
        self.performance_metrics['detection_time'] = detection_time
        
        return targets
    
    def _detect_targets_with_validation(self) -> List[RuneLiteObject]:
        """Enhanced detection with validation"""
        # Multiple detection methods
        primary_targets = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
        
        # Validate detections
        valid_targets = [t for t in primary_targets if self._validate_target(t)]
        
        # Fallback detection if needed
        if not valid_targets:
            valid_targets = self._fallback_detection()
        
        return valid_targets
    
    def _validate_target(self, target: RuneLiteObject) -> bool:
        """Validate target detection"""
        # Size validation
        if target.width < 10 or target.height < 10:
            return False
        
        # Position validation
        if not self.win.game_view.contains_point(target.get_center()):
            return False
        
        return True
```

#### Step 10: Add Comprehensive Tests
**Focus**: Test edge cases and error conditions

```python
# Additional tests after refactoring
def test_target_detection_edge_cases(self):
    """Test edge cases in target detection"""
    # Empty image
    empty_image = np.zeros((100, 100, 3), dtype=np.uint8)
    bot = create_mock_bot_with_image(empty_image)
    targets = bot.find_targets()
    assert len(targets) == 0
    
    # Corrupted image
    corrupted_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    bot = create_mock_bot_with_image(corrupted_image)
    targets = bot.find_targets()
    assert isinstance(targets, list)  # Should not crash
    
    # Multiple targets
    multi_target_image = cv2.imread("tests/fixtures/multiple_targets.png")
    bot = create_mock_bot_with_image(multi_target_image)
    targets = bot.find_targets()
    assert len(targets) > 1
    
def test_performance_requirements(self):
    """Test performance requirements"""
    test_image = cv2.imread("tests/fixtures/standard_game_view.png")
    bot = create_mock_bot_with_image(test_image)
    
    start_time = time.time()
    targets = bot.find_targets()
    detection_time = time.time() - start_time
    
    # Performance requirement: < 100ms
    assert detection_time < 0.1
```

### Phase 5: Integration and Validation

#### Step 11: Integration Testing
**Focus**: Test with other system components

```python
# Integration with existing bots
def test_integration_with_existing_bots(self):
    """Test integration with other bot components"""
    # Test with inventory management
    bot = YourBot()
    bot.win = create_mock_window()
    
    # Simulate full inventory
    mock_full_inventory = [{"id": 1355, "quantity": 1}] * 28
    with patch.object(bot, 'api_client') as mock_api:
        mock_api.get_inv.return_value = mock_full_inventory
        mock_api.get_is_inv_full.return_value = True
        
        # Test inventory handling
        result = bot.handle_full_inventory()
        assert result == True
```

#### Step 12: Documentation Update
**Update**: `docs/current-state.md`

```markdown
## New Feature: {Feature Name}

### Overview
Description of the new feature and its integration.

### Implementation Details
- **Detection Method**: How visual detection works
- **API Integration**: Which APIs are used
- **Performance**: Benchmarks and optimization

### Testing Coverage
- **Unit Tests**: X tests covering core logic
- **Integration Tests**: Y tests covering API integration  
- **Visual Tests**: Z tests covering detection
- **E2E Tests**: W tests covering full workflow

### Known Limitations
- List any current limitations
- Performance considerations
- Future improvement areas
```

### Phase 6: Quality Assurance

#### Step 13: Run Complete Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run performance tests
pytest tests/ -m "performance" -v

# Run slow tests
pytest tests/ -m "slow" -v
```

#### Step 14: Type Checking and Linting
```bash
# Type checking
mypy src/

# Code linting
flake8 src/

# Format check
black --check src/
```

#### Step 15: Manual Testing
**Required Steps**:
1. **Setup game client** in appropriate state
2. **Configure bot** with test options
3. **Run bot** for validation period
4. **Observe behavior** and verify expectations
5. **Document results** in test log

**Test Log Template**:
```
## Manual Test Session: {Feature Name}
**Date**: {Date}
**Tester**: {Name}
**Game Client**: {Version}
**Test Duration**: {Duration}

### Test Results
- [ ] Feature works as expected
- [ ] No unexpected errors
- [ ] Performance acceptable
- [ ] Visual detection reliable

### Issues Found
- Issue 1: Description and severity
- Issue 2: Description and severity

### Recommendations
- Recommendation 1
- Recommendation 2
```

## Best Practices for TDD Game Automation

### 1. Test Isolation
- Each test should be independent
- Use fresh game state for each test
- Mock external dependencies
- Clean up test artifacts

### 2. Test Data Management
- Version control test images
- Use consistent image formats
- Document test data requirements
- Automate test data generation

### 3. Performance Considerations
- Target detection times < 100ms
- Minimize screenshot operations
- Cache detection results appropriately
- Profile performance regularly

### 4. Error Handling
- Test failure scenarios
- Handle API timeouts gracefully
- Validate visual detection results
- Provide meaningful error messages

### 5. Maintainability
- Use descriptive test names
- Document test purposes
- Keep tests simple and focused
- Refactor tests with implementation

## Workflow Integration

### 1. Development Cycle
1. **Feature Planning**: Create specification
2. **Test Creation**: Write failing tests
3. **Implementation**: Write minimal code
4. **Refactoring**: Improve quality
5. **Integration**: Test with system
6. **Documentation**: Update docs
7. **Review**: Code review and validation

### 2. Continuous Integration
- Run fast tests on every commit
- Run full test suite on pull requests
- Run performance tests nightly
- Update test baselines regularly

### 3. Quality Gates
- All tests must pass
- Code coverage > 80%
- Performance benchmarks met
- Type checking passes
- Manual validation completed

### 4. Release Process
- Feature branch testing
- Integration testing
- Performance validation
- Documentation updates
- Deployment verification