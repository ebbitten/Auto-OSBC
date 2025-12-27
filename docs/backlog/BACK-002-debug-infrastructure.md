# BACK-002: Debug Infrastructure Enhancement

## Epic Overview
**Priority**: Medium
**Effort**: Medium (4-6 weeks)
**Status**: Mostly Complete (Dec 2025)
**Dependencies**: BACK-001 (testing framework) ✅

## Progress Summary (Dec 2025)
Major debug infrastructure now in place:
- **ActionRecorder** - Captures before/after screenshots with annotations
- **Flow Profiler** - Performance profiling for state detection
- **Organized captures** - `captures/action_recordings/` with HTML reports

## Original Problem Statement (Status)
~~Debug infrastructure exists but is scattered and inconsistent:~~
- ~~Debug tools exist in `scripts/` but not integrated~~ → **ActionRecorder integrated into `osbc go --record`**
- ~~Debug screenshots saved to various locations~~ → **Organized in `captures/action_recordings/`**
- ~~Mining bot has debug mode but patterns not standardized~~ → **ActionRecorder is the standard pattern**
- ~~No real-time debugging interface or performance profiling~~ → **flow_profiler.py exists**
- **MSS library bug** - Status unknown, needs verification
- **Screenshot capture architecture** - Improved with caching in login_screen.py

## Current State
✅ **Complete**:
- `scripts/recorder.py` - ActionRecorder class for automated debugging
- `scripts/debug_console.py` - Interactive debug console
- `scripts/manual_capture.py` - Screenshot capture
- `scripts/flow_profiler.py` - Performance profiling
- Debug screenshot capture in mining bot
- HTML report generation for action recordings

⚠️ **Partial**:
- Real-time debugging interface (ActionRecorder is post-hoc, not real-time)
- Visual debugging overlay system (annotations exist but not live overlay)

## Success Criteria
- [ ] Unified debug interface accessible from all bots
- [ ] Real-time visual debugging overlays
- [ ] Performance profiling integrated into development workflow
- [ ] Standardized debug patterns across all bot implementations
- [ ] Debug session management and replay capability

## Implementation Breakdown

### Sub-Task 1: Debug Interface Standardization
**Effort**: 1.5 weeks
- Standardize debug screenshot patterns across bots
- Create unified debug configuration system
- Build debug session management
- **Fix MSS library global variable bug** - implement proper context management

### Sub-Task 2: Real-Time Debug Overlays
**Effort**: 2 weeks
- Visual detection result overlays
- Mouse movement path visualization
- API response data display
- Performance metrics overlay

### Sub-Task 3: Performance Monitoring Integration  
**Effort**: 1.5 weeks
- Detection algorithm performance tracking
- Memory usage monitoring
- Bot cycle time analysis
- Automated performance regression detection

### Sub-Task 4: Debug Session Replay
**Effort**: 1 week
- Debug session recording
- Step-by-step replay capability
- State inspection tools
- Debug session sharing and analysis

## Technical Requirements
- Enhanced debug console with real-time capabilities
- Visual overlay system using OpenCV
- Performance monitoring hooks in core framework
- Debug session serialization and storage

---
**Moved from**: docs/debugging-guide.md, scattered debug implementations
**Related**: Mining bot debug mode, scripts/debug_console.py