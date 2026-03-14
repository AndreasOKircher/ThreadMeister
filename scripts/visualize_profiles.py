"""
Standalone matplotlib visualization for ThreadMeister profile fixtures.

Multi-stage filter visualization with keyboard navigation.

Usage:
    python visualize_profiles.py fixtures/simple_m3_clean.json
    python visualize_profiles.py fixtures/  # all JSON files

Controls:
    Arrow keys: Navigate between filter stages (Area → Centroid → Final)
    Close window to move to next fixture
"""

import json
import sys
import os
import glob
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def _sample_elliptical_arc(center, start_xy, end_xy, major, minor, rotation_rad, n=15):
    """
    Sample n points along an elliptical arc and return (xs, ys) lists.

    Uses parametric form with rotation:
      x(t) = cx + a*cos(t)*cos(r) - b*sin(t)*sin(r)
      y(t) = cy + a*cos(t)*sin(r) + b*sin(t)*cos(r)

    Finds t_start/t_end by inverting the parametric equations, then samples
    linearly between them (taking the shorter arc).
    """
    cx, cy = center
    a, b = major, minor
    cos_r, sin_r = math.cos(rotation_rad), math.sin(rotation_rad)

    def point_to_t(px, py):
        dx, dy = px - cx, py - cy
        u =  dx * cos_r + dy * sin_r   # = a * cos(t)
        v = -dx * sin_r + dy * cos_r   # = b * sin(t)
        return math.atan2(v / b, u / a)

    t0 = point_to_t(*start_xy)
    t1 = point_to_t(*end_xy)

    def sample(dt):
        ts = [t0 + dt * i / (n - 1) for i in range(n)]
        xs = [cx + a * math.cos(t) * cos_r - b * math.sin(t) * sin_r for t in ts]
        ys = [cy + a * math.cos(t) * sin_r + b * math.sin(t) * cos_r for t in ts]
        return xs, ys

    # Straight-line bounding box of start→end
    bb_x = (min(start_xy[0], end_xy[0]), max(start_xy[0], end_xy[0]))
    bb_y = (min(start_xy[1], end_xy[1]), max(start_xy[1], end_xy[1]))
    margin = max(abs(end_xy[0] - start_xy[0]), abs(end_xy[1] - start_xy[1])) * 0.5 + 0.01

    def arc_stays_near(xs, ys):
        """True if all sampled points stay within margin of the start-end straight line bbox."""
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


FILTER_STAGES = [
    ('Area Filter', 'Profiles passing area filter (area ≤ target × 1.01)'),
    ('Centroid Filter', 'Profiles passing centroid filter (centroid inside circle)'),
    ('Final Result', 'Profiles selected after all filters'),
]


def load_fixture(filepath):
    """Load and parse a JSON fixture file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def evaluate_filters(data):
    """
    Evaluate all filters for each profile (Area and Centroid).

    Returns dict mapping profile index to filter results.
    """
    circle = data['target_circle']
    profiles = data['profiles']

    circle_center_2d = tuple(circle['center_xy'])
    circle_radius = circle['radius_cm']
    target_area = circle['area_low']

    # Create 3D versions for distance calc
    class Point3D:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.z = 0

        def distanceTo(self, other):
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    circle_center_3d = Point3D(circle_center_2d[0], circle_center_2d[1])

    results = {}
    area_pass_indices = []

    # Stage 1: Area filter
    for i, profile in enumerate(profiles):
        area = profile['area_high_accuracy'] if 'area_high_accuracy' in profile else profile['area_low_accuracy']
        passes_area = area <= target_area * 1.01
        results[i] = {
            'area_pass': passes_area,
            'centroid_pass': False,
            'area': area,
        }
        if passes_area:
            area_pass_indices.append(i)

    # Stage 2: Centroid filter (only on area-passing profiles)
    for i in area_pass_indices:
        profile = profiles[i]
        centroid = tuple(profile['centroid_low_xy'])
        centroid_3d = Point3D(centroid[0], centroid[1])
        distance = circle_center_3d.distanceTo(centroid_3d)
        passes_centroid = distance <= circle_radius
        results[i]['centroid_pass'] = passes_centroid
        results[i]['centroid_distance'] = distance

    return results


def _build_results_table(profiles, filter_results, stage_idx, expected_result=None):
    """Build results table showing filter results."""
    stage_name = FILTER_STAGES[stage_idx][0]
    if expected_result is None:
        expected_result = []

    lines = [
        "╔" + "═" * 78 + "╗",
        f"║  Filter Stage: {stage_name:20s} ({stage_idx + 1}/3)  PASS/FAIL RESULTS".ljust(79) + "║",
        "╠" + "═" * 78 + "╣",
        "║  #  │    Area    │ Area │ Centroid │ Selected │ Notes".ljust(79) + "║",
        "╟" + "─" * 78 + "╢",
    ]

    for i, profile in enumerate(profiles):
        result = filter_results.get(i, {})
        area = result.get('area', profile.get('area_high_accuracy', profile.get('area_low_accuracy')))
        area_sym = "✓" if result.get('area_pass', False) else "✗"
        centroid_sym = "✓" if result.get('centroid_pass', False) else "✗"

        # Determine selection based on stage
        if stage_idx == 0:
            selected = result.get('area_pass', False)
        elif stage_idx == 1:
            selected = result.get('area_pass', False) and result.get('centroid_pass', False)
        else:  # Final (stage 2)
            selected = i in expected_result

        selected_sym = "YES" if selected else "NO"

        # Determine notes about why it might be rejected
        notes = ""
        if not result.get('area_pass', False):
            notes = "area too large"
        elif not result.get('centroid_pass', False):
            notes = "centroid outside"

        line = f"║  {i}  │ {area:9.4f} │  {area_sym}  │    {centroid_sym}    │   {selected_sym:3s}   │ {notes}".ljust(79) + "║"
        lines.append(line)

    lines.append("╚" + "═" * 78 + "╝")
    return lines


def _get_test_criteria(stage_idx):
    """Return text describing the test criteria for each stage."""
    criteria = {
        0: "Test: profile_area ≤ 1.01 × target_area",
        1: "Test: centroid_distance ≤ circle_radius",
        2: "Final: selected profiles from all filters"
    }
    return criteria.get(stage_idx, "")


def visualize_fixture_interactive(data, filepath):
    """Create interactive multi-stage visualization with keyboard navigation."""

    filter_results = evaluate_filters(data)
    profiles = data['profiles']
    circle = data['target_circle']
    circle_center = tuple(circle['center_xy'])
    circle_radius = circle['radius_cm']

    # Store current stage in a mutable container for the event handler
    state = {'stage': 2}  # Start at final result

    fig = plt.figure(figsize=(20, 16))

    def update_stage(stage_idx):
        """Update the visualization for a given stage."""
        fig.clear()  # Clear all axes

        stage_title, stage_desc = FILTER_STAGES[stage_idx]
        fig.suptitle(f"Profile Selection: {os.path.basename(filepath)}\n{data.get('description', '')}\n"
                     f"Stage {stage_idx + 1}/3: {stage_title}",
                     fontsize=14, fontweight='bold', x=0.75, ha='center')

        # Build and display results table
        table_lines = _build_results_table(profiles, filter_results, stage_idx, data.get('expected_result', []))
        table_text = '\n'.join(table_lines)
        fig.text(0.02, 0.98, table_text, ha='left', va='top', fontfamily='monospace',
                 fontsize=7, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # Navigation hint
        hint_text = "⬅️ ➡️ Arrow keys to navigate | ESC to close | Close window to continue"
        fig.text(0.5, 0.96, hint_text, ha='center', va='top', fontsize=9,
                 style='italic', color='darkblue')

        # Create 2x2 grid
        ax1 = plt.subplot(2, 2, 1)
        ax2 = plt.subplot(2, 2, 2)
        ax3 = plt.subplot(2, 2, 3)
        ax4 = plt.subplot(2, 2, 4)

        # Determine which profiles are selected at this stage
        selected_indices = set()
        for i, profile in enumerate(profiles):
            result = filter_results[i]
            if stage_idx == 0:
                if result['area_pass']:
                    selected_indices.add(i)
            elif stage_idx == 1:
                if result['area_pass'] and result['centroid_pass']:
                    selected_indices.add(i)
            else:  # Final (stage 2)
                if i in data['expected_result']:
                    selected_indices.add(i)

        _plot_all_profiles(ax1, circle_center, circle_radius, profiles, selected_indices,
                          title='All Profiles (Full View)', zoom=False, bbox_search_radius=None, stage_idx=stage_idx)

        _plot_filter_results(ax2, circle_center, circle_radius, profiles, selected_indices,
                           title='Selected Profiles (Full View)', zoom=False, bbox_search_radius=None, stage_idx=stage_idx)

        _plot_all_profiles(ax3, circle_center, circle_radius, profiles, selected_indices,
                          title=f'{stage_title} (Zoomed)', zoom=True,
                          zoom_radius=circle_radius * 1.5, bbox_search_radius=None, stage_idx=stage_idx)

        _plot_filter_results(ax4, circle_center, circle_radius, profiles, selected_indices,
                           title=f'{stage_title} Results (Zoomed)', zoom=True,
                           zoom_radius=circle_radius * 1.5, bbox_search_radius=None, stage_idx=stage_idx)

        plt.subplots_adjust(top=0.80, bottom=0.05, left=0.05, right=0.98, hspace=0.3, wspace=0.3)
        fig.canvas.draw()

    def on_key(event):
        if event.key == 'left':
            state['stage'] = max(0, state['stage'] - 1)
            update_stage(state['stage'])
        elif event.key == 'right':
            state['stage'] = min(2, state['stage'] + 1)
            update_stage(state['stage'])
        elif event.key == 'escape':
            plt.close(fig)

    # Draw initial stage
    update_stage(state['stage'])
    fig.canvas.mpl_connect('key_press_event', on_key)
    return fig


def _draw_curves(ax, profile_data, color, alpha=0.5):
    """
    Draw sketch geometry curves from profile data.

    Args:
        ax: matplotlib axis
        profile_data: dict with 'loops' key containing curve geometry
        color: color for drawing
        alpha: transparency level
    """
    if 'loops' not in profile_data:
        return

    for loop in profile_data['loops']:
        is_split = loop.get('has_weird_split', False)
        linestyle = '--' if is_split else '-'
        lw = 2.0 if is_split else 1.5

        for curve in loop['curves']:
            curve_type = curve.get('type')

            if curve_type == 'SketchLine':
                start = curve['start_xy']
                end = curve['end_xy']
                ax.plot([start[0], end[0]], [start[1], end[1]], color=color,
                        linewidth=lw, alpha=alpha, linestyle=linestyle)

            elif curve_type == 'SketchCircle':
                center = curve['center_xy']
                radius = curve['radius']
                circle_patch = patches.Circle(center, radius, fill=False, edgecolor=color,
                                            linewidth=lw, alpha=alpha, linestyle=linestyle)
                ax.add_patch(circle_patch)

            elif curve_type == 'SketchArc':
                center = curve['center_xy']
                radius = curve['radius']
                start = curve['start_xy']
                end = curve['end_xy']

                start_angle = math.degrees(math.atan2(start[1] - center[1], start[0] - center[0]))
                end_angle = math.degrees(math.atan2(end[1] - center[1], end[0] - center[0]))

                arc_patch = patches.Arc(center, radius * 2, radius * 2,
                                       angle=0, theta1=start_angle, theta2=end_angle,
                                       color=color, linewidth=lw, alpha=alpha, linestyle=linestyle)
                ax.add_patch(arc_patch)

            elif curve_type == 'SketchEllipticalArc':
                center = curve['center_xy']
                start = curve['start_xy']
                end = curve['end_xy']
                major = curve['major_axis_length']
                minor = curve['minor_axis_length']
                rotation = curve['rotation_angle']

                xs, ys = _sample_elliptical_arc(center, start, end, major, minor, rotation)
                ax.plot(xs, ys, color=color, linewidth=lw, alpha=alpha, linestyle=linestyle)

            elif curve_type == 'SketchEllipse':
                center = curve['center_xy']
                major = curve['major_axis_length']
                minor = curve['minor_axis_length']
                rotation = math.degrees(curve['rotation_angle'])

                ellipse_patch = patches.Ellipse(center, major, minor,
                                                angle=rotation, fill=False, edgecolor=color,
                                                linewidth=lw, alpha=alpha, linestyle=linestyle)
                ax.add_patch(ellipse_patch)


def _plot_all_profiles(ax, circle_center, circle_radius, profiles, selected_indices,
                       title='Profiles', zoom=False, zoom_radius=None, bbox_search_radius=None, stage_idx=None):
    """Draw all profiles with bounding boxes and color-coded markers."""
    ax.set_aspect('equal')
    ax.set_title(title, fontweight='bold')

    # Add test criteria text
    test_criteria = _get_test_criteria(stage_idx)
    if test_criteria:
        ax.text(0.02, 0.98, test_criteria, transform=ax.transAxes,
               ha='left', va='top', fontsize=8, bbox=dict(boxstyle='round',
               facecolor='lightyellow', alpha=0.7), family='monospace')

    circle_patch = patches.Circle(circle_center, circle_radius,
                                   fill=False, edgecolor='black', linewidth=2, label='Target Circle')
    ax.add_patch(circle_patch)

    if bbox_search_radius:
        bbox_patch = patches.Rectangle(
            (circle_center[0] - bbox_search_radius, circle_center[1] - bbox_search_radius),
            bbox_search_radius * 2, bbox_search_radius * 2,
            fill=False, edgecolor='blue', linewidth=1.5, linestyle=':', alpha=0.7, label='BBox Search (1.1x)'
        )
        ax.add_patch(bbox_patch)

    colors = plt.cm.tab10(range(min(10, len(profiles))))
    for i, profile in enumerate(profiles):
        color = colors[i % len(colors)]

        # Draw sketch geometry curves
        _draw_curves(ax, profile, color, alpha=0.6)

        # Draw bounding box
        bbox = profile['bbox']
        min_xy = tuple(bbox['min_xy'])
        max_xy = tuple(bbox['max_xy'])
        width = max_xy[0] - min_xy[0]
        height = max_xy[1] - min_xy[1]

        bbox_patch = patches.Rectangle(min_xy, width, height,
                                       fill=False, edgecolor=color, linewidth=1.5,
                                       linestyle='--', alpha=0.4, label=f'Profile {i}')
        ax.add_patch(bbox_patch)

        centroid = tuple(profile['centroid_low_xy'])
        ax.plot(centroid[0], centroid[1], '+', color=color, markersize=12, markeredgewidth=2)
        ax.text(centroid[0] + 0.05, centroid[1] + 0.05, f'{i}', fontsize=9, ha='left', color=color, fontweight='bold')

    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Y (cm)')

    if zoom and zoom_radius:
        margin = circle_radius * 0.3
        ax.set_xlim(circle_center[0] - zoom_radius - margin, circle_center[0] + zoom_radius + margin)
        ax.set_ylim(circle_center[1] - zoom_radius - margin, circle_center[1] + zoom_radius + margin)
    else:
        all_bounds = [circle_center[0] - circle_radius, circle_center[0] + circle_radius,
                      circle_center[1] - circle_radius, circle_center[1] + circle_radius]
        for profile in profiles:
            bbox = profile['bbox']
            all_bounds[0] = min(all_bounds[0], bbox['min_xy'][0])
            all_bounds[1] = max(all_bounds[1], bbox['max_xy'][0])
            all_bounds[2] = min(all_bounds[2], bbox['min_xy'][1])
            all_bounds[3] = max(all_bounds[3], bbox['max_xy'][1])

        margin = 0.5
        ax.set_xlim(all_bounds[0] - margin, all_bounds[1] + margin)
        ax.set_ylim(all_bounds[2] - margin, all_bounds[3] + margin)


def _plot_filter_results(ax, circle_center, circle_radius, profiles, selected_indices,
                        title='Selected Profiles', zoom=False, zoom_radius=None, bbox_search_radius=None, stage_idx=None):
    """Draw filter results with green (selected) and red (rejected) boxes."""
    ax.set_aspect('equal')
    ax.set_title(title, fontweight='bold')

    # Add test criteria text
    test_criteria = _get_test_criteria(stage_idx)
    if test_criteria:
        ax.text(0.02, 0.98, test_criteria, transform=ax.transAxes,
               ha='left', va='top', fontsize=8, bbox=dict(boxstyle='round',
               facecolor='lightyellow', alpha=0.7), family='monospace')

    circle_patch = patches.Circle(circle_center, circle_radius,
                                   fill=False, edgecolor='black', linewidth=2,
                                   linestyle='--', label='Target Circle')
    ax.add_patch(circle_patch)

    if bbox_search_radius:
        bbox_patch = patches.Rectangle(
            (circle_center[0] - bbox_search_radius, circle_center[1] - bbox_search_radius),
            bbox_search_radius * 2, bbox_search_radius * 2,
            fill=False, edgecolor='blue', linewidth=1.5, linestyle=':', alpha=0.7, label='BBox Search (1.1x)'
        )
        ax.add_patch(bbox_patch)

    for i, profile in enumerate(profiles):
        is_selected = i in selected_indices
        color = 'green' if is_selected else 'red'
        alpha = 0.6 if is_selected else 0.3

        # Draw sketch geometry curves
        _draw_curves(ax, profile, color, alpha=alpha)

        # Draw bounding box (lighter for visual hierarchy)
        bbox = profile['bbox']
        min_xy = tuple(bbox['min_xy'])
        max_xy = tuple(bbox['max_xy'])
        width = max_xy[0] - min_xy[0]
        height = max_xy[1] - min_xy[1]

        bbox_patch = patches.Rectangle(min_xy, width, height,
                                       fill=True, facecolor=color, alpha=alpha * 0.4,
                                       edgecolor=color, linewidth=1.5, linestyle='--')
        ax.add_patch(bbox_patch)

        centroid = tuple(profile['centroid_low_xy'])
        ax.plot(centroid[0], centroid[1], '+', color=color, markersize=12, markeredgewidth=2)
        ax.text(centroid[0] + 0.05, centroid[1] + 0.05, f'{i}', fontsize=9, ha='left',
               color=color, fontweight='bold')

    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='green', alpha=0.6, edgecolor='green', label='Selected'),
                       Patch(facecolor='red', alpha=0.3, edgecolor='red', label='Rejected')]
    ax.legend(handles=legend_elements, loc='best', fontsize=9)

    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (cm)')
    ax.set_ylabel('Y (cm)')

    if zoom and zoom_radius:
        margin = circle_radius * 0.3
        ax.set_xlim(circle_center[0] - zoom_radius - margin, circle_center[0] + zoom_radius + margin)
        ax.set_ylim(circle_center[1] - zoom_radius - margin, circle_center[1] + zoom_radius + margin)
    else:
        all_bounds = [circle_center[0] - circle_radius, circle_center[0] + circle_radius,
                      circle_center[1] - circle_radius, circle_center[1] + circle_radius]
        for profile in profiles:
            bbox = profile['bbox']
            all_bounds[0] = min(all_bounds[0], bbox['min_xy'][0])
            all_bounds[1] = max(all_bounds[1], bbox['max_xy'][0])
            all_bounds[2] = min(all_bounds[2], bbox['min_xy'][1])
            all_bounds[3] = max(all_bounds[3], bbox['max_xy'][1])

        margin = 0.5
        ax.set_xlim(all_bounds[0] - margin, all_bounds[1] + margin)
        ax.set_ylim(all_bounds[2] - margin, all_bounds[3] + margin)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_profiles.py <fixture_file_or_dir>")
        print("  fixture_file: path to a single .json fixture")
        print("  fixture_dir:  path to directory of .json fixtures")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.json")))
        if not files:
            print(f"No JSON files found in {path}")
            sys.exit(1)
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

    for fixture_file in files:
        try:
            print(f"\nProcessing: {fixture_file}")
            data = load_fixture(fixture_file)
            fig = visualize_fixture_interactive(data, fixture_file)
        except Exception as e:
            print(f"Error processing {fixture_file}: {e}")
            import traceback
            traceback.print_exc()
            continue

    plt.show()


if __name__ == '__main__':
    main()
