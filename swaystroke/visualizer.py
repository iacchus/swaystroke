"""
visualizer.py
-------------
Renders a gesture path using the best available backend:

    1. Tkinter  – stdlib, zero extra deps (needs `python3-tk` / `tk` system pkg)
    2. Matplotlib – `pip install matplotlib`
    3. ASCII     – always works, no dependencies at all

The correct backend is chosen automatically at runtime; you never need to
change this file.

Usage
-----
    from visualizer import GestureVisualizer

    vis = GestureVisualizer()
    vis.show(points, title="My gesture")
    vis.show_comparison(recorded, template, template_name="swipe-right", score=0.93)
"""

from __future__ import annotations

from typing import Optional


# ── backend probe ─────────────────────────────────────────────────────────────

def _detect_backend() -> str:
    """Return the name of the best available visualisation backend."""
    # Probe _tkinter (the C extension that loads libtk*.so) directly.
    # This is cheaper than creating a Tk() window and avoids any display
    # connection.  A missing shared-library shows up as ImportError here.
    try:
        import _tkinter  # noqa: F401
        import tkinter   # noqa: F401 – also check the Python wrapper
        return "tkinter"
    except Exception:
        pass

    # Try Matplotlib
    try:
        import matplotlib  # noqa: F401
        return "matplotlib"
    except ImportError:
        pass

    return "ascii"


_BACKEND: Optional[str] = None   # lazily resolved on first use


def _backend() -> str:
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = _detect_backend()
        print(f"[visualizer] Using backend: {_BACKEND}")
    return _BACKEND


# ── shared geometry helpers ───────────────────────────────────────────────────

def _fit(
    pts: list[tuple],
    w: int | float,
    h: int | float,
    pad: int | float,
) -> list[tuple[float, float]]:
    """Scale+centre *pts* into (pad, pad) … (w-pad, h-pad)."""
    if not pts:
        return []
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1e-6
    span_y = max_y - min_y or 1e-6
    scale  = min((w - 2 * pad) / span_x, (h - 2 * pad) / span_y)
    off_x  = pad + ((w - 2 * pad) - span_x * scale) / 2
    off_y  = pad + ((h - 2 * pad) - span_y * scale) / 2
    return [((p[0] - min_x) * scale + off_x,
             (p[1] - min_y) * scale + off_y) for p in pts]


# ── Tkinter backend ───────────────────────────────────────────────────────────

def _tk_show(
    points: list[tuple],
    title: str,
    score: Optional[float],
) -> None:
    import tkinter as tk

    W, H, PAD = 500, 400, 30
    BG = "#1e1e2e"; GRID = "#2a2a3e"
    PATH_COL = "#89b4fa"; POINT_COL = "#f38ba8"; END_COL = "#fab387"
    TEXT_COL = "#cdd6f4"

    root = tk.Tk()
    root.title(title)
    root.configure(bg=BG)
    root.resizable(False, False)
    c = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
    c.pack()

    for x in range(0, W, 40):
        c.create_line(x, 0, x, H, fill=GRID, width=1)
    for y in range(0, H, 40):
        c.create_line(0, y, W, y, fill=GRID, width=1)

    fitted = _fit(points, W, H, PAD)
    if len(fitted) >= 2:
        flat = [coord for p in fitted for coord in p]
        c.create_line(*flat, fill=PATH_COL, width=2, capstyle=tk.ROUND,
                      joinstyle=tk.ROUND)
        r = 4
        x0, y0 = fitted[0]
        c.create_oval(x0-r, y0-r, x0+r, y0+r, fill=POINT_COL, outline="")
        xn, yn = fitted[-1]
        c.create_oval(xn-r, yn-r, xn+r, yn+r, fill=END_COL, outline="")

    if score is not None:
        c.create_text(W - PAD, PAD, text=f"score: {score:.3f}",
                      fill=TEXT_COL, anchor="ne", font=("monospace", 11, "bold"))
    c.create_text(W//2, H - 12,
                  text="● start   ● end   (close window to continue)",
                  fill=GRID, font=("monospace", 9))
    root.mainloop()


def _tk_show_comparison(
    recorded: list[tuple],
    template: list[tuple],
    template_name: str,
    score: Optional[float],
) -> None:
    import tkinter as tk

    W, H, PAD = 500, 400, 30
    BG = "#1e1e2e"; GRID = "#2a2a3e"
    PATH_COL = "#89b4fa"; TMPL_COL = "#a6e3a1"; TEXT_COL = "#cdd6f4"
    POINT_COL = "#f38ba8"; END_COL = "#fab387"

    root = tk.Tk()
    root.title("Gesture comparison")
    root.configure(bg=BG)
    root.resizable(False, False)
    c = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
    c.pack()

    for x in range(0, W, 40):
        c.create_line(x, 0, x, H, fill=GRID, width=1)
    for y in range(0, H, 40):
        c.create_line(0, y, W, y, fill=GRID, width=1)

    half = W // 2
    c.create_line(half, PAD//2, half, H - PAD//2, fill=GRID, width=1, dash=(4, 4))

    def draw(pts, color, x_offset=0):
        fitted = _fit(pts, half, H, PAD)
        fitted = [(x + x_offset, y) for x, y in fitted]
        if len(fitted) >= 2:
            flat = [coord for p in fitted for coord in p]
            c.create_line(*flat, fill=color, width=2, capstyle=tk.ROUND,
                          joinstyle=tk.ROUND)
            r = 4
            x0, y0 = fitted[0]
            c.create_oval(x0-r, y0-r, x0+r, y0+r, fill=POINT_COL, outline="")
            xn, yn = fitted[-1]
            c.create_oval(xn-r, yn-r, xn+r, yn+r, fill=END_COL, outline="")

    draw(recorded, PATH_COL, 0)
    draw(template, TMPL_COL, half)

    c.create_text(PAD, PAD//2, text="recorded", fill=PATH_COL,
                  anchor="w", font=("monospace", 9))
    c.create_text(half + PAD, PAD//2, text=template_name, fill=TMPL_COL,
                  anchor="w", font=("monospace", 9))
    if score is not None:
        c.create_text(W//2, H - 12, text=f"score: {score:.3f}",
                      fill=TEXT_COL, font=("monospace", 11, "bold"))
    root.mainloop()


# ── Matplotlib backend ────────────────────────────────────────────────────────

def _mpl_show(
    points: list[tuple],
    title: str,
    score: Optional[float],
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 5), facecolor="#1e1e2e")
    ax.set_facecolor("#1e1e2e")
    ax.set_title(
        title + (f"  —  score: {score:.3f}" if score is not None else ""),
        color="#cdd6f4", fontsize=11,
    )
    ax.tick_params(colors="#2a2a3e")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a2a3e")
    ax.grid(color="#2a2a3e", linewidth=0.5)

    if points:
        xs, ys = zip(*points)
        ys = [-y for y in ys]   # flip Y so "up" is up
        ax.plot(xs, ys, color="#89b4fa", linewidth=2)
        ax.plot(xs[0], ys[0], "o", color="#f38ba8", markersize=8, label="start")
        ax.plot(xs[-1], ys[-1], "o", color="#fab387", markersize=8, label="end")
        ax.legend(facecolor="#2a2a3e", labelcolor="#cdd6f4")

    ax.set_aspect("equal", "box")
    plt.tight_layout()
    plt.show()


def _mpl_show_comparison(
    recorded: list[tuple],
    template: list[tuple],
    template_name: str,
    score: Optional[float],
) -> None:
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor="#1e1e2e")
    fig.suptitle(
        f"Comparison  —  score: {score:.3f}" if score is not None else "Comparison",
        color="#cdd6f4", fontsize=12,
    )

    for ax, pts, color, label in [
        (ax1, recorded, "#89b4fa", "recorded"),
        (ax2, template, "#a6e3a1", template_name),
    ]:
        ax.set_facecolor("#1e1e2e")
        ax.set_title(label, color=color)
        ax.grid(color="#2a2a3e", linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2a2a3e")
        if pts:
            xs, ys = zip(*pts)
            ys = [-y for y in ys]
            ax.plot(xs, ys, color=color, linewidth=2)
            ax.plot(xs[0], ys[0], "o", color="#f38ba8", markersize=8)
            ax.plot(xs[-1], ys[-1], "o", color="#fab387", markersize=8)
        ax.set_aspect("equal", "box")

    plt.tight_layout()
    plt.show()


# ── ASCII backend ─────────────────────────────────────────────────────────────

def _ascii_show(
    points: list[tuple],
    title: str,
    score: Optional[float],
) -> None:
    W, H = 60, 20
    grid = [["·"] * W for _ in range(H)]

    fitted = _fit(points, W - 1, H - 1, 1)
    for i, (px, py) in enumerate(fitted):
        x, y = int(round(px)), int(round(py))
        x = max(0, min(W - 1, x))
        y = max(0, min(H - 1, y))
        if i == 0:
            grid[y][x] = "S"
        elif i == len(fitted) - 1:
            grid[y][x] = "E"
        else:
            grid[y][x] = "█"

    border = "─" * (W + 2)
    score_str = f"  score: {score:.3f}" if score is not None else ""
    print(f"\n┌{border}┐")
    print(f"│  {title}{score_str:<{W - len(title)}}│")
    print(f"├{border}┤")
    for row in grid:
        print("│ " + "".join(row) + " │")
    print(f"└{border}┘")
    print("  S=start  E=end\n")


def _ascii_show_comparison(
    recorded: list[tuple],
    template: list[tuple],
    template_name: str,
    score: Optional[float],
) -> None:
    print(f"\n── Recorded ──────────────")
    _ascii_show(recorded, "recorded", None)
    print(f"── Template: {template_name} ──")
    _ascii_show(template, template_name, score)


# ── public facade ─────────────────────────────────────────────────────────────

class GestureVisualizer:
    """
    Backend-agnostic gesture visualizer.

    Tries Tkinter → Matplotlib → ASCII in order and uses the first one that
    works.  Install hints are printed when falling back.
    """

    def show(
        self,
        points: list[tuple],
        title: str = "Gesture",
        score: Optional[float] = None,
    ) -> None:
        b = _backend()
        if b == "tkinter":
            _tk_show(points, title, score)
        elif b == "matplotlib":
            _mpl_show(points, title, score)
        else:
            _ascii_show(points, title, score)
            print(
                "[visualizer] For a graphical view install either:\n"
                "  • Tkinter:     sudo apt install python3-tk   (Debian/Ubuntu)\n"
                "                 sudo pacman -S tk              (Arch)\n"
                "  • Matplotlib:  pip install matplotlib\n"
            )

    def show_comparison(
        self,
        recorded: list[tuple],
        template: list[tuple],
        template_name: str = "template",
        score: Optional[float] = None,
    ) -> None:
        b = _backend()
        if b == "tkinter":
            _tk_show_comparison(recorded, template, template_name, score)
        elif b == "matplotlib":
            _mpl_show_comparison(recorded, template, template_name, score)
        else:
            _ascii_show_comparison(recorded, template, template_name, score)
            print(
                "[visualizer] For a graphical view install either:\n"
                "  • Tkinter:     sudo apt install python3-tk   (Debian/Ubuntu)\n"
                "                 sudo pacman -S tk              (Arch)\n"
                "  • Matplotlib:  pip install matplotlib\n"
            )
