#!/usr/bin/env python3
"""
Auto-OSBC Command Line Interface.

A minimal CLI for human interaction with the bot framework.

Commands:
    osbc start           Launch RuneLite + open bot GUI
    osbc start --headless  Launch RuneLite only (no GUI)
    osbc gui             Open bot selection GUI
    osbc login           Automate game login
    osbc status          Check window status
"""

import argparse
import sys


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
    """Check OSBC and RuneLite window status."""
    from model.actions import osbc

    result = osbc.check_windows_status()
    print(result.message)

    if args.verbose:
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
        """,
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

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

    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
