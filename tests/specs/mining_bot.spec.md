# Feature: Mining Bot

## Objective
Create a simple mining automation bot that detects pink-tagged mining rocks, mines them until inventory is full, drops all items, and continues mining. The bot serves as a reference implementation to validate the Auto-OSBC TDD workflow and demonstrate all framework components.

## Acceptance Criteria
- [ ] **AC1: Rock Detection**: Bot must detect pink-tagged mining rocks in the game view using color detection
- [ ] **AC2: Mining Interaction**: Bot must click on detected rocks and wait for mining animation to complete
- [ ] **AC3: Inventory Management**: Bot must detect when inventory is full and drop all items
- [ ] **AC4: Continuous Operation**: Bot must continue mining until the specified time limit is reached
- [ ] **AC5: Safety Features**: Bot must logout when friends are detected nearby (if enabled)
- [ ] **AC6: Progress Tracking**: Bot must update progress bar and log meaningful messages
- [ ] **AC7: Error Handling**: Bot must handle scenarios where no rocks are found gracefully
- [ ] **AC8: Performance**: Mining cycle (detect → click → wait → check) must complete in under 5 seconds

## Visual Requirements

### Detection Targets
- **Primary Target**: Pink-tagged mining rocks (clr.PINK color isolation)
- **Target Validation**: Objects must be 20-100 pixels in width/height to filter noise
- **Prioritization**: Nearest rock to screen center should be selected first

### Color Requirements
- **Rock Detection**: `clr.PINK` color for tagged mining rocks
- **Inventory Detection**: Use EventsAPI `get_is_inv_full()` for inventory state
- **Animation Detection**: Use EventsAPI `get_is_player_idle()` for mining completion

### OCR Requirements
- **Not Required**: This bot relies primarily on color detection and API calls
- **Logging Only**: Use bot logging system for user feedback

### Screenshot Fixtures Required
- `mining_area_with_rocks.png` - Game view with 2-3 pink-tagged rocks visible
- `mining_area_no_rocks.png` - Game view with no tagged rocks (fallback scenario)
- `inventory_full_mining.png` - Control panel with full inventory
- `inventory_empty_mining.png` - Control panel with empty inventory
- `mining_in_progress.png` - Game view showing mining animation

## API Integration

### Required Endpoints
**EventsAPI Methods**:
- `get_is_inv_full()` - Check if inventory is full (primary inventory detection)
- `get_is_player_idle()` - Check if mining animation has completed
- `get_player_position()` - For potential stuck detection (future enhancement)

**Alternative Methods** (if EventsAPI unavailable):
- Visual inventory detection using control panel screenshots
- OCR-based idle detection using current action text area

### Game State Dependencies
- **Player Position**: Must be positioned near tagged mining rocks
- **Equipment**: Pickaxe must be equipped (assumption - not validated by bot)
- **Inventory**: Must start with empty or partially empty inventory
- **Game Mode**: Fixed or resizable client modes supported

### Timing Constraints
- **API Response Time**: EventsAPI calls must respond within 1 second
- **Detection Time**: Rock detection must complete within 100ms
- **Mining Cycle**: Complete detect→click→wait→check cycle within 5 seconds

## Game Client Setup

### Prerequisites
**Player Setup**:
1. Player must be positioned in a mining area
2. Pickaxe must be equipped in weapon slot
3. Inventory should be empty or have space for ore
4. Player should be in a safe area (no aggressive NPCs)

**Game Client Configuration**:
1. RuneLite client with mining rocks tagged (pink outline)
2. Client can be in Fixed or Resizable mode
3. EventsAPI plugin must be active and responding
4. Game view must be visible and unobstructed

**Required Manual Setup**:
1. Right-click and "Mark" mining rocks with pink color
2. Position character within clicking distance of rocks
3. Ensure inventory tab is accessible
4. Verify EventsAPI is responding (test with debug console)

### Test Environment
- **Game Area**: Any mining location with 2+ rock spawns
- **Rock Types**: Any minable rocks (copper, iron, coal, etc.)
- **Time of Day**: Any (color detection not affected by lighting)
- **World Population**: Low population preferred for safety

## Edge Cases

### Visual Detection Edge Cases
- **No rocks detected**: Bot should wait 5 seconds and retry detection
- **Multiple rocks available**: Bot should prioritize nearest to screen center
- **Partially visible rocks**: Detection should work with rocks at screen edges
- **Other players mining**: Bot should still detect and attempt available rocks

### Inventory Management Edge Cases
- **Inventory full mid-mining**: Bot should complete current mining action then drop
- **Drop action interrupted**: Bot should retry drop operation if items remain
- **Untradeable items**: Bot should attempt to drop all items regardless of type

### API Communication Edge Cases
- **EventsAPI timeout**: Fallback to visual detection methods
- **Invalid API response**: Retry API call up to 3 times before fallback
- **API temporarily unavailable**: Continue with visual-only detection

### Safety and Error Conditions
- **Friends detected**: Immediate logout if `logout_on_friends` enabled
- **No rocks found for 30+ seconds**: Log warning but continue searching
- **Player stuck/not moving**: Future enhancement - not implemented in v1
- **Game client disconnection**: Bot should detect and stop gracefully

## Testing Strategy

### Unit Tests Focus
- `test_rock_detection_logic()` - Test color filtering and validation logic
- `test_inventory_management()` - Test drop logic with mocked inventory data
- `test_safety_checks()` - Test friend detection and logout logic
- `test_configuration_handling()` - Test options parsing and validation

### Integration Tests Focus
- `test_api_integration()` - Test EventsAPI calls with mocked responses
- `test_window_integration()` - Test window region access with mock window
- `test_mouse_integration()` - Test mouse movement logic with mock mouse
- `test_error_handling()` - Test error scenarios with mocked failures

### Visual Tests Focus
- `test_rock_detection_accuracy()` - Test detection with screenshot fixtures
- `test_inventory_detection()` - Test inventory state detection with screenshots
- `test_detection_performance()` - Benchmark detection speed with test images
- `test_visual_regression()` - Ensure detection remains stable across UI changes

### End-to-End Tests Focus
- `test_complete_mining_cycle()` - Test full cycle with actual game client (manual)
- `test_safety_features()` - Test friend detection with real game state
- `test_error_recovery()` - Test bot behavior when rocks disappear

## Performance Requirements

### Speed Targets
- **Rock Detection**: < 100ms per detection cycle
- **API Calls**: < 1000ms per EventsAPI request
- **Mouse Movement**: < 500ms from target selection to click
- **Complete Cycle**: < 5000ms from detection to action completion

### Memory Targets
- **Peak Memory**: < 50MB additional memory usage during operation
- **Memory Leaks**: No memory growth over 30-minute operation
- **Screenshot Caching**: Limit cached screenshots to 10MB maximum

### Reliability Targets
- **Success Rate**: > 95% successful rock detection when rocks are visible
- **Uptime**: Bot should run for 60+ minutes without crashes
- **Recovery Rate**: > 90% successful recovery from transient errors

## Implementation Notes

### Bot Inheritance
- **Base Class**: `RuneLiteBot` (requires color detection and contour extraction)
- **Reason**: Needs `get_all_tagged_in_rect()` for pink rock detection
- **Alternative**: Could use base `Bot` class with manual color detection

### Development Phases
1. **Phase 1**: Basic rock detection and clicking
2. **Phase 2**: Inventory management and dropping
3. **Phase 3**: Safety features and error handling
4. **Phase 4**: Performance optimization and caching

### Known Limitations
- **Rock Respawn**: Bot does not predict or optimize for rock respawn timing
- **Efficiency**: Bot does not optimize for fastest XP/hour (focuses on simplicity)
- **Advanced Features**: No banking, no ore selection, no efficiency tracking
- **Multi-Rock Mining**: Mines one rock at a time (no power mining optimization)

## Success Metrics

### Functional Success
- ✅ Bot can detect and mine tagged rocks consistently
- ✅ Bot manages inventory by dropping when full
- ✅ Bot operates safely with friend detection
- ✅ Bot provides clear user feedback via logging

### Technical Success
- ✅ All tests pass (unit, integration, visual)
- ✅ Performance targets met (< 100ms detection, < 5s cycles)
- ✅ Code follows framework patterns and conventions
- ✅ Documentation demonstrates complete TDD workflow

### Educational Success
- ✅ Implementation validates documented TDD workflow
- ✅ Code serves as reference for future bot development
- ✅ Debug tools are demonstrated and validated
- ✅ Testing strategies are proven effective

This specification serves as both a functional requirement and a validation test for the Auto-OSBC TDD workflow. Successful implementation following the documented process will prove the framework's effectiveness for game automation development.