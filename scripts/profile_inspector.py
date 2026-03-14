#!/usr/bin/env python3
"""
Profile Inspector: Display each profile one at a time, then all together.
Shows which loops are outer vs inner for each profile.
"""

import json
import sys
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def _sample_elliptical_arc(center, start_xy, end_xy, major, minor, rotation_rad, n=15):
    """Sample n points along a rotated elliptical arc, returns (xs, ys).
    Uses bounding-box proximity check to pick the correct arc direction."""
    cx, cy = center
    a, b = major, minor
    cos_r, sin_r = math.cos(rotation_rad), math.sin(rotation_rad)

    def point_to_t(px, py):
        dx, dy = px - cx, py - cy
        u =  dx * cos_r + dy * sin_r
        v = -dx * sin_r + dy * cos_r
        return math.atan2(v / b, u / a)

    t0 = point_to_t(*start_xy)
    t1 = point_to_t(*end_xy)

    def sample(dt):
        ts = [t0 + dt * i / (n - 1) for i in range(n)]
        xs = [cx + a * math.cos(t) * cos_r - b * math.sin(t) * sin_r for t in ts]
        ys = [cy + a * math.cos(t) * sin_r + b * math.sin(t) * cos_r for t in ts]
        return xs, ys

    bb_x = (min(start_xy[0], end_xy[0]), max(start_xy[0], end_xy[0]))
    bb_y = (min(start_xy[1], end_xy[1]), max(start_xy[1], end_xy[1]))
    margin = max(abs(end_xy[0] - start_xy[0]), abs(end_xy[1] - start_xy[1])) * 0.5 + 0.01

    def arc_stays_near(xs, ys):
        for x, y in zip(xs, ys):
            if x < bb_x[0] - margin or x > bb_x[1] + margin:
                return False
            if y < bb_y[0] - margin or y > bb_y[1] + margin:
                return False
        return True

    dt_short = (t1 - t0) % (2 * math.pi)
    if dt_short > math.pi:
        dt_short -= 2 * math.pi
    dt_long = dt_short - math.copysign(2 * math.pi, dt_short)

    xs, ys = sample(dt_short)
    if not arc_stays_near(xs, ys):
        xs, ys = sample(dt_long)
    return xs, ys

def load_fixture(filepath):
    """Load JSON fixture."""
    with open(filepath, 'r') as f:
        return json.load(f)

def draw_curves(ax, profile_data, color, alpha=0.7):
    """Draw sketch geometry curves from profile data."""
    if 'loops' not in profile_data:
        return

    for loop_idx, loop in enumerate(profile_data['loops']):
        for curve in loop['curves']:
            curve_type = curve.get('type')

            if curve_type == 'SketchLine':
                start = curve['start_xy']
                end = curve['end_xy']
                ax.plot([start[0], end[0]], [start[1], end[1]],
                       color=color, linewidth=2.5, alpha=alpha)

            elif curve_type == 'SketchCircle':
                center = curve['center_xy']
                radius = curve['radius']
                circle_patch = patches.Circle(center, radius, fill=False,
                                             edgecolor=color, linewidth=2.5, alpha=alpha)
                ax.add_patch(circle_patch)

            elif curve_type == 'SketchArc':
                center = curve['center_xy']
                radius = curve['radius']
                start = curve['start_xy']
                end = curve['end_xy']

                start_angle = math.degrees(math.atan2(start[1] - center[1],
                                                     start[0] - center[0]))
                end_angle = math.degrees(math.atan2(end[1] - center[1],
                                                   end[0] - center[0]))

                arc_patch = patches.Arc(center, radius * 2, radius * 2,
                                       angle=0, theta1=start_angle, theta2=end_angle,
                                       color=color, linewidth=2.5, alpha=alpha)
                ax.add_patch(arc_patch)

            elif curve_type == 'SketchEllipticalArc':
                center = curve['center_xy']
                start = curve['start_xy']
                end = curve['end_xy']
                major = curve['major_axis_length']
                minor = curve['minor_axis_length']
                rotation = curve['rotation_angle']

                xs, ys = _sample_elliptical_arc(center, start, end, major, minor, rotation)
                ax.plot(xs, ys, color=color, linewidth=2.5, alpha=alpha)

            elif curve_type == 'SketchEllipse':
                center = curve['center_xy']
                major = curve['major_axis_length']
                minor = curve['minor_axis_length']
                rotation = math.degrees(curve['rotation_angle'])

                ellipse_patch = patches.Ellipse(center, major, minor,
                                                angle=rotation, fill=False, edgecolor=color,
                                                linewidth=2.5, alpha=alpha)
                ax.add_patch(ellipse_patch)

def inspect_profiles(fixture_path):
    """Display each profile individually, then all together."""
    data = load_fixture(fixture_path)

    circle = data['target_circle']
    profiles = data['profiles']

    circle_center = tuple(circle['center_xy'])
    circle_radius = circle['radius_cm']

    print(f"Fixture: {Path(fixture_path).name}")
    print(f"Target circle: center={circle_center}, radius={circle_radius:.4f}")
    print(f"Total profiles: {len(profiles)}\n")

    # Display each profile individually
    for prof_idx, profile in enumerate(profiles):
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_aspect('equal')

        # Draw target circle
        target = patches.Circle(circle_center, circle_radius,
                               fill=False, edgecolor='black', linewidth=2,
                               linestyle='--', label='Target Circle')
        ax.add_patch(target)

        # Draw this profile
        color = plt.cm.tab10(prof_idx % 10)
        draw_curves(ax, profile, color, alpha=0.8)

        # Draw centroid
        centroid = tuple(profile['centroid_high_xy'])
        ax.plot(centroid[0], centroid[1], 'r+', markersize=15, markeredgewidth=2.5,
               label='Centroid')

        # Draw bounding box
        bbox = profile['bbox']
        min_xy = tuple(bbox['min_xy'])
        max_xy = tuple(bbox['max_xy'])
        width = max_xy[0] - min_xy[0]
        height = max_xy[1] - min_xy[1]
        bbox_patch = patches.Rectangle(min_xy, width, height,
                                       fill=False, edgecolor='blue', linewidth=1.5,
                                       linestyle=':', alpha=0.5, label='BBox')
        ax.add_patch(bbox_patch)

        # Add loop info to title
        num_loops = len(profile.get('loops', []))
        num_curves = sum(len(loop.get('curves', [])) for loop in profile.get('loops', []))
        has_any_split = any(loop.get('has_weird_split', False) for loop in profile.get('loops', []))

        title = f"Profile {prof_idx} — Area: {profile['area_high_accuracy']:.4f} cm²"
        title += f"\n{num_loops} loops, {num_curves} curves"
        if has_any_split:
            title += "  ⚠ WEIRD SPLIT DETECTED"
        ax.set_title(title, fontweight='bold', fontsize=12)

        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (cm)')
        ax.set_ylabel('Y (cm)')

        # Auto-scale
        all_x = [circle_center[0] - circle_radius, circle_center[0] + circle_radius,
                min_xy[0], max_xy[0]]
        all_y = [circle_center[1] - circle_radius, circle_center[1] + circle_radius,
                min_xy[1], max_xy[1]]
        margin = 1.0
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

        # Print loop details
        print(f"Profile {prof_idx}:")
        print(f"  Area: {profile['area_high_accuracy']:.4f} cm²")
        print(f"  Centroid: {centroid}")
        print(f"  Loops: {num_loops}")
        for loop_idx, loop in enumerate(profile.get('loops', [])):
            num_loop_curves = len(loop.get('curves', []))
            split_flag = " ⚠ WEIRD SPLIT" if loop.get('has_weird_split', False) else ""
            print(f"    Loop {loop_idx}: {num_loop_curves} curves{split_flag}")
            for curve in loop.get('curves', []):
                token = curve.get('entity_token', '')
                token_short = f"...{token[-16:]}" if token and len(token) > 16 else (token or 'N/A')
                print(f"      C{curve['curve_index']}: {curve['type']} token={token_short}")
        print()

    # Final figure: All profiles together
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_aspect('equal')

    # Draw target circle
    target = patches.Circle(circle_center, circle_radius,
                           fill=False, edgecolor='black', linewidth=2.5, label='Target Circle')
    ax.add_patch(target)

    # Draw all profiles
    colors = plt.cm.tab10(range(len(profiles)))
    for prof_idx, profile in enumerate(profiles):
        color = colors[prof_idx]
        draw_curves(ax, profile, color, alpha=0.7)

        # Draw centroid
        centroid = tuple(profile['centroid_high_xy'])
        ax.plot(centroid[0], centroid[1], '+', color=color, markersize=12, markeredgewidth=2)
        ax.text(centroid[0] + 0.1, centroid[1] + 0.1, f'P{prof_idx}',
               fontsize=9, color=color, fontweight='bold')

    ax.set_title(f"All Profiles — {data.get('description', 'Fixture')}",
                fontweight='bold', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Y (cm)')

    # Create legend
    legend_elements = [patches.Patch(facecolor=colors[i], edgecolor=colors[i],
                                    label=f'Profile {i}')
                      for i in range(len(profiles))]
    ax.legend(handles=legend_elements, loc='best', fontsize=10)

    # Auto-scale to show all
    all_bounds = [circle_center[0] - circle_radius, circle_center[0] + circle_radius,
                  circle_center[1] - circle_radius, circle_center[1] + circle_radius]
    for profile in profiles:
        bbox = profile['bbox']
        all_bounds[0] = min(all_bounds[0], bbox['min_xy'][0])
        all_bounds[1] = max(all_bounds[1], bbox['max_xy'][0])
        all_bounds[2] = min(all_bounds[2], bbox['min_xy'][1])
        all_bounds[3] = max(all_bounds[3], bbox['max_xy'][1])

    margin = 1.0
    ax.set_xlim(all_bounds[0] - margin, all_bounds[1] + margin)
    ax.set_ylim(all_bounds[2] - margin, all_bounds[3] + margin)

    plt.tight_layout()
    print("Displaying profiles...")
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python profile_inspector.py <fixture.json>")
        sys.exit(1)

    fixture_path = sys.argv[1]
    try:
        inspect_profiles(fixture_path)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
