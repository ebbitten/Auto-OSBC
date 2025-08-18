
AI AGENT DEVELOPMENT ROADMAP (Auto-OSBC Game Automation)

Project Context:  
Auto-OSBC is a sophisticated game automation framework for RuneScape-like games using computer vision, OCR, HTTP APIs, and mouse automation. The framework provides Bot/RuneLiteBot base classes, Window management, EventsAPI/MorgHTTPSocket game state APIs, and comprehensive visual detection utilities. All development follows TDD principles adapted for visual game automation.

Required Reading:
- `docs/current-state.md` - Complete system architecture and component overview
- `docs/development-workflow.md` - Detailed TDD process for game automation
- `docs/testing-strategy.md` - Visual testing methodology and framework
- `docs/api-reference.md` - Bot framework APIs and utilities
- `docs/debugging-guide.md` - Visual debugging tools and techniques

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
- Document API integration needs (EventsAPI vs MorgHTTPSocket)
- Plan mouse interaction patterns and timing requirements
- Include edge cases (full inventory, friends nearby, API failures)

**Step 2: Test Creation (Red Phase)**
Write failing tests in this order:
```python
# 1. Unit tests (isolated components)
tests/unit/test_{bot_name}_unit.py

# 2. Integration tests (API mocking)  
tests/integration/test_{bot_name}_integration.py

# 3. Visual tests (screenshot fixtures)
tests/visual/test_{bot_name}_visual.py

# 4. E2E tests (actual game client - limited)
tests/e2e/test_{bot_name}_e2e.py
```

**Key Testing Patterns**:
- Mock EventsAPI/MorgHTTPSocket responses for integration tests
- Use `create_mock_bot_with_image()` for visual detection tests  
- Test detection with `get_all_tagged_in_rect()` and color isolation
- Validate OCR with `ocr.extract_text()` and different fonts
- Test timing with `wait_til_gained_xp()` and animation detection

**Step 3: Minimal Implementation (Green Phase)**
- Create bot class inheriting from appropriate base (Bot/RuneLiteBot)
- Implement required abstract methods: `main_loop()`, `create_options()`, `save_options()`
- Use existing framework APIs: color detection, OCR, window management, mouse automation
- Integrate game state monitoring via EventsAPI or MorgHTTPSocket
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
        # - Game state checking (API calls)
        # - Mouse automation (self.mouse.move_to, click)
        # - Progress tracking (update_progress)
        # - Error handling and logging
```

**Step 4: Regression Testing**
- Run complete test suite: `pytest tests/ -v`
- Execute visual regression tests: `python scripts/visual_regression_test.py`
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

### API Integration Requirements:
- **Game State**: Use EventsAPI for real-time data, MorgHTTPSocket for HTTP polling
- **Inventory**: Check `get_is_inv_full()` before actions that generate items
- **Player Status**: Monitor `get_is_player_idle()` for action completion
- **Safety**: Implement friend detection (`friends_nearby()`) for logout safety

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
- **API mocking**: All external API calls mocked in integration tests
- **Error handling**: Graceful degradation on API failures
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
python scripts/visual_regression_test.py

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
if self.api_client.get_is_inv_full():
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
# Fast development cycle
pytest tests/unit/ tests/integration/ -v

# Visual testing
pytest tests/visual/ -v --capture=no

# Slow end-to-end tests  
pytest tests/e2e/ -v -m "slow"

# Performance testing
pytest tests/ -m "performance" -v

# Full test suite
pytest tests/ -v --cov=src --cov-report=html

# Type checking
mypy src/ --strict

# Visual regression
python scripts/visual_regression_test.py
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
