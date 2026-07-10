import threading
import time
import tkinter as tk

import pyautogui
from pynput import keyboard, mouse

running = False
recording = False
stop_now = False
last_event_time = None
recorded_actions = []
listener_status = {
    "keyboard": False,
    "mouse": False,
}

hotkey = None
KEYBOARD_MODIFIERS = {
    keyboard.Key.cmd,
    keyboard.Key.cmd_l,
    keyboard.Key.cmd_r,
    keyboard.Key.ctrl,
    keyboard.Key.ctrl_l,
    keyboard.Key.ctrl_r,
}


def set_status(text):
    root.after(0, lambda: status.config(text=text))


def start_macro():
    global running, stop_now

    if running:
        set_status("Already running")
        return

    running = True
    stop_now = False
    set_status("Running built-in macro...")

    thread = threading.Thread(target=run_macro, daemon=True)
    thread.start()


def run_macro():
    global running

    try:
        root.after(0, root.withdraw)
        time.sleep(2)

        for _ in range(15):
            if stop_now:
                break

            pyautogui.write("testing :D", interval=0.005)
            pyautogui.press("enter")
            time.sleep(0.1)

        if stop_now:
            set_status("Built-in macro stopped")
        else:
            set_status("Built-in macro finished")
    finally:
        root.after(0, root.deiconify)
        running = False


def start_recording():
    global recording, recorded_actions, last_event_time

    if running:
        set_status("Stop playback first")
        return

    recording = True
    recorded_actions = []
    last_event_time = time.time()
    set_status("Recording input... Press Stop when done")


def stop_recording():
    global recording

    if not recording:
        return

    recording = False
    if recorded_actions:
        set_status(f"Recorded {len(recorded_actions)} events")
    else:
        status_text = "Recording stopped: no events captured"
        if not listener_status["keyboard"] or not listener_status["mouse"]:
            issue = []
            if not listener_status["keyboard"]:
                issue.append("keyboard")
            if not listener_status["mouse"]:
                issue.append("mouse")
            status_text += f" (listeners inactive: {', '.join(issue)})"
        set_status(status_text)


def play_recording():
    global running, stop_now

    if recording:
        set_status("Stop recording before playback")
        return

    if running:
        set_status("Already running")
        return

    if not recorded_actions:
        set_status("No recorded input yet")
        return

    running = True
    stop_now = False
    set_status("Replaying recorded input until stopped...")

    thread = threading.Thread(target=run_recording, daemon=True)
    thread.start()


def run_recording():
    global running

    try:
        root.after(0, root.withdraw)
        time.sleep(1)

        while not stop_now:
            for action in recorded_actions:
                if stop_now:
                    break

                if action[0] == "wait":
                    time.sleep(action[1])
                elif action[0] == "key":
                    pyautogui.press(action[1])
                elif action[0] == "click":
                    x, y, button = action[1], action[2], action[3]
                    pyautogui.click(x=x, y=y, button=button)

        set_status("Playback stopped")
    finally:
        root.after(0, root.deiconify)
        running = False


def stop_macro():
    global stop_now
    stop_now = True
    set_status("Stopping...")


def toggle_macro():
    if recording:
        stop_recording()
    elif running:
        stop_macro()
    else:
        start_macro()


def record_event(event_type, *data):
    global last_event_time

    if not recording:
        return

    now = time.time()
    delay = now - last_event_time
    if delay > 0:
        recorded_actions.append(("wait", delay))

    if event_type == "key":
        key = data[0]
        if isinstance(key, keyboard.KeyCode):
            if key.char is not None:
                recorded_actions.append(("key", key.char))
            else:
                recorded_actions.append(("key", str(key)))
        else:
            name = str(key).split(".")[-1]
            recorded_actions.append(("key", name))
    elif event_type == "click":
        x, y, button = data
        recorded_actions.append(("click", x, y, button))

    last_event_time = now


def on_press(key):
    if hotkey is not None:
        hotkey.press(key)

    if recording:
        if key not in KEYBOARD_MODIFIERS:
            record_event("key", key)


def on_release(key):
    if hotkey is not None:
        hotkey.release(key)


def on_click(x, y, button, pressed):
    if recording and pressed:
        record_event("click", x, y, button.name)


root = tk.Tk()
root.title("Simple Macro Recorder")
root.geometry("320x200")
root.attributes("-topmost", True)

tk.Label(root, text="Start/Stop key: Command+Control+K").pack(pady=8)

button_frame = tk.Frame(root)
button_frame.pack(pady=6)

record_button = tk.Button(button_frame, text="Record", command=start_recording)
record_button.grid(row=0, column=0, padx=4)

stop_button = tk.Button(button_frame, text="Stop", command=stop_recording)
stop_button.grid(row=0, column=1, padx=4)

play_button = tk.Button(button_frame, text="Play", command=play_recording)
play_button.grid(row=0, column=2, padx=4)

macro_button_frame = tk.Frame(root)
macro_button_frame.pack(pady=4)

tk.Button(macro_button_frame, text="Start Macro", command=start_macro).grid(row=0, column=0, padx=4)

tk.Button(macro_button_frame, text="Stop Macro", command=stop_macro).grid(row=0, column=1, padx=4)

status = tk.Label(root, text="Ready")
status.pack(pady=10)

try:
    global hotkey
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse("<cmd>+<ctrl>+k"),
        toggle_macro,
    )
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener_status["keyboard"] = True
except Exception:
    set_status("Keyboard listener failed: allow Accessibility in System Settings")

try:
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    listener_status["mouse"] = True
except Exception:
    set_status("Mouse listener failed: allow Accessibility in System Settings")

if not listener_status["keyboard"] or not listener_status["mouse"]:
    issue = []
    if not listener_status["keyboard"]:
        issue.append("keyboard")
    if not listener_status["mouse"]:
        issue.append("mouse")
    set_status(f"Listeners inactive: {', '.join(issue)}. Enable Accessibility.")

root.mainloop()


