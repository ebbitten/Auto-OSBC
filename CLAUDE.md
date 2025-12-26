
AI AGENT DEVELOPMENT ROADMAP (Auto-OSBC Game Automation)

Project Context:
Auto-OSBC is a sophisticated game automation framework for RuneScape-like games using computer vision, OCR, and mouse automation. The framework provides Bot/RuneLiteBot base classes, Window management, and comprehensive visual detection utilities. All development follows TDD principles adapted for visual game automation.

Required Reading:
- `docs/current-state.md` - Complete system architecture and component overview
- `docs/development-workflow.md` - Detailed TDD process for game automation
- `docs/testing-strategy.md` - Visual testing methodology and framework
- `docs/api-reference.md` - Bot framework APIs and utilities
- `docs/debugging-guide.md` - Visual debugging tools and techniques

## Available Scripts (USE THESE - Don't Write Inline Python!)

When interacting with the game or capturing data, USE these scripts instead of writing inline Python:

| Script | Purpose | Example |
|--------|---------|---------|
| `python scripts/recorder.py` | Capture screenshots, extract templates | `python scripts/recorder.py --window "RuneLite" --duration 5` |
| `python scripts/debug_console.py` | Interactive debugging | `python scripts/debug_console.py` |
| `python scripts/manual_capture.py` | Quick screenshot capture | `python scripts/manual_capture.py "description"` |
| `python scripts/performance_profiler.py` | Profile detection speed | `python scripts/performance_profiler.py` |

### Recorder Commands (Most Useful)
```bash
# List available templates
python scripts/recorder.py --list-templates

# Test if a template matches on screen
python scripts/recorder.py --test-template src/images/bot/login/existing_user_button.png --window "RuneLite"

# Capture screenshots from a window
python scripts/recorder.py --window "RuneLite" --duration 5 --interval 1000

# Extract a region as a new template
python scripts/recorder.py --from-session "captures/2025-..." --extract-template "X,Y,W,H,template_name"
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `osbc status` | Check if OSBC/RuneLite windows are running |
| `osbc start --headless` | Launch RuneLite via OSBC (no GUI) |
| `osbc start` | Launch RuneLite and open OSBC GUI |
| `osbc login` | Perform automated login on RuneLite |

## Mandatory TDD Workflow for Bot Development

### Pre-Implementation (REQUIRED):
1. **Architecture Understanding**: Read `docs/current-state.md` to understand Bot framework inheritance (Bot → RuneLiteBot → YourBot)
2. **API Familiarization**: Review `docs/api-reference.md` for available detection methods, game state APIs, and automation utilities
3. **Testing Strategy**: Study `docs/testing-strategy.md` for visual testing pyramid (Unit → Integration → Visual → E2E)
4. **Environment Setup**: Verify Python 3.10 venv, mypy configuration, and game client accessibility

### Development Sequence (6 Steps - MANDATORY):

**Step 1: Bot Specification**
- Create `tests/specs/{bot-name}.spec.md` following the template in `docs/development-workflow.md`
- Define bot inheritance pattern (Bot vs RuneLiteBot)
- Specify visual detection requirements (colors, OCR, image templates)
- Plan mouse interaction patterns and timing requirements
- Include edge cases (full inventory, friends nearby, detection failures)

**Step 2: Test Creation (Red Phase)**
Write failing tests following the actual test structure:
```python
# 1. Specifications (test requirements)
tests/specs/{bot_name}.spec.md

# 2. Unit tests (isolated components)
# Place in tests/ or create tests/unit/ if organizing by type

# 3. Integration tests (window management, visual detection)
tests/integration/test_{bot_name}_integration.py

# 4. Platform-specific tests (if needed)
tests/platform/test_{bot_name}_platform.py

# Note: Visual fixtures and E2E tests are planned for future implementation
# Current test organization: tests/api/, tests/integration/, tests/platform/,
# tests/dependencies/, tests/smoke/, tests/specs/, tests/tools/
```

**Key Testing Patterns**:
- Use `create_mock_bot_with_image()` for visual detection tests
- Test detection with `get_all_tagged_in_rect()` and color isolation
- Validate OCR with `ocr.extract_text()` and different fonts
- Test timing with animation detection and visual state changes
- Test visual inventory detection methods

**Step 3: Minimal Implementation (Green Phase)**
- Create bot class inheriting from appropriate base (Bot/RuneLiteBot)
- Implement required abstract methods: `main_loop()`, `create_options()`, `save_options()`
- Use existing framework APIs: color detection, OCR, window management, mouse automation
- Use visual detection methods for game state monitoring (inventory, idle, combat)
- Write minimal code to pass tests (resist over-engineering)

**Bot Development Pattern**:
```python
class YourBot(RuneLiteBot):
    def __init__(self):
        super().__init__(
            game_title="Game Name",
            bot_title="Bot Name", 
            description="Bot description"
        )
        # Bot-specific properties
    
    def create_options(self):
        # Use self.options_builder for UI generation
    
    def save_options(self, options: dict):
        # Process user configuration
        self.options_set = True
    
    def main_loop(self):
        # Core automation logic with:
        # - Visual detection (get_all_tagged_in_rect, color isolation)
        # - Game state checking (is_inventory_full_visual, is_player_idle_visual)
        # - Mouse automation (self.mouse.move_to, click)
        # - Progress tracking (update_progress)
        # - Error handling and logging
```

**Step 4: Regression Testing**
- Run complete test suite: `pytest tests/ -v`
- Execute visual regression tests: `python tests/tools/visual_regression.py`
- Verify no existing functionality broken
- Update reference images if game UI changed (with justification)

**Step 5: Refactoring (Blue Phase)**
- Optimize detection algorithms for performance (< 100ms target)
- Add error handling and retry logic
- Implement caching for expensive operations
- Extract reusable patterns to utilities
- Add performance monitoring and logging
- **Requirement**: All tests must continue passing

**Step 6: Documentation & Integration**
- Update `docs/current-state.md` with new bot capabilities
- Document any new detection patterns or API usage
- Add performance benchmarks and known limitations
- Create debug capture examples in `docs/debugging-guide.md`

## Game Automation Specific Guidelines

### Visual Detection Standards:
- **Colors**: Use framework constants (`clr.CYAN`, `clr.PINK`, `clr.PURPLE`) 
- **Detection**: Target < 100ms for `get_all_tagged_in_rect()` calls
- **Validation**: Always validate detection results (size, position, count)
- **Fallbacks**: Implement alternative detection methods for reliability

### Visual Detection Requirements:
- **Game State**: Use visual detection methods for all game state monitoring
- **Inventory**: Check `is_inventory_full_visual()` before actions that generate items
- **Player Status**: Monitor `is_player_idle_visual()` for action completion
- **Safety**: Implement friend detection (`friends_nearby()`) for logout safety
- **Item Counting**: Use `count_inventory_items_visual()` to track inventory changes

### Mouse Automation Standards:
- **Movement**: Use human-like curves with `self.mouse.move_to(point, mouseSpeed="medium")`
- **Targeting**: Use `random_point()` on Rectangle objects for click variation
- **Timing**: Add appropriate delays between actions (`time.sleep(1)`)
- **Precision**: Validate click targets are within game view bounds

## Quality Gates (ENFORCED):

### Code Quality:
```bash
# Type checking (REQUIRED)
mypy src/

# Linting (REQUIRED)  
flake8 src/

# Test execution (REQUIRED)
pytest tests/ --cov=src --cov-report=html

# Performance validation (REQUIRED)
python scripts/performance_benchmark.py
```

### Visual Testing Requirements:
- **Unit tests**: > 80% coverage for bot logic
- **Visual tests**: Detection accuracy > 95% with test fixtures
- **Performance**: Detection operations < 100ms average
- **Regression**: No degradation in existing visual detection

### Integration Requirements:
- **Visual detection**: All game state detection uses visual methods
- **Error handling**: Graceful degradation on detection failures
- **Safety features**: Friend detection and logout mechanisms tested
- **Progress tracking**: Accurate progress reporting throughout execution

## Development Tools & Debugging:

### Visual Debugging Tools:
```bash
# Interactive debug console
python scripts/debug_console.py

# Manual screenshot capture
python scripts/manual_capture.py "description"

# Visual regression testing
python tests/tools/visual_regression.py

# Performance profiling
python scripts/performance_profiler.py
```

### Debug Workflow:
1. **Enable debug mode**: Set `bot.debug_mode = True`
2. **Capture screenshots**: Use `DebugCapture` for systematic screenshot collection
3. **Analyze detection**: Use `DetectionDebugger` for visual analysis
4. **Profile performance**: Use `PerformanceDebugger` for timing analysis
5. **Generate reports**: Automated debug reports after sessions

## Framework Integration Patterns:

### Bot Inheritance Decision:
- **Use Bot**: For simple automation not requiring RuneLite-specific features
- **Use RuneLiteBot**: For games with color-tagged objects, OCR text, and contour detection

### Common Implementation Patterns:
```python
# Object detection pattern
tagged_objects = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
if tagged_objects:
    nearest = sorted(tagged_objects, key=RuneLiteObject.distance_from_rect_center)[0]
    self.mouse.move_to(nearest.random_point())
    self.mouse.click()

# Inventory management pattern
if self.is_inventory_full_visual():
    self.drop_all(skip_slots=[0])  # Keep item in first slot

# Safety pattern
if self.logout_on_friends and self.friends_nearby():
    self.logout()
    self.stop()

# Progress tracking pattern
self.update_progress((time.time() - start_time) / total_time)
```

## Testing Command Reference:

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories (actual structure)
pytest tests/platform/ -v          # Platform detection tests
pytest tests/dependencies/ -v      # Import dependency tests
pytest tests/integration/ -v       # Integration tests (window, screenshot)
pytest tests/api/ -v               # API integration tests
pytest tests/smoke/ -v             # Installation smoke tests

# Run tests by marker
pytest tests/ -m "not slow" -v     # Skip slow tests
pytest tests/ -m integration -v    # Integration tests only
pytest tests/ -m unit -v           # Unit tests only

# Full test suite with coverage
pytest tests/ -v --cov=src --cov-report=html

# Type checking
mypy src/ --strict

# Visual regression
python tests/tools/visual_regression.py
```

## Forbidden Actions (STRICTLY ENFORCED):

❌ **Never commit failing tests** (any category: unit, visual, integration, e2e)
❌ **Never bypass visual regression checks** without documented UI changes
❌ **Never implement bots without comprehensive test coverage** (minimum 80%)
❌ **Never use hardcoded coordinates** instead of proper detection
❌ **Never skip API integration testing** with mocked responses
❌ **Never deploy without performance validation** (detection speed requirements)
❌ **Never commit without updating documentation** (`docs/current-state.md`)

## Success Criteria:

✅ **All tests pass**: Unit, integration, visual, and limited e2e tests
✅ **Performance targets met**: < 100ms detection, < 2GB memory usage
✅ **Type checking passes**: `mypy src/` with no errors
✅ **Visual regression passes**: No unintended UI detection changes
✅ **Documentation updated**: Architecture and API usage documented
✅ **Manual validation**: Bot operates correctly in actual game environment
✅ **Safety features tested**: Friend detection, error handling, graceful degradation

Remember: This framework prioritizes reliable, maintainable game automation through comprehensive testing, performance optimization, and safety features. Every bot must integrate seamlessly with the existing architecture while maintaining the highest standards of code quality and visual detection accuracy.
