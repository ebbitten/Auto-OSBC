"""
Platform-specific process and thread management for Auto-OSBC
Handles thread termination and subprocess creation across platforms
"""
import ctypes
import subprocess
from typing import List
from .detection import get_platform


def terminate_thread(thread_id: int) -> None:
    """
    Terminate a thread by raising SystemExit exception.
    Platform-specific implementation for thread termination.

    Args:
        thread_id: The thread ID to terminate

    Note:
        On Windows, thread IDs are used directly
        On Linux/macOS, thread IDs must be cast to c_long
    """
    current_platform = get_platform()

    try:
        if current_platform == "windows":
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print("Exception raise failure")
        elif current_platform in ["linux", "darwin"]:
            # Linux and macOS use c_long for thread ID
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
                print("Exception raise failure")
        else:
            print(f"Warning: Thread termination not implemented for platform: {current_platform}")
    except Exception as e:
        print(f"Error during thread termination: {e}")


def launch_detached_process(executable_path: str, *args: str) -> subprocess.Popen:
    """
    Launch a detached process that continues running after parent exits.
    Platform-specific implementation for process creation.

    Args:
        executable_path: Path to the executable to launch
        *args: Additional command-line arguments

    Returns:
        Popen object representing the launched process

    Note:
        On Windows, uses DETACHED_PROCESS creation flag
        On Linux/macOS, uses start_new_session with redirected output
    """
    current_platform = get_platform()
    command: List[str] = [executable_path] + list(args)

    if current_platform == "windows":
        return subprocess.Popen(command, creationflags=subprocess.DETACHED_PROCESS)
    elif current_platform in ["linux", "darwin"]:
        # Linux and macOS use different subprocess options
        return subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    else:
        # Fallback for unknown platforms
        print(f"Warning: Unknown platform {current_platform}, using default subprocess options")
        return subprocess.Popen(command)
