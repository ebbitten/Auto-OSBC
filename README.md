### ⚠️ This project is in Alpha stage ⚠️

# ![logo](https://github.com/kelltom/OS-Bot-COLOR/assets/44652363/c9b93ee8-91a7-4bb4-8e92-5944e2d9d283)
OS Bot COLOR (OSBC) is a desktop client for controlling and monitoring automation scripts for games. This application is paired with a toolkit for writing new scripts. Unlike popular automation frameworks that modify/inject code into a game's client, OSBC is completely hands-off; it uses a combination of color detection, image recognition, and optical character recognition to navigate the game. The goal of OSBC is to provide a fun and educational learning experience for new & seasoned developers alike, emphasizing the exploration of automation technologies and not to encourage or support activities that are in violation of any game's Terms of Service.

<!--
💬 [Join the Discord](https://discord.gg/S6DXZfma5z) to discuss the project, ask questions, and follow development

📹 Subscribe to [Kell's Code](https://www.youtube.com/@KellsCode/featured) on YouTube for updates and tutorials

⭐ If you like this project, please leave a Star :)
 -->

# Developer Setup <img height=20 src="documentation/media/windows_logo.png"/>
1. Install [Python 3.10](https://www.python.org/downloads/release/python-3109/) *(not compatible with other major versions)*
2. Clone/download this repository
3. Open the project folder in your IDE of choice (Visual Studio Code recommended)
4. Open the repository folder in a terminal window
   1. Create a virtual environment ```py -3.10 -m venv env```
   2. Activate the newly created virtual environment ```.\env\Scripts\activate```
   3. Install the depedencies ```pip install -r requirements.txt```
5. Run `./src/*OSBC.py*` *(may need to restart IDE for it to recognize installed dependencies)*

# Type Checking and Code Quality

## Static Type Checking with mypy
OSBC uses strict type checking to catch errors early. Before submitting any code changes:

1. Install mypy if not already installed:
   ```bash
   pip install mypy
   ```

2. Run mypy on the source code:
   ```bash
   mypy src/
   ```

3. Fix any type errors that are reported. Common issues include:
   - Missing type hints
   - Incorrect return types
   - Incompatible types in assignments
   - Missing imports

## Runtime Type and Attribute Checking
OSBC provides two key decorators for runtime checks:

1. `@validate_types`: Validates function argument and return types:
   ```python
   @validate_types
   def my_function(arg1: int, arg2: str) -> bool:
       return isinstance(arg2, str)
   ```

2. `@validate_module_attributes`: Ensures required module attributes exist:
   ```python
   @validate_module_attributes('rd.truncated_normal_sample', 'rd.random_chance')
   def my_function() -> None:
       value = rd.truncated_normal_sample(0, 1)
   ```

## Development Best Practices

1. Type Hints:
   - Always add type hints to function arguments and return values
   - Use `Optional[Type]` for values that might be None
   - Use `Union[Type1, Type2]` for values that could be multiple types
   - Use `TypeGuard` for type narrowing functions

   ```python
   from typing import Optional, Union, TypeGuard
   
   def process_value(value: Optional[Union[int, float]]) -> None:
       if value is not None:
           print(value + 1)
   
   def is_valid_point(obj: Any) -> TypeGuard[Point]:
       return isinstance(obj, Point)
   ```

2. Attribute Checking:
   - Use `hasattr()` to check for attribute existence
   - Use the `@validate_module_attributes` decorator for module dependencies
   - Add required attributes to function documentation

3. Error Handling:
   - Use type-specific exception handling
   - Log detailed error information
   - Include stack traces in debug mode

4. Pre-commit Checks:
   Run these checks before committing code:
   ```bash
   # Run static type checking
   mypy src/

   # Run linter (if configured)
   flake8 src/

   # Run tests (if available)
   pytest
   ```

## Common Issues and Solutions

1. Missing Attributes:
   ```python
   # Wrong:
   result = module.some_function()  # Might raise AttributeError
   
   # Right:
   @validate_module_attributes('module.some_function')
   def my_function():
       result = module.some_function()
   ```

2. Type Checking:
   ```python
   # Wrong:
   def process_point(point):  # No type hints
       return point.x + 10
   
   # Right:
   def process_point(point: Point) -> int:
       return point.x + 10
   ```

3. Optional Values:
   ```python
   # Wrong:
   def find_item(items: List[str]) -> str:
       return next(iter(items))  # Might raise StopIteration
   
   # Right:
   def find_item(items: List[str]) -> Optional[str]:
       return next(iter(items), None)
   ```

For more information about type checking and best practices, see the [Wiki](https://github.com/kelltom/OSRS-Bot-COLOR/wiki).

---

# Documentation

See the [Wiki](https://github.com/kelltom/OSRS-Bot-COLOR/wiki) for tutorials, and software design information.

# Features
## User Interface
OSBC offers a clean interface for configuring, running, and monitoring your Python bots. For developers, this means that all you need to do is write a bot's logic loop, and *the UI is already built for you*.

![intro_demo](documentation/media/intro_demo.gif)

### Script Log
The Script Log provides a clean and simple way to track your bot's progress. No more command line clutter!

```python
self.log_msg("The bot has started.")
```

### Simple Option Menus
OSBC allows developers to create option menus and parse user selections with ease.

```python
def create_options(self):
  ''' Declare what should appear when the user opens the Options menu '''
  self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 180)
  self.options_builder.add_text_edit_option("text_edit_example", "Text Edit Example", "Placeholder text here")
  self.options_builder.add_checkbox_option("multi_select_example", "Multi-select Example", ["A", "B", "C"])
  self.options_builder.add_dropdown_option("menu_example", "Menu Example", ["A", "B", "C"])
```

## Human-like Mouse Movement
OSBC uses Bezier curves to create smooth, human-like mouse movements.

## Object Detection
Using color isolation, OSBC can quickly locate objects/NPCs outlined by solid colors and extract their properties into simple data structures.

## Random Click Distribution
With the help of the OSBC community, we've created a randomization algorithm that distributes clicks in a way that is more human-like.

## Efficient Image Searching
Sometimes, your bot might need to find a specific image on screen. We've modified OpenCV's template matching algorithm to be more efficient and reliable with UI elements and sprites - even supporting images with transparency.

## Lightning Fast Optical Character Recognition
We've ditched machine learned OCR in favor of a much faster and more reliable custom implementation. OSBC can locate text on screen in as little as **2 milliseconds**. That's **0.002 seconds**.

---

<p>
  <a href="https://www.buymeacoffee.com/kelltom" target="_blank">
    <img src="https://i.imgur.com/5X29MVY.png" alt="Buy Me A Coffee" height="60dp">
  </a>
</p>




# OS Bot COLOR

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/OS-Bot-COLOR.git
   cd OS-Bot-COLOR
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the project and its dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python src/OSBY.py
   ```

## Development

For development, you may want to install the project in editable mode:
```
pip install -e .
```

This allows changes to the source code to be immediately reflected in the installed package.

## Code Modification Guidelines

When modifying or adding code:

1. Use existing utilities:
   - Random operations: `rd.random_int()`, `rd.random_chance()`, etc.
   - Mouse movements: `self.mouse.move_to()`, `self.mouse.click()`
   - Geometry: `Point`, `Rectangle` from `utilities.geometry`
   - Color detection: `utilities.color as clr`
   - Image search: `utilities.imagesearch as imsearch`
   - OCR: `utilities.ocr as ocr`

2. Follow established patterns:
   - Use `self.log_msg()` for user feedback
   - Use consistent timing patterns
   - Follow existing error handling approaches
   - Use existing mouse movement patterns

3. Check similar implementations:
   - Look for similar functionality in other bot classes
   - Maintain consistency with existing code
   - Reuse existing methods where possible