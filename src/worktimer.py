#!/usr/bin/env python3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


class State(Enum):
    BIG_REST, SMALL_REST, WORK, NOTHING = range(4)


class Action(Enum):
    WRITE_DONE, WRITE_SKIPPED, DISMISS, DISABLE = range(4)


MSG_FILE = Path.home() / "msg"
SOUNDS = Path("/usr/share/worktimer/sounds")
STATES = ["Big rest", "Small rest", "Work", "Nothing yet"]
ACTIONS = ["Done", "Skipped", "Okay", "Disable"]
RUNNING = True


def exec_cmd(cmd):
    """Run a command and return its output if successful."""
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip() if result.returncode == 0 else None


def take_photo(name):
    """Capture a photo with ffmpeg."""
    output_path = Path.home() / "Pictures/worktimer" / f"{name}.jpg"
    try:
        subprocess.run(f"ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 {output_path} -y", shell=True, timeout=1.5)
    except subprocess.TimeoutExpired as e:
        print("No camera found or too long to take_photo", e)


def predict_place():
    """Predict location based on worklog."""
    try:
        return "HM" if "HM" in (Path.home() / ".worklog").read_text().splitlines()[-1] else "CW"
    except Exception as e:
        return "CW"


def store_workunit(success, event_time, duration=timedelta(minutes=25)):
    """Log a work unit to .worklog."""
    start = event_time - duration
    with (Path.home() / ".worklog").open("a") as f:
        f.write(f"{start:%Y-%m-%d %H:%M}-{event_time:%H:%M} [{'x' if success else ' '}] {predict_place()}\n")


def store_score():
    """Append a score entry to .worklog."""
    with (Path.home() / ".worklog").open("a") as f:
        f.write("depth: 0/9\n")


def read_msg():
    """Read and remove message file if it exists."""
    if MSG_FILE.exists():
        msg = MSG_FILE.read_text().strip()
        MSG_FILE.unlink()
        return f"Msg: {msg}"
    return ""


def get_actions(state):
    """Generate action parameters for notify-send."""
    return "--action=" + "=Done --action=".join(ACTIONS[:2]) if state in {State.BIG_REST, State.SMALL_REST} else ""


def handle_transition(old, new):
    """Handle state transitions."""
    global RUNNING
    h, m, _ = datetime.now().timetuple()[3:6]
    event_time = datetime.now()
    msg = f"{h:02}:{m:02} {STATES[old.value]} finished. {STATES[new.value]}. {read_msg()}"
    sound = SOUNDS / ["click.ogg", "click.ogg", "string.ogg"][new.value]

    take_photo(event_time.strftime("%Y-%m-%d_%H:%M"))
    subprocess.run(f"paplay {sound}", shell=True)
    res = exec_cmd(
        f'notify-send {get_actions(new)} --action={ACTIONS[Action.DISABLE.value]}={ACTIONS[Action.DISABLE.value]} -a worktimer -u critical -e -t 10000 "{msg}"'
    )

    if res and old == State.WORK:
        if res == ACTIONS[Action.DISABLE.value]:
            RUNNING = False
        else:
            store_workunit(res == ACTIONS[Action.WRITE_DONE.value], event_time)
            if new == State.BIG_REST:
                store_score()
            subprocess.run("alacritty -e nvim -c 'normal! GA' ~/.worklog", shell=True)


def main():
    """Run the work timer."""
    state = State.NOTHING
    while RUNNING:
        h, m, _ = datetime.now().timetuple()[3:6]
        new = State.BIG_REST if h % 3 == 0 and m < 35 else State.SMALL_REST if m % 30 < 5 else State.WORK

        if state != new:
            threading.Thread(target=handle_transition, args=(state, new)).start()
            state = new
        time.sleep(1)


if __name__ == "__main__":
    main()
