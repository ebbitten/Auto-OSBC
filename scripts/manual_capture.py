#!/usr/bin/env python3
"""
Manual Screenshot Capture Tool for Auto-OSBC
Quickly capture game state for debugging and testing purposes.
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utilities.window import Window
import cv2


def capture_current_state(description: str = "manual_capture", 
                         window_title: str = "RuneLite",
                         output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Capture current game state across all regions.
    
    Args:
        description: Description for the capture session
        window_title: Title of the game window to capture
        output_dir: Directory to save captures (default: debug_screenshots)
    
    Returns:
        Dictionary mapping region names to captured file paths
    """
    
    # Setup output directory
    if output_dir is None:
        output_dir = Path("debug_screenshots")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"{timestamp}_{description}"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Saving captures to: {session_dir}")
    
    # Initialize window
    try:
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
        print(f"✅ Connected to window: '{window_title}'")
        print(f"   Client mode: {'Fixed' if window.client_fixed else 'Resizable'}")
        print(f"   Game view: {window.game_view.width}x{window.game_view.height}")
    except Exception as e:
        print(f"❌ Failed to initialize window '{window_title}': {e}")
        print("   Make sure the game client is running and visible.")
        return {}
    
    # Define regions to capture
    regions = {
        'full_client': window.rectangle(),
        'game_view': window.game_view,
        'control_panel': window.control_panel,
        'inventory': window.control_panel,  # Alias for control panel
        'minimap_area': window.minimap_area,
        'minimap': window.minimap,
        'chat': window.chat,
    }
    
    # Add orb regions
    orb_regions = {
        'hp_orb': window.hp_orb_text,
        'prayer_orb': window.prayer_orb_text,
        'run_orb': window.run_orb_text,
        'spec_orb': window.spec_orb_text,
    }
    regions.update(orb_regions)
    
    captures = {}
    failed_captures = []
    
    print(f"📸 Capturing {len(regions)} regions...")
    
    for region_name, region in regions.items():
        try:
            screenshot = region.screenshot()
            filename = f"{region_name}.png"
            filepath = session_dir / filename
            
            cv2.imwrite(str(filepath), screenshot)
            captures[region_name] = filepath
            
            # Get image dimensions
            h, w = screenshot.shape[:2]
            print(f"   ✅ {region_name}: {w}x{h} → {filename}")
            
        except Exception as e:
            print(f"   ❌ {region_name}: Failed - {e}")
            failed_captures.append(region_name)
    
    # Create metadata file
    metadata = {
        "timestamp": timestamp,
        "description": description,
        "window_title": window_title,
        "client_mode": "fixed" if window.client_fixed else "resizable",
        "game_view_size": f"{window.game_view.width}x{window.game_view.height}",
        "successful_captures": list(captures.keys()),
        "failed_captures": failed_captures,
        "total_regions": len(regions)
    }
    
    metadata_file = session_dir / "capture_metadata.json"
    import json
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n📋 Capture Summary:")
    print(f"   Successful: {len(captures)}/{len(regions)} regions")
    print(f"   Failed: {len(failed_captures)} regions")
    if failed_captures:
        print(f"   Failed regions: {', '.join(failed_captures)}")
    print(f"   Metadata: {metadata_file}")
    
    return captures


def capture_specific_regions(regions: List[str], 
                           description: str = "specific_capture",
                           window_title: str = "RuneLite",
                           output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Capture specific regions only.
    
    Args:
        regions: List of region names to capture
        description: Description for the capture session
        window_title: Title of the game window
        output_dir: Directory to save captures
    
    Returns:
        Dictionary mapping region names to captured file paths
    """
    
    # Available regions
    available_regions = [
        'full_client', 'game_view', 'control_panel', 'inventory',
        'minimap_area', 'minimap', 'chat', 'hp_orb', 'prayer_orb',
        'run_orb', 'spec_orb'
    ]
    
    # Validate requested regions
    invalid_regions = [r for r in regions if r not in available_regions]
    if invalid_regions:
        print(f"❌ Invalid regions: {', '.join(invalid_regions)}")
        print(f"   Available regions: {', '.join(available_regions)}")
        return {}
    
    # Setup output directory
    if output_dir is None:
        output_dir = Path("debug_screenshots")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"{timestamp}_{description}"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Saving captures to: {session_dir}")
    
    # Initialize window
    try:
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
        print(f"✅ Connected to window: '{window_title}'")
    except Exception as e:
        print(f"❌ Failed to initialize window: {e}")
        return {}
    
    # Map region names to window objects
    region_map = {
        'full_client': window.rectangle(),
        'game_view': window.game_view,
        'control_panel': window.control_panel,
        'inventory': window.control_panel,
        'minimap_area': window.minimap_area,
        'minimap': window.minimap,
        'chat': window.chat,
        'hp_orb': window.hp_orb_text,
        'prayer_orb': window.prayer_orb_text,
        'run_orb': window.run_orb_text,
        'spec_orb': window.spec_orb_text,
    }
    
    captures = {}
    
    print(f"📸 Capturing {len(regions)} specific regions...")
    
    for region_name in regions:
        try:
            region = region_map[region_name]
            screenshot = region.screenshot()
            filename = f"{region_name}.png"
            filepath = session_dir / filename
            
            cv2.imwrite(str(filepath), screenshot)
            captures[region_name] = filepath
            
            h, w = screenshot.shape[:2]
            print(f"   ✅ {region_name}: {w}x{h} → {filename}")
            
        except Exception as e:
            print(f"   ❌ {region_name}: Failed - {e}")
    
    return captures


def capture_inventory_states(description: str = "inventory_states",
                           window_title: str = "RuneLite",
                           output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Capture inventory with slot overlays for testing.
    
    Args:
        description: Description for the capture session
        window_title: Title of the game window
        output_dir: Directory to save captures
    
    Returns:
        Dictionary mapping capture types to file paths
    """
    
    if output_dir is None:
        output_dir = Path("debug_screenshots")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"{timestamp}_{description}"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Saving inventory captures to: {session_dir}")
    
    try:
        window = Window(window_title, padding_top=26, padding_left=0)
        window.initialize()
        print(f"✅ Connected to window: '{window_title}'")
    except Exception as e:
        print(f"❌ Failed to initialize window: {e}")
        return {}
    
    captures = {}
    
    # Capture raw inventory
    try:
        inventory_screenshot = window.control_panel.screenshot()
        raw_path = session_dir / "inventory_raw.png"
        cv2.imwrite(str(raw_path), inventory_screenshot)
        captures['inventory_raw'] = raw_path
        print(f"   ✅ Raw inventory captured")
        
        # Create overlay with slot numbers
        overlay = inventory_screenshot.copy()
        
        for i, slot in enumerate(window.inventory_slots):
            # Calculate relative position within control panel
            rel_x = slot.left - window.control_panel.left
            rel_y = slot.top - window.control_panel.top
            
            # Draw slot rectangle
            cv2.rectangle(overlay, 
                         (rel_x, rel_y),
                         (rel_x + slot.width, rel_y + slot.height),
                         (0, 255, 0), 1)
            
            # Draw slot number
            cv2.putText(overlay, str(i),
                       (rel_x + 2, rel_y + 12),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
        
        overlay_path = session_dir / "inventory_with_slots.png"
        cv2.imwrite(str(overlay_path), overlay)
        captures['inventory_with_slots'] = overlay_path
        print(f"   ✅ Inventory with slot overlay captured")
        
        # Capture individual slots
        slots_dir = session_dir / "individual_slots"
        slots_dir.mkdir(exist_ok=True)
        
        for i, slot in enumerate(window.inventory_slots):
            try:
                slot_screenshot = slot.screenshot()
                slot_path = slots_dir / f"slot_{i:02d}.png"
                cv2.imwrite(str(slot_path), slot_screenshot)
            except Exception as e:
                print(f"   ⚠️  Failed to capture slot {i}: {e}")
        
        print(f"   ✅ Individual slots captured to: {slots_dir}")
        captures['individual_slots_dir'] = slots_dir
        
    except Exception as e:
        print(f"❌ Failed to capture inventory: {e}")
    
    return captures


def main():
    """Command-line interface for manual capture tool."""
    parser = argparse.ArgumentParser(description="Auto-OSBC Manual Screenshot Capture Tool")
    parser.add_argument("description", help="Description for this capture session")
    parser.add_argument("--window", default="RuneLite", help="Game window title")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--regions", nargs="+", help="Specific regions to capture")
    parser.add_argument("--inventory", action="store_true", help="Capture inventory with slot overlays")
    
    args = parser.parse_args()
    
    try:
        if args.inventory:
            captures = capture_inventory_states(args.description, args.window, args.output)
        elif args.regions:
            captures = capture_specific_regions(args.regions, args.description, args.window, args.output)
        else:
            captures = capture_current_state(args.description, args.window, args.output)
        
        if captures:
            print(f"\n✅ Capture completed successfully!")
            print(f"   Files saved: {len(captures)}")
        else:
            print(f"\n❌ Capture failed or no files saved.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Capture cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())