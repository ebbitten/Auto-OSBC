from setuptools import setup, find_packages

setup(
    name="os-bot-color",
    version="0.1",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        "customtkinter",
        "pillow",
        "pynput",
        "tktooltip",
        # Add any other dependencies your project needs
    ],
)
