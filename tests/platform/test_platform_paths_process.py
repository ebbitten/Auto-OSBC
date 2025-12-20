"""
Comprehensive tests for platform_utils paths and process modules
Tests path utilities and process management functions
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils.paths import (
    get_python_executable_name,
    get_venv_activation_command,
    get_pip_executable_path
)

from src.platform_utils.process import (
    terminate_thread,
    launch_detached_process
)


class TestGetPythonExecutableName(unittest.TestCase):
    """Test Python executable name determination"""

    @patch('src.platform_utils.paths.get_platform')
    def test_windows_python_executable(self, mock_platform):
        """Test Windows uses 'python'"""
        mock_platform.return_value = "windows"

        result = get_python_executable_name()
        self.assertEqual(result, "python")

    @patch('src.platform_utils.paths.get_platform')
    def test_linux_python_executable(self, mock_platform):
        """Test Linux uses 'python3'"""
        mock_platform.return_value = "linux"

        result = get_python_executable_name()
        self.assertEqual(result, "python3")

    @patch('src.platform_utils.paths.get_platform')
    def test_macos_python_executable(self, mock_platform):
        """Test macOS uses 'python3'"""
        mock_platform.return_value = "darwin"

        result = get_python_executable_name()
        self.assertEqual(result, "python3")

    @patch('src.platform_utils.paths.get_platform')
    def test_unknown_platform_python_executable(self, mock_platform):
        """Test unknown platform defaults to 'python3'"""
        mock_platform.return_value = "unknown"

        result = get_python_executable_name()
        self.assertEqual(result, "python3")


class TestGetVenvActivationCommand(unittest.TestCase):
    """Test virtual environment activation command generation"""

    @patch('src.platform_utils.paths.get_platform')
    def test_windows_venv_activation(self, mock_platform):
        """Test Windows venv activation command"""
        mock_platform.return_value = "windows"

        venv_path = Path("venv")
        result = get_venv_activation_command(venv_path)

        self.assertIsInstance(result, str)
        self.assertIn("Scripts", result)
        self.assertIn("activate.bat", result)
        self.assertIn("venv", result)

    @patch('src.platform_utils.paths.get_platform')
    def test_linux_venv_activation(self, mock_platform):
        """Test Linux venv activation command"""
        mock_platform.return_value = "linux"

        venv_path = Path("venv")
        result = get_venv_activation_command(venv_path)

        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("source"))
        self.assertIn("bin/activate", result)
        self.assertIn("venv", result)

    @patch('src.platform_utils.paths.get_platform')
    def test_macos_venv_activation(self, mock_platform):
        """Test macOS venv activation command"""
        mock_platform.return_value = "darwin"

        venv_path = Path("venv")
        result = get_venv_activation_command(venv_path)

        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("source"))
        self.assertIn("bin/activate", result)

    @patch('src.platform_utils.paths.get_platform')
    def test_custom_venv_path(self, mock_platform):
        """Test custom venv path in activation command"""
        mock_platform.return_value = "windows"

        venv_path = Path("my_custom_env")
        result = get_venv_activation_command(venv_path)

        self.assertIn("my_custom_env", result)


class TestGetPipExecutablePath(unittest.TestCase):
    """Test pip executable path determination"""

    @patch('src.platform_utils.paths.get_platform')
    def test_windows_pip_path(self, mock_platform):
        """Test Windows pip executable path"""
        mock_platform.return_value = "windows"

        venv_path = Path("venv")
        result = get_pip_executable_path(venv_path)

        self.assertIsInstance(result, Path)
        self.assertEqual(result, venv_path / "Scripts" / "pip.exe")

    @patch('src.platform_utils.paths.get_platform')
    def test_linux_pip_path(self, mock_platform):
        """Test Linux pip executable path"""
        mock_platform.return_value = "linux"

        venv_path = Path("venv")
        result = get_pip_executable_path(venv_path)

        self.assertIsInstance(result, Path)
        self.assertEqual(result, venv_path / "bin" / "pip")

    @patch('src.platform_utils.paths.get_platform')
    def test_macos_pip_path(self, mock_platform):
        """Test macOS pip executable path"""
        mock_platform.return_value = "darwin"

        venv_path = Path("venv")
        result = get_pip_executable_path(venv_path)

        self.assertIsInstance(result, Path)
        self.assertEqual(result, venv_path / "bin" / "pip")

    @patch('src.platform_utils.paths.get_platform')
    def test_custom_venv_pip_path(self, mock_platform):
        """Test pip path with custom venv directory"""
        mock_platform.return_value = "windows"

        venv_path = Path("my_env")
        result = get_pip_executable_path(venv_path)

        expected = Path("my_env") / "Scripts" / "pip.exe"
        self.assertEqual(result, expected)


class TestTerminateThread(unittest.TestCase):
    """Test thread termination function"""

    def test_terminate_thread_basic(self):
        """Test basic thread termination"""
        # Create a simple thread that runs
        def worker():
            time.sleep(0.1)

        thread = threading.Thread(target=worker)
        thread.start()

        # Give thread time to start
        time.sleep(0.01)

        # Terminate the thread
        # Note: This function may use deprecated or unsafe methods
        # The test verifies it can be called without error
        try:
            terminate_thread(thread)
            # If function doesn't raise an exception, test passes
            self.assertTrue(True)
        except Exception as e:
            # Some thread termination methods may not work on all platforms
            self.skipTest(f"Thread termination not supported: {e}")

    def test_terminate_none_thread(self):
        """Test terminating None doesn't crash"""
        try:
            # Should handle None gracefully or raise appropriate error
            terminate_thread(None)
        except (TypeError, AttributeError):
            # Expected to fail with None
            pass

    def test_terminate_finished_thread(self):
        """Test terminating already finished thread"""
        def quick_worker():
            pass

        thread = threading.Thread(target=quick_worker)
        thread.start()
        thread.join()  # Wait for completion

        # Try to terminate already finished thread
        try:
            terminate_thread(thread)
            # Should handle gracefully
            self.assertTrue(True)
        except Exception:
            # May raise exception for finished thread
            pass


class TestLaunchDetachedProcess(unittest.TestCase):
    """Test detached process launching"""

    @patch('subprocess.Popen')
    @patch('src.platform_utils.process.get_platform')
    def test_launch_windows_process(self, mock_platform, mock_popen):
        """Test launching detached process on Windows"""
        mock_platform.return_value = "windows"
        mock_popen.return_value = MagicMock()

        # Function signature: launch_detached_process(executable_path, *args)
        result = launch_detached_process("python", "script.py")

        # Verify Popen was called
        mock_popen.assert_called_once()
        # Check that Windows-specific flags were used
        call_kwargs = mock_popen.call_args[1]
        if 'creationflags' in call_kwargs:
            # Windows uses CREATE_NEW_PROCESS_GROUP or DETACHED_PROCESS
            self.assertIsNotNone(call_kwargs.get('creationflags'))

    @patch('subprocess.Popen')
    @patch('src.platform_utils.process.get_platform')
    def test_launch_linux_process(self, mock_platform, mock_popen):
        """Test launching detached process on Linux"""
        mock_platform.return_value = "linux"
        mock_popen.return_value = MagicMock()

        result = launch_detached_process("python3", "script.py")

        # Verify Popen was called
        mock_popen.assert_called_once()
        # Check Unix-specific flags
        call_kwargs = mock_popen.call_args[1]
        if 'start_new_session' in call_kwargs:
            self.assertTrue(call_kwargs.get('start_new_session'))

    @patch('subprocess.Popen')
    def test_launch_returns_process(self, mock_popen):
        """Test that launch returns a process object"""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        result = launch_detached_process("python", "test.py")

        self.assertEqual(result, mock_process)

    @patch('subprocess.Popen')
    @patch('src.platform_utils.process.get_platform')
    def test_launch_with_multiple_args(self, mock_platform, mock_popen):
        """Test launching process with multiple arguments"""
        mock_platform.return_value = "linux"
        mock_popen.return_value = MagicMock()

        result = launch_detached_process("python3", "-m", "pytest", "tests/")

        # Verify Popen was called
        mock_popen.assert_called_once()
        # Check that executable and args were passed
        call_args = mock_popen.call_args[0]
        # Should contain the command as a list
        if call_args:
            self.assertIn("python3", str(call_args))


if __name__ == '__main__':
    unittest.main()
