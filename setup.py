from setuptools import setup, find_packages

setup(
    name="auto_osbc",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        # Core dependencies
        'numpy==1.23.1',
        'opencv-python==4.5.4.60',
        'pillow==9.3.0',
        'pyautogui==0.9.53',
        'customtkinter==5.1.3',
        'pynput==1.7.6',
        'tkinter-tooltip==2.1.0',
        
        # Window and GUI management
        'PyWinCtl==0.0.42',
        'mss==7.0.1',
        
        # Utilities
        'requests==2.31.0',
        'deprecated==1.2.13',
        'pytweening==1.2.0',
        
        # Development tools
        'mypy',
        'flake8==6.0.0',
    ],
    extras_require={
        'dev': [
            'pre-commit==2.20.0',
            'pytest',
            'pytest-mock',
            'pytest-cov',
            'opencv-python-headless==4.5.4.60',
        ],
        'linux': [
            # Linux-specific dependencies if needed in future
            # 'evdev==1.7.0',  # Currently unused
        ],
        'windows': [
            # Windows-specific dependencies if needed
        ],
    },
    python_requires='>=3.10',
)
