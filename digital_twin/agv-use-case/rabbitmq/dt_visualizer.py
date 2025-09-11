"""
dt_visualizer.py — Live visualization for AGV telemetry

- Runs a separate process hosting a matplotlib window
- Receives frames via multiprocessing.Queue:
  { sim_time, x, y, theta, tx, ty, v, soc, reached, agv_id }
- Renders:
  - AGV pose (triangle arrow)
  - Target marker (X)
  - Trail (path history)
  - HUD text: v, SoC, sim_time, AGV id

Usage from client:
    from dt_visualizer import start_visualizer, send_to_visualizer, stop_visualizer
    proc, q = start_visualizer()
    send_to_visualizer(q, {...})
    stop_visualizer(q)
"""

from multiprocessing import Process, Queue
from queue import Empty as QueueEmpty
from typing import Any, Dict, Tuple, Optional
import math
import time

def _run_visualizer(queue: Queue, window_title: str = "AGV Live") -> None:
    # Import matplotlib in the child process to avoid backend issues
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    plt.rcParams["toolbar"] = "toolmanager"
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.canvas.manager.set_window_title(window_title)

    # Plot artists
    agv_body, = ax.plot([], [], lw=2)              # triangle outline
    trail, = ax.plot([], [], lw=1, alpha=0.6)      # path trail
    tgt_scatter = ax.scatter([], [], marker="x", s=80)  # target
    hud_text = ax.text(0.02, 0.98, "", transform=ax.transAxes,
                       va="top", ha="left", fontsize=10)

    # State
    state = {
        "x": 0.0, "y": 0.0, "theta": 0.0,
        "tx": None, "ty": None,
        "v": 0.0, "soc": 1.0, "sim_time": 0.0,
        "agv_id": "AGV",
        "trail": [],  # list of (x,y)
        "reached": False,
        "last_update": time.time(),
    }

    # Axes setup
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-1, 7)
    ax.set_ylim(-1, 7)
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_title("Simulation Bridge — AGV Telemetry")

    def triangle_at(x: float, y: float, theta: float, scale: float = 0.3) -> Tuple[list, list]:
        # Simple isosceles triangle centered at (x,y) with heading theta
        # Points in body frame
        pts = [
            (scale, 0.0),
            (-scale * 0.6, scale * 0.4),
            (-scale * 0.6, -scale * 0.4),
            (scale, 0.0),
        ]
        ct, st = math.cos(theta), math.sin(theta)
        xs = [x + ct*px - st*py for (px, py) in pts]
        ys = [y + st*px + ct*py for (px, py) in pts]
        return xs, ys

    def drain_queue() -> Optional[Dict[str, Any]]:
        """Drain queue and return the most recent payload (if any)."""
        latest = None
        while True:
            try:
                item = queue.get_nowait()
                latest = item
            except QueueEmpty:
                break
        return latest

    def on_update(frame):
        # Read most recent update
        msg = drain_queue()
        if msg is None:
            return agv_body, trail, tgt_scatter, hud_text

        if isinstance(msg, dict) and msg.get("_cmd") == "stop":
            plt.close(fig)
            return agv_body, trail, tgt_scatter, hud_text

        # Update state
        x = msg.get("x", state["x"])
        y = msg.get("y", state["y"])
        theta = msg.get("theta", state["theta"])
        tx = msg.get("tx", state["tx"])
        ty = msg.get("ty", state["ty"])
        v = msg.get("v", state["v"])
        soc = msg.get("soc", state["soc"])
        simt = msg.get("sim_time", state["sim_time"])
        agv_id = msg.get("agv_id", state["agv_id"])
        reached = bool(msg.get("reached", False))

        state.update(dict(x=x, y=y, theta=theta, tx=tx, ty=ty,
                          v=v, soc=soc, sim_time=simt, agv_id=agv_id, reached=reached))
        state["trail"].append((x, y))
        if len(state["trail"]) > 2000:
            state["trail"] = state["trail"][-2000:]

        # Auto-scale with margins if agent exits current view
        xmins, xmaxs = ax.get_xlim()
        ymins, ymaxs = ax.get_ylim()
        margin = 0.5
        need_rescale = (
            x < xmins + margin or x > xmaxs - margin or
            y < ymins + margin or y > ymaxs - margin
        )
        if need_rescale:
            xs = [p[0] for p in state["trail"]]
            ys = [p[1] for p in state["trail"]]
            xs += [tx] if tx is not None else []
            ys += [ty] if ty is not None else []
            if xs and ys:
                ax.set_xlim(min(xs) - 1.0, max(xs) + 1.0)
                ax.set_ylim(min(ys) - 1.0, max(ys) + 1.0)

        # Update artists
        xs, ys = triangle_at(x, y, theta)
        agv_body.set_data(xs, ys)

        trail_x = [p[0] for p in state["trail"]]
        trail_y = [p[1] for p in state["trail"]]
        trail.set_data(trail_x, trail_y)

        if tx is not None and ty is not None:
            tgt_scatter.set_offsets([[tx, ty]])
        else:
            tgt_scatter.set_offsets([])

        hud_text.set_text(
            f"{state['agv_id']} | t={simt:.1f}s | v={v:.2f} m/s | SoC={soc:.2f} | "
            f"target=({'' if tx is None else f'{tx:.1f}'}, {'' if ty is None else f'{ty:.1f}'})"
            f"{' | reached' if reached else ''}"
        )

        return agv_body, trail, tgt_scatter, hud_text

    anim = FuncAnimation(fig, on_update, interval=100)  # 10 Hz UI update
    try:
        plt.show()
    except Exception:
        # Ensure figure closes cleanly in headless environments
        pass


# ---------------------- Public API for the client ---------------------

def start_visualizer(window_title: str = "AGV Live") -> Tuple[Process, Queue]:
    """
    Start the visualizer process and return (process, queue).
    """
    q: Queue = Queue(maxsize=1000)
    p = Process(target=_run_visualizer, args=(q, window_title), daemon=True)
    p.start()
    return p, q


def send_to_visualizer(queue: Queue, payload: Dict[str, Any]) -> None:
    """Non-blocking enqueue of a telemetry payload."""
    try:
        queue.put_nowait(payload)
    except Exception:
        # Drop on full queue
        pass


def stop_visualizer(queue: Queue) -> None:
    """Signal the visualizer to stop."""
    try:
        queue.put_nowait({"_cmd": "stop"})
    except Exception:
        pass
