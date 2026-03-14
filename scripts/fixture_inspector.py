#!/usr/bin/env python3
"""
Interactive Fixture Inspector
- Up/Down arrows: Navigate between profiles
- Left/Right arrows: Navigate between curves within a profile
- Space: Toggle centroid display
- C: Toggle curve numbers
- ESC: Exit
"""

import json
import sys
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import TextBox


def _sample_elliptical_arc(center, start_xy, end_xy, major, minor, rotation_rad, n=15):
    """Sample n points along a rotated elliptical arc, returns (xs, ys)."""
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
    dt = (t1 - t0) % (2 * math.pi)
    if dt > math.pi:
        dt -= 2 * math.pi

    ts = [t0 + dt * i / (n - 1) for i in range(n)]
    xs = [cx + a * math.cos(t) * cos_r - b * math.sin(t) * sin_r for t in ts]
    ys = [cy + a * math.cos(t) * sin_r + b * math.sin(t) * cos_r for t in ts]
    return xs, ys


class FixtureInspector:
    def __init__(self, fixture_path):
        with open(fixture_path, 'r') as f:
            self.data = json.load(f)

        self.profiles = self.data['profiles']
        self.target_circle = self.data['target_circle']

        self.profile_idx = 0
        self.curve_idx = 0
        self.show_centroid = True
        self.show_curve_numbers = True

        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        self.draw()

    def get_current_profile(self):
        return self.profiles[self.profile_idx]

    def get_all_curves(self):
        """Get all curves from all loops in current profile"""
        profile = self.get_current_profile()
        all_curves = []
        for loop_idx, loop in enumerate(profile['loops']):
            for curve in loop['curves']:
                all_curves.append({
                    'curve': curve,
                    'loop_idx': loop_idx,
                    'global_idx': len(all_curves)
                })
        return all_curves

    def draw(self):
        self.ax.clear()

        profile = self.get_current_profile()
        all_curves = self.get_all_curves()

        # Draw target circle
        target = self.target_circle
        circle = patches.Circle(
            target['center_xy'],
            target['radius_cm'],
            fill=False,
            edgecolor='gray',
            linestyle='--',
            linewidth=1.5,
            alpha=0.5
        )
        self.ax.add_patch(circle)

        # Draw all curves
        for item in all_curves:
            curve = item['curve']
            is_highlighted = (item['global_idx'] == self.curve_idx)

            color = 'red' if is_highlighted else 'black'
            linewidth = 3 if is_highlighted else 1.5

            if curve['type'] == 'SketchLine':
                start = curve['start_xy']
                end = curve['end_xy']
                self.ax.plot([start[0], end[0]], [start[1], end[1]],
                           color=color, linewidth=linewidth, zorder=10 if is_highlighted else 5)

                # Label if showing curve numbers
                if self.show_curve_numbers and is_highlighted:
                    mid_x = (start[0] + end[0]) / 2
                    mid_y = (start[1] + end[1]) / 2
                    self.ax.text(mid_x, mid_y, f'  C{item["global_idx"]}',
                               fontsize=10, color='red', weight='bold')

            elif curve['type'] == 'SketchCircle':
                circ = patches.Circle(
                    curve['center_xy'],
                    curve['radius'],
                    fill=False,
                    edgecolor=color,
                    linewidth=linewidth,
                    zorder=10 if is_highlighted else 5
                )
                self.ax.add_patch(circ)

                if self.show_curve_numbers and is_highlighted:
                    self.ax.text(curve['center_xy'][0], curve['center_xy'][1],
                               f' C{item["global_idx"]}', fontsize=10, color='red', weight='bold')

            elif curve['type'] == 'SketchArc':
                center = curve['center_xy']
                radius = curve['radius']
                start = curve['start_xy']
                end = curve['end_xy']

                start_angle = math.degrees(math.atan2(start[1] - center[1], start[0] - center[0]))
                end_angle = math.degrees(math.atan2(end[1] - center[1], end[0] - center[0]))

                arc = patches.Arc(center, radius * 2, radius * 2,
                               angle=0, theta1=start_angle, theta2=end_angle,
                               color=color, linewidth=linewidth, zorder=10 if is_highlighted else 5)
                self.ax.add_patch(arc)

                if self.show_curve_numbers and is_highlighted:
                    self.ax.text(center[0], center[1], f'  C{item["global_idx"]}',
                               fontsize=10, color='red', weight='bold')

            elif curve['type'] == 'SketchEllipticalArc':
                center = curve['center_xy']
                major = curve['major_axis_length']
                minor = curve['minor_axis_length']
                rotation = curve['rotation_angle']
                start = curve['start_xy']
                end = curve['end_xy']

                xs, ys = _sample_elliptical_arc(center, start, end, major, minor, rotation)
                self.ax.plot(xs, ys, color=color, linewidth=linewidth,
                             zorder=10 if is_highlighted else 5)

                if self.show_curve_numbers and is_highlighted:
                    mid = len(xs) // 2
                    self.ax.text(xs[mid], ys[mid], f'  C{item["global_idx"]}',
                               fontsize=10, color='red', weight='bold')

            elif curve['type'] == 'SketchEllipse':
                center = curve['center_xy']
                major = curve['major_axis_length']
                minor = curve['minor_axis_length']
                rotation = math.degrees(curve['rotation_angle'])

                ellipse_patch = patches.Ellipse(center, major, minor,
                                                angle=rotation, fill=False, edgecolor=color,
                                                linewidth=linewidth, zorder=10 if is_highlighted else 5)
                self.ax.add_patch(ellipse_patch)

                if self.show_curve_numbers and is_highlighted:
                    self.ax.text(center[0], center[1], f'  C{item["global_idx"]}',
                               fontsize=10, color='red', weight='bold')

        # Draw centroid if enabled
        if self.show_centroid:
            centroid = profile['centroid_low_xy']
            self.ax.plot(centroid[0], centroid[1], 'g+', markersize=15, markeredgewidth=2)

        # Title and info
        current_curve = all_curves[self.curve_idx] if all_curves else None
        curve_info = ""
        if current_curve:
            c = current_curve['curve']
            if c['type'] == 'SketchLine':
                curve_info = f"  | Curve {self.curve_idx}: LINE from ({c['start_xy'][0]:.3f}, {c['start_xy'][1]:.3f}) to ({c['end_xy'][0]:.3f}, {c['end_xy'][1]:.3f})"
            elif c['type'] == 'SketchCircle':
                curve_info = f"  | Curve {self.curve_idx}: CIRCLE at ({c['center_xy'][0]:.3f}, {c['center_xy'][1]:.3f}), r={c['radius']:.3f}"
            elif c['type'] == 'SketchArc':
                curve_info = f"  | Curve {self.curve_idx}: ARC at ({c['center_xy'][0]:.3f}, {c['center_xy'][1]:.3f}), r={c['radius']:.3f}"
            elif c['type'] == 'SketchEllipticalArc':
                curve_info = f"  | Curve {self.curve_idx}: ELLIPTICAL_ARC at ({c['center_xy'][0]:.3f}, {c['center_xy'][1]:.3f}), major={c['major_axis_length']:.3f}, minor={c['minor_axis_length']:.3f}"
            elif c['type'] == 'SketchEllipse':
                curve_info = f"  | Curve {self.curve_idx}: ELLIPSE at ({c['center_xy'][0]:.3f}, {c['center_xy'][1]:.3f}), major={c['major_axis_length']:.3f}, minor={c['minor_axis_length']:.3f}"

        title = f"Profile {self.profile_idx}/{len(self.profiles)-1} (Area: {profile['area_low_accuracy']:.4f} cm²)"
        title += f"  | {len(all_curves)} curves" + curve_info

        self.ax.set_title(title, fontsize=11, loc='left')

        # Set equal aspect and grid
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('X (cm)')
        self.ax.set_ylabel('Y (cm)')

        # Auto-scale
        if all_curves:
            xs = []
            ys = []
            for item in all_curves:
                c = item['curve']
                if c['type'] == 'SketchLine':
                    xs.extend([c['start_xy'][0], c['end_xy'][0]])
                    ys.extend([c['start_xy'][1], c['end_xy'][1]])
                elif c['type'] == 'SketchCircle':
                    xs.append(c['center_xy'][0])
                    ys.append(c['center_xy'][1])

            if xs and ys:
                margin = 0.5
                self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
                self.ax.set_ylim(min(ys) - margin, max(ys) + margin)

        # Info text
        info = "↑↓ Profile | ← → Curve | SPACE Centroid | C Labels | ESC Exit"
        self.ax.text(0.01, 0.99, info, transform=self.ax.transAxes,
                    fontsize=9, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        self.fig.canvas.draw()

    def on_key(self, event):
        if event.key == 'up':
            self.profile_idx = (self.profile_idx + 1) % len(self.profiles)
            self.curve_idx = 0
            self.draw()

        elif event.key == 'down':
            self.profile_idx = (self.profile_idx - 1) % len(self.profiles)
            self.curve_idx = 0
            self.draw()

        elif event.key == 'right':
            all_curves = self.get_all_curves()
            if all_curves:
                self.curve_idx = (self.curve_idx + 1) % len(all_curves)
                self.draw()

        elif event.key == 'left':
            all_curves = self.get_all_curves()
            if all_curves:
                self.curve_idx = (self.curve_idx - 1) % len(all_curves)
                self.draw()

        elif event.key == ' ':
            self.show_centroid = not self.show_centroid
            self.draw()

        elif event.key == 'c':
            self.show_curve_numbers = not self.show_curve_numbers
            self.draw()

        elif event.key == 'escape':
            plt.close()
            sys.exit(0)

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: fixture_inspector.py <path-to-fixture.json>")
        sys.exit(1)
    fixture = sys.argv[1]

    inspector = FixtureInspector(fixture)
    plt.show()
