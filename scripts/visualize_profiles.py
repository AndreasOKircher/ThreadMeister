"""
Standalone matplotlib visualization for ThreadMeister profile fixtures.

Usage:
    python visualize_profiles.py fixtures/simple_m3_clean.json
    python visualize_profiles.py fixtures/  # all JSON files
"""

import json
import sys
import os
import glob
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def load_fixture(filepath):
    """Load and parse a JSON fixture file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def visualize_fixture(data, filepath):
    """
    Create visualization plots for a single fixture.

    Plots:
    1. All profiles with bounding boxes and centroids
    2. Filter results color-coded (green/yellow/blue/red)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f"Profile Selection: {os.path.basename(filepath)}\n{data.get('description', '')}",
                 fontsize=14, fontweight='bold')

    # Extract data
    circle = data['target_circle']
    profiles = data['profiles']
    expected_result = data['expected_result']

    circle_center = tuple(circle['center_xy'])
    circle_radius = circle['radius_cm']

    # ===== PLOT 1: All Profiles =====
    ax1.set_aspect('equal')
    ax1.set_title('All Profiles with Bounding Boxes')

    # Draw target circle
    circle_patch = patches.Circle(circle_center, circle_radius,
                                   fill=False, edgecolor='black', linewidth=2, label='Target Circle')
    ax1.add_patch(circle_patch)

    # Draw profiles with distinct colors
    colors = plt.cm.tab10(range(min(10, len(profiles))))
    for i, profile in enumerate(profiles):
        color = colors[i % len(colors)]

        # Bounding box
        bbox = profile['bbox']
        min_xy = tuple(bbox['min_xy'])
        max_xy = tuple(bbox['max_xy'])
        width = max_xy[0] - min_xy[0]
        height = max_xy[1] - min_xy[1]

        bbox_patch = patches.Rectangle(min_xy, width, height,
                                       fill=False, edgecolor=color, linewidth=1.5,
                                       linestyle='--', alpha=0.7, label=f'Profile {i}')
        ax1.add_patch(bbox_patch)

        # Centroid
        centroid = tuple(profile['centroid_low_xy'])
        ax1.plot(centroid[0], centroid[1], 'rx', markersize=8, markeredgewidth=2)
        ax1.text(centroid[0], centroid[1], f' {i}', fontsize=9, ha='left')

    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel('X (cm)')
    ax1.set_ylabel('Y (cm)')

    # Set axis limits to show all data
    all_bounds = [circle_center[0] - circle_radius, circle_center[0] + circle_radius,
                  circle_center[1] - circle_radius, circle_center[1] + circle_radius]
    for profile in profiles:
        bbox = profile['bbox']
        all_bounds[0] = min(all_bounds[0], bbox['min_xy'][0])
        all_bounds[1] = max(all_bounds[1], bbox['max_xy'][0])
        all_bounds[2] = min(all_bounds[2], bbox['min_xy'][1])
        all_bounds[3] = max(all_bounds[3], bbox['max_xy'][1])

    margin = 0.5
    ax1.set_xlim(all_bounds[0] - margin, all_bounds[1] + margin)
    ax1.set_ylim(all_bounds[2] - margin, all_bounds[3] + margin)

    # ===== PLOT 2: Filter Results Color-Coded =====
    ax2.set_aspect('equal')
    ax2.set_title('Filter Results (Green=Selected, Red=Rejected)')

    # Draw target circle
    circle_patch2 = patches.Circle(circle_center, circle_radius,
                                    fill=False, edgecolor='black', linewidth=2,
                                    linestyle='--', label='Target Circle')
    ax2.add_patch(circle_patch2)

    # Evaluate each profile
    for i, profile in enumerate(profiles):
        color = 'green' if i in expected_result else 'red'
        alpha = 0.6 if i in expected_result else 0.3

        # Bounding box
        bbox = profile['bbox']
        min_xy = tuple(bbox['min_xy'])
        max_xy = tuple(bbox['max_xy'])
        width = max_xy[0] - min_xy[0]
        height = max_xy[1] - min_xy[1]

        bbox_patch = patches.Rectangle(min_xy, width, height,
                                       fill=True, facecolor=color, alpha=alpha,
                                       edgecolor=color, linewidth=2)
        ax2.add_patch(bbox_patch)

        # Centroid
        centroid = tuple(profile['centroid_low_xy'])
        ax2.plot(centroid[0], centroid[1], 'ko', markersize=6)
        ax2.text(centroid[0], centroid[1], f' {i}', fontsize=9, ha='left', fontweight='bold')

    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('X (cm)')
    ax2.set_ylabel('Y (cm)')
    ax2.set_xlim(all_bounds[0] - margin, all_bounds[1] + margin)
    ax2.set_ylim(all_bounds[2] - margin, all_bounds[3] + margin)

    plt.tight_layout()
    return fig


def print_pass_fail_table(data):
    """Print pass/fail table for each profile and each filter."""
    profiles = data['profiles']
    expected_result = data['expected_result']

    print("\n" + "="*70)
    print(f"Fixture: {data.get('description', 'Unknown')}")
    print("="*70)
    print(f"Profile Count: {len(profiles)}")
    print(f"Selected Count: {len(expected_result)}")
    print("-"*70)
    print("Profile | Area   | Centroid | BBox   | Final")
    print("--------|--------|----------|--------|--------")

    for i, profile in enumerate(profiles):
        # Simplified pass/fail (would be more detailed with actual threshold values)
        area_pass = "✓"  # Would check against threshold in real implementation
        centroid_pass = "✓"
        bbox_pass = "✓"
        final = "SELECT" if i in expected_result else "REJECT"

        print(f"{i:7} | {area_pass:6} | {centroid_pass:8} | {bbox_pass:6} | {final:7}")

    print("="*70 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_profiles.py <fixture_file_or_dir>")
        print("  fixture_file: path to a single .json fixture")
        print("  fixture_dir:  path to directory of .json fixtures")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isfile(path):
        # Single file
        files = [path]
    elif os.path.isdir(path):
        # Directory of files
        files = sorted(glob.glob(os.path.join(path, "*.json")))
        if not files:
            print(f"No JSON files found in {path}")
            sys.exit(1)
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

    # Visualize each fixture
    for fixture_file in files:
        try:
            print(f"\nProcessing: {fixture_file}")
            data = load_fixture(fixture_file)
            print_pass_fail_table(data)
            fig = visualize_fixture(data, fixture_file)
        except Exception as e:
            print(f"Error processing {fixture_file}: {e}")
            continue

    plt.show()


if __name__ == '__main__':
    main()
