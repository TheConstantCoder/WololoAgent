from pynput import keyboard

def on_press(key):
    print(f'Pressed: {key}')

def on_release(key):
    print(f'Released: {key}')
    if key == keyboard.Key.esc:
        return False

print("Testing keyboard listener. Press keys (ESC to exit)...")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
