"""
Generate a NACA 4-digit airfoil surface as a binary/ASCII STL for use with
OpenFOAM's snappyHexMesh (2D case: extruded slightly beyond the domain
thickness so no end caps are needed).

Usage:
    python3 make_naca_stl.py
"""

import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("aoa", type=float, help="angle of attack (degrees)")
parser.add_argument("outfile", type=str, help="output STL file path")
args = parser.parse_args()

# ---------------------------------------------------------------------
# User-editable parameters
# ---------------------------------------------------------------------
NACA = "0012"        # 4-digit NACA designation
CHORD = 1.0           # chord length
N_POINTS = 200         # points along each surface (LE to TE)
SPAN_HALF = 1.0        # extrude from -SPAN_HALF to +SPAN_HALF in z
                        # (must exceed your blockMesh domain half-thickness)
OUT_FILE = args.outfile
PATCH_NAME = "airfoil"
AOA =   -args.aoa             # angle of attack (degrees)


def naca4_coords(code, chord, n):
    m = int(code[0]) / 100.0        # max camber
    p = int(code[1]) / 10.0         # location of max camber
    t = int(code[2:4]) / 100.0      # max thickness

    # cosine spacing -> clusters points near LE and TE
    beta = np.linspace(0.0, np.pi, n)
    x = (1 - np.cos(beta)) / 2.0    # 0..1

    # thickness distribution (standard NACA4 formula, closed TE variant)
    yt = 5 * t * (0.2969 * np.sqrt(x)
                  - 0.1260 * x
                  - 0.3516 * x**2
                  + 0.2843 * x**3
                  - 0.1015 * x**4)

    if p == 0 or m == 0:
        yc = np.zeros_like(x)
        dyc_dx = np.zeros_like(x)
    else:
        yc = np.where(
            x < p,
            m / p**2 * (2 * p * x - x**2),
            m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * x - x**2),
        )
        dyc_dx = np.where(
            x < p,
            2 * m / p**2 * (p - x),
            2 * m / (1 - p)**2 * (p - x),
        )

    theta = np.arctan(dyc_dx)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    # Build a single closed loop: TE -> upper surface -> LE -> lower surface -> TE
    x_up = xu[::-1]
    y_up = yu[::-1]
    x_lo = xl[1:]
    y_lo = yl[1:]

    xs = np.concatenate([x_up, x_lo]) * chord
    ys = np.concatenate([y_up, y_lo]) * chord

    return xs, ys

PIVOT_X = 0.25 * CHORD   # quarter-chord is the typical AoA pivot; use 0.5*CHORD for mid-chord, or 0.0 for LE

def rotate(aoa, xs, ys, pivot_x=0.0, pivot_y=0.0):
    """Rotate the airfoil coordinates by AoA (degrees) about (pivot_x, pivot_y)."""
    aoa_rad = np.radians(aoa)
    cos_aoa = np.cos(aoa_rad)
    sin_aoa = np.sin(aoa_rad)

    # shift so pivot is at origin
    xs_shifted = xs - pivot_x
    ys_shifted = ys - pivot_y

    x_rot = xs_shifted * cos_aoa - ys_shifted * sin_aoa
    y_rot = xs_shifted * sin_aoa + ys_shifted * cos_aoa

    # shift back
    x_rot += pivot_x
    y_rot += pivot_y
    return x_rot, y_rot

def write_stl(xs, ys, z_lo, z_hi, patch_name, out_file):
    n = len(xs)
    facets = []

    for i in range(n - 1):
        x1, y1 = xs[i], ys[i]
        x2, y2 = xs[i + 1], ys[i + 1]

        p1 = (x1, y1, z_lo)
        p2 = (x2, y2, z_lo)
        p3 = (x2, y2, z_hi)
        p4 = (x1, y1, z_hi)

        # outward normal (rough, snappyHexMesh recomputes anyway but
        # good STL hygiene): perpendicular to the segment in the xy-plane
        dx, dy = x2 - x1, y2 - y1
        nx, ny = dy, -dx
        norm = np.hypot(nx, ny)
        if norm > 1e-12:
            nx, ny = nx / norm, ny / norm
        else:
            nx, ny = 0.0, 0.0

        facets.append((nx, ny, 0.0, p1, p2, p3))
        facets.append((nx, ny, 0.0, p1, p3, p4))

    with open(out_file, "w") as f:
        f.write(f"solid {patch_name}\n")
        for nx, ny, nz, p1, p2, p3 in facets:
            f.write(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}\n")
            f.write("    outer loop\n")
            for p in (p1, p2, p3):
                f.write(f"      vertex {p[0]:.6e} {p[1]:.6e} {p[2]:.6e}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write(f"endsolid {patch_name}\n")


if __name__ == "__main__":
    xs, ys = naca4_coords(NACA, CHORD, N_POINTS)
    xs_rot, ys_rot = rotate(AOA, xs, ys, pivot_x=PIVOT_X, pivot_y=0.0)
    write_stl(xs_rot, ys_rot, -SPAN_HALF, SPAN_HALF, PATCH_NAME, OUT_FILE)
    print(f"Wrote {OUT_FILE}")
    print(f"Points per surface loop: {len(xs)}")
    print(f"x range: [{xs.min():.4f}, {xs.max():.4f}]")
    print(f"y range: [{ys.min():.4f}, {ys.max():.4f}]")