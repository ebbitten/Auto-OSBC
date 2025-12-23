# Login Automation Specification

## Overview
Automate the RuneLite game login process using human-like input via the intent-executor pattern.

## Requirements

### Functional Requirements

1. **Credential Management**
   - Load username from `OSBC_USERNAME` environment variable
   - Load password from `OSBC_PASSWORD` environment variable
   - Support credential override via method parameters
   - Validate credentials are configured before attempting login

2. **Login Screen Detection**
   - Detect when game is on login screen (vs logged in, lobby, error states)
   - Locate username input field
   - Locate password input field
   - Locate login button
   - Extract error messages if present

3. **Login Execution**
   - Click username field to focus
   - Type username with human-like timing (TypeIntent)
   - Press Tab to move to password field (KeyPressIntent)
   - Type password with masking in logs (TypeIntent, mask_in_logs=True)
   - Click login button
   - Wait for login to complete (game UI visible)

4. **Error Handling**
   - Retry on connection errors (configurable max attempts)
   - Stop immediately on invalid credentials (no retry)
   - Handle account locked/disabled states
   - Handle client update required state
   - Timeout after configurable duration

### Non-Functional Requirements

1. **Security**
   - Never log actual password text
   - Credentials stored in environment variables only
   - No credential persistence

2. **Human-like Behavior**
   - Use existing TypeIntent interval (0.05s between keys)
   - Use medium mouse speed for clicks
   - Add small delays between actions

3. **Testability**
   - All components unit-testable with mocks
   - Use MockExecutor for testing intent sequences
   - Visual detection mockable with test images

## Login States

```
UNKNOWN           - Cannot determine state
LOGIN_SCREEN      - Main login screen, credentials needed
ENTERING_USERNAME - Username field has focus
ENTERING_PASSWORD - Password field has focus
CLICK_TO_PLAY     - Post-login "Click here to Play" screen
LOBBY             - World selection screen
LOGGED_IN         - Fully in-game with UI visible
CONNECTION_ERROR  - Network/server error
INVALID_CREDENTIALS - Wrong username/password
ACCOUNT_LOCKED    - Too many failed attempts
UPDATE_REQUIRED   - Client needs update
```

## Detection Strategy

### Login Screen Detection
1. **Primary**: Template match for login button image
2. **Fallback**: OCR search for "Username:" text

### Field Location
1. Find "Username:" label via OCR
2. Username field: Centered below label
3. Password field: Below username field (fixed offset)
4. Login button: Template match

### Logged-In Detection
1. Check if window.inventory_slots exists and has 28 slots
2. Alternatively, check for minimap or other game UI elements

## API Design

### LoginCredentials
```python
class LoginCredentials:
    ENV_USERNAME = "OSBC_USERNAME"
    ENV_PASSWORD = "OSBC_PASSWORD"

    username: str
    password: str

    def is_configured(self) -> bool
```

### LoginScreenDetector
```python
class LoginScreenDetector:
    def __init__(self, window: Window)

    def detect_state(self) -> LoginScreenInfo
    def is_on_login_screen(self) -> bool
    def is_logged_in(self) -> bool
    def get_username_field_location(self) -> Optional[Rectangle]
    def get_password_field_location(self) -> Optional[Rectangle]
    def get_login_button_location(self) -> Optional[Rectangle]
    def get_error_message(self) -> Optional[str]
```

### LoginService
```python
class LoginService:
    def __init__(self, bot: Bot)

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_attempts: int = 3,
        timeout: float = 60.0,
    ) -> ActionOutcome
```

### Bot Integration
```python
class Bot:
    def login(self, username=None, password=None) -> bool
    def is_on_login_screen(self) -> bool
```

## Test Cases

### LoginCredentials Tests
- Load from environment variables
- Override with explicit values
- is_configured() returns False when missing
- Empty string treated as not configured

### LoginScreenDetector Tests
- Detect login screen from screenshot
- Detect logged-in state from game UI
- Find username field location
- Find password field location
- Find login button location
- Extract error messages
- Return UNKNOWN for unrecognized states

### LoginService Tests
- Successful login flow (mock executor)
- Retry on connection error
- No retry on invalid credentials
- Timeout handling
- Credential loading from env vars
- Credential override support

## Edge Cases

1. **Already logged in**: Return success immediately
2. **Missing credentials**: Return failure before attempting
3. **Field not found**: Try fallback detection, fail gracefully
4. **Login button not found**: Try OCR fallback
5. **Multiple retries exhausted**: Return failure with attempt count
6. **Unexpected screen state**: Log warning, return failure
