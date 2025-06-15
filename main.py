import multiprocessing
import sys
import os
from pathlib import Path


def run_keyboard_detect():
    from keyboard_detect import start_detect
    start_detect()


def run_keyboard_release():
    from keyboard_release import start_heatmap
    start_heatmap()


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    detect_process = multiprocessing.Process(target=run_keyboard_detect)
    release_process = multiprocessing.Process(target=run_keyboard_release)

    detect_process.start()
    release_process.start()

    detect_process.join()
    release_process.join()