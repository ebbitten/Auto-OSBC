# Login State Test Fixtures

Screenshots of each login state for visual detection testing.

## Available Fixtures

| File | State | Source |
|------|-------|--------|
| `welcome_screen.png` | WELCOME | ActionRecorder session 22-23-57 |
| `login_screen.png` | LOGIN | ActionRecorder session 22-23-57 (after click) |
| `logged_in_screen.png` | LOGGED_IN | ActionRecorder session 22-19-39 (false positive session) |

## Missing Fixtures

- `click_to_play_screen.png` - Need to capture when at CLICK_TO_PLAY state

## How to Capture New Fixtures

```bash
# Use recorder to capture screenshots
python scripts/recorder.py --window "RuneLite" --duration 5 --interval 1000

# Or use manual capture
python scripts/manual_capture.py "description"
```

## Usage in Tests

```python
import cv2
from pathlib import Path

FIXTURES_PATH = Path(__file__).parent / "tests/fixtures/login_states"

def load_fixture(name: str):
    return cv2.imread(str(FIXTURES_PATH / name))

# Example
welcome_img = load_fixture("welcome_screen.png")
```
