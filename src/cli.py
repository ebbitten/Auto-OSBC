#!/usr/bin/env python3
"""
Auto-OSBC Command Line Interface.

A minimal CLI for human interaction with the bot framework.

Commands:
    osbc go              Launch + login (auto-detects state)
    osbc go --skip-login Stop at login screen
    osbc start           Launch RuneLite + open bot GUI
    osbc start --headless  Launch RuneLite only (no GUI)
    osbc gui             Open bot selection GUI
    osbc login           Automate game login
    osbc status          Check current system state
"""

import argparse
import os
import sys


def cmd_go(args):
    """Unified launch + login command."""
    from model.actions import go_action

    result = go_action.go(
        force_restart=args.force_restart,
        skip_login=args.skip_login,
        timeout=args.timeout,
    )

    print(result.message)
    return 0 if result.success else 1


def cmd_start(args):
    """Main entry point - launch RuneLite and optionally open GUI."""
    from model.actions import orchestration

    if not args.no_launch:
        print("Launching RuneLite via OSBC...")
        result = orchestration.auto_launch_runelite(
            game=args.game,
            skip_if_running=not args.force,
            timeout=args.timeout,
        )

        if result.success:
            if result.data.get("skipped"):
                print("RuneLite already running")
            else:
                print(f"RuneLite launched: {result.message}")
        else:
            print(f"Launch failed: {result.message}")
            if not args.force_gui:
                return 1

    if not args.headless:
        return cmd_gui(args)

    return 0


def cmd_gui(args):
    """Open the bot selection GUI."""
    from OSBC import App
    App().start()
    return 0


def cmd_login(args):
    """Automate game login."""
    from model.actions import login

    result = login.perform_login(
        window_title=args.window,
        max_attempts=args.max_attempts,
    )

    print(result.message)
    return 0 if result.success else 1


def cmd_status(args):
    """Check current system state."""
    from model.system_state import SystemStateDetector

    detector = SystemStateDetector()
    state = detector.detect()
    description = detector.get_state_description(state)

    print(f"State: {state.name}")
    print(f"  {description}")

    if args.verbose:
        from model.actions import osbc
        result = osbc.check_windows_status()
        print(f"  OSBC: {result.data.get('osbc_title', 'Not running')}")
        print(f"  RuneLite: {result.data.get('runelite_title', 'Not running')}")

    return 0


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="osbc",
        description="Auto-OSBC Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  osbc start                Launch RuneLite + open bot GUI
  osbc start --headless     Launch RuneLite only (no GUI)
  osbc gui                  Open bot selection GUI
  osbc login                Automate game login
  osbc status               Check window status
  
  # Machine profiles:
  osbc --profile laptop start    Use laptop machine profile
  OSBC_MACHINE_PROFILE=desktop osbc start    Use desktop profile
        """,
    )
    
    # Add global options
    parser.add_argument(
        "--profile",
        help="Machine profile to use (overrides auto-detection)",
        dest="machine_profile",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    # --- go (primary command) ---
    go_parser = subparsers.add_parser(
        "go",
        help="Launch and login (auto-detects state)",
    )
    go_parser.add_argument("--skip-login", action="store_true", help="Stop at login screen")
    go_parser.add_argument("--force-restart", action="store_true", help="Close existing windows first")
    go_parser.add_argument("--timeout", type=float, default=180.0, help="Overall timeout (default: 180)")
    go_parser.set_defaults(func=cmd_go)

    # --- start ---
    start_parser = subparsers.add_parser(
        "start",
        help="Launch RuneLite and open bot GUI",
    )
    start_parser.add_argument("--game", default="OSRS", help="Game to select (default: OSRS)")
    start_parser.add_argument("--timeout", type=float, default=120.0, help="Launch timeout (default: 120)")
    start_parser.add_argument("--no-launch", action="store_true", help="Skip auto-launch")
    start_parser.add_argument("--headless", action="store_true", help="Don't open GUI")
    start_parser.add_argument("--force-gui", action="store_true", help="Open GUI even if launch fails")
    start_parser.add_argument("--force", action="store_true", help="Launch even if RuneLite already running")
    start_parser.set_defaults(func=cmd_start)

    # --- gui ---
    gui_parser = subparsers.add_parser("gui", help="Open bot selection GUI")
    gui_parser.set_defaults(func=cmd_gui)

    # --- login ---
    login_parser = subparsers.add_parser("login", help="Automate game login")
    login_parser.add_argument("--window", default="RuneLite", help="Window title (default: RuneLite)")
    login_parser.add_argument("--max-attempts", type=int, default=3, help="Max attempts (default: 3)")
    login_parser.set_defaults(func=cmd_login)

    # --- status ---
    status_parser = subparsers.add_parser("status", help="Check window status")
    status_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    status_parser.set_defaults(func=cmd_status)

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set machine profile if specified
    if hasattr(args, 'machine_profile') and args.machine_profile:
        os.environ['OSBC_MACHINE_PROFILE'] = args.machine_profile

    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
