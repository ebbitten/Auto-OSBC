from setuptools import setup, find_packages

setup(
    name="auto_osbc",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        'numpy',
        'opencv-python',
        'pillow',
        'pyautogui',
        'mypy',
        'pylint',
        'customtkinter',
        'pynput',
        'tktooltip'
    ],
)
