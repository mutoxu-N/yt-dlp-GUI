import datetime
import os
import sys
import tkinter as tk
import tkinter.filedialog as tkFDialog
import tkinter.font as tkFont
from tkinter import ttk

import ffmpeg
import re
import threading
from PIL import Image
from mutagen.id3 import ID3, APIC
from yt_dlp import YoutubeDL, DownloadError
from typing import Optional

# constants
APP_NAME = 'yt-dlp GUI'
CURRENT_DIRECTORY = os.getcwd()
MAX_LOG_COUNT = 10
WIN_WIDTH = 800
WIN_HEIGHT = 360
COLOR_BG = '#f2f6fc'

# variables
root: Optional[tk.Tk] = None
processingFlag = False
consoleLogText = ''
urlEntry: Optional[tk.Entry] = None
outputEntry: Optional[tk.Entry] = None
outputFormat: Optional[tk.StringVar] = None
rButton1: Optional[tk.Radiobutton] = None
rButton2: Optional[tk.Radiobutton] = None
confirmButton: Optional[tk.Button] = None


# prohibit running on main thread
def subprocess():
    thread = threading.Thread(target=start)
    thread.start()


# prepare download
def start():
    # 二重処理を防ぐ
    global processingFlag
    if processingFlag:
        return
    else:
        processingFlag = True

    # disable buttons
    global confirmButton, rButton1, rButton2, urlEntry, outputEntry
    urlEntry["state"] = "disable"
    outputEntry["state"] = "disable"
    rButton1["state"] = "disable"
    rButton2["state"] = "disable"
    confirmButton["state"] = "disable"

    # load download URLs
    global outputFormat
    download_list = []  # list of [url, format(mp3/mp4), start, end]
    if urlEntry.get() == "":
        # load download_list.txt
        if os.path.isfile(f"{outputEntry.get()}\\download_list.txt"):
            with open(f"{outputEntry.get()}\\download_list.txt", encoding="UTF-8", mode="r") as f:
                download_list = list(map(lambda a: a.split(','), f.readlines()))

    else:
        download_list = [[urlEntry.get(), outputFormat.get()]]

    for i in range(len(download_list)):
        if "mp3" in download_list[i][1]: download_list[i][1] = "mp3"
        else: download_list[i][1] = "mp4"
        outputFormat.set(download_list[i][1])
        download(download_list[i][0], download_list[i][1], cnt=i + 1)

    # enable buttons
    urlEntry["state"] = "active"
    outputEntry["state"] = "active"
    rButton1["state"] = "active"
    rButton2["state"] = "active"
    confirmButton["state"] = "active"

    processingFlag = False


def download(url, f, s=0, t=-1, cnt=-1):
    global CURRENT_DIRECTORY
    # get metadata
    with YoutubeDL() as ydl:
        data = ydl.extract_info(url, download=False)
        title = data['title']
        thumb_url = data['thumbnail']
        webpage_url = data['webpage_url']
        duration = data['duration']  # sec

        if cnt < 0:
            print(">> META DATA <<")
        else:
            print(f">> META DATA ({cnt}本目) <<")
        print(f"URL: {webpage_url}\ntitle: {title}\nduration: {duration} sec\nthumbnail: {thumb_url}")

    # download mp3
    if f == "mp3":
        opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': f"{CURRENT_DIRECTORY}\\a.m4a",
            'writethumbnail': "true",
        }
        with YoutubeDL(opts) as ydl:
            try: ydl.download(url)
            except DownloadError:
                if not (os.path.exists(f"{CURRENT_DIRECTORY}\\a.m4a") and
                        os.path.exists(f"{CURRENT_DIRECTORY}\\a.webp")):
                    return False

        # convert to jpg from webp
        Image.open(f"{CURRENT_DIRECTORY}\\a.webp").convert('RGB').save(f"{CURRENT_DIRECTORY}\\t.jpg", 'jpeg')

        # convert to mp3 from m4a
        stream = ffmpeg.input(f"{CURRENT_DIRECTORY}\\a.m4a")
        ffmpeg.run(ffmpeg.output(stream, f"{CURRENT_DIRECTORY}\\a.mp3"), overwrite_output=True)

        # set thumbnail to mp3
        tags = ID3(f"{CURRENT_DIRECTORY}\\a.mp3")
        with open(f"{CURRENT_DIRECTORY}\\t.jpg", 'rb') as album_art:
            tags.add(
                APIC(
                    mime="image/jpg",
                    type=3,
                    data=album_art.read()
                )
            )
        tags.save(v2_version=3)

        # file rename
        output_file_name = re.sub(r"[\\/:*?'<>|]+\n", '', title) + ".mp3"
        if os.path.exists(f"{CURRENT_DIRECTORY}\\{output_file_name}") and output_file_name != "a.mp3":
            # remove old file
            os.remove(f"{CURRENT_DIRECTORY}\\{output_file_name}")

        if output_file_name != "a.mp3":
            # rename if needed
            os.rename(f"{CURRENT_DIRECTORY}\\a.mp3",
                      f"{CURRENT_DIRECTORY}\\{output_file_name}")

        # delete tmp files
        if os.path.exists(f"{CURRENT_DIRECTORY}\\a.m4a"): os.remove(f"{CURRENT_DIRECTORY}\\a.m4a")
        if os.path.exists(f"{CURRENT_DIRECTORY}\\a.webp"): os.remove(f"{CURRENT_DIRECTORY}\\a.webp")
        if os.path.exists(f"{CURRENT_DIRECTORY}\\t.jpg"): os.remove(f"{CURRENT_DIRECTORY}\\t.jpg")

    # download mp4
    else:
        opts = {
            'format': 'mp4/bestvideo/best',
            'outtmpl': f"{CURRENT_DIRECTORY}\\v.mp4",
        }
        with YoutubeDL(opts) as ydl:
            try:
                ydl.download(url)
            except DownloadError:
                if not os.path.exists(f"{CURRENT_DIRECTORY}\\v.mp4"):
                    return False

            # file rename
            output_file_name = re.sub(r"[\\/:*?'<>|]+\n", '', title) + ".mp4"
            if os.path.exists(f"{CURRENT_DIRECTORY}\\{output_file_name}") and output_file_name != "v.mp4":
                # remove old file
                os.remove(f"{CURRENT_DIRECTORY}\\{output_file_name}")

            if output_file_name != "v.mp4":
                # rename if needed
                os.rename(f"{CURRENT_DIRECTORY}\\v.mp4",
                          f"{CURRENT_DIRECTORY}\\{output_file_name}")

    return True


def select():
    global outputEntry
    output_file_path = tkFDialog.askdirectory()
    outputEntry.delete(0, tk.END)
    outputEntry.insert(0, output_file_path)


def close():
    for _, _, files in os.walk(CURRENT_DIRECTORY + '/log'):
        if len(files) >= MAX_LOG_COUNT - 1:
            files.sort()
            files = files[MAX_LOG_COUNT - 2:-1]
            for f in files:
                os.remove(CURRENT_DIRECTORY + '/log/' + f)

    now = datetime.datetime.now()
    # config
    with open(CURRENT_DIRECTORY + '/config.cfg', encoding='UTF-8', mode='w') as f:
        global outputEntry
        if isinstance(outputEntry, tk.Entry):
            f.write(outputEntry.get())
            f.close()

    # log
    if not os.path.isdir(CURRENT_DIRECTORY + '/log'):
        os.mkdir(CURRENT_DIRECTORY + '/log')
    with open(CURRENT_DIRECTORY + '/log/' + str(now.year).zfill(4) + str(now.month).zfill(2) + str(now.day).zfill(
            2) + str(now.hour).zfill(2) + str(now.minute).zfill(2) + str(now.second).zfill(2) + '.txt',
              encoding='UTF-8', mode='w') as f:
        global consoleLogText
        f.write(consoleLogText)
        f.close()
    sys.exit(0)


# Pyinstaller 用 埋め込みファイル参照
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS + '\\' + relative_path
    return os.path.join(os.path.abspath('.'), relative_path)


def main():
    # get config
    config_txt = CURRENT_DIRECTORY
    if os.path.isfile(CURRENT_DIRECTORY + '/config.cfg'):
        with open(CURRENT_DIRECTORY + '/config.cfg', encoding='UTF-8', mode='r') as f:
            tmp = f.readline()
            if tmp != "": config_txt = tmp
            f.close()

    # create window
    global root, outputFormat
    root = tk.Tk()
    outputFormat = tk.StringVar(value="mp3")

    # window settings
    root.resizable(width=False, height=False)
    root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
    root.config(bg=COLOR_BG)
    root.title(APP_NAME)

    # style
    normal_text_font = tkFont.Font(family='Rounded-L M+ 1c heavy', size=15)
    s = ttk.Style()
    s.configure('YTDL.TFrame', background=COLOR_BG)
    s.configure('YTDL.TLabel', background=COLOR_BG)

    # url
    url_frame = ttk.Frame(root, padding=0, style='YTDL.TFrame')
    url_frame.pack(pady=15)
    ttk.Label(url_frame, text='URL: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global urlEntry
    urlEntry = ttk.Entry(url_frame, width=70)
    urlEntry.pack(side=tk.LEFT)

    # output config
    output_frame = ttk.Frame(root, padding=3, style='YTDL.TFrame')
    output_frame.pack()
    ttk.Label(output_frame, text='Output Folder: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global outputEntry
    outputEntry = ttk.Entry(output_frame, width=70)
    outputEntry.insert(0, config_txt)
    outputEntry.pack(side=tk.LEFT)
    ttk.Button(output_frame, text='Browse', command=select).pack(side=tk.LEFT)

    # radio button
    radio_frame = ttk.Frame(root, padding=5, style="YTDL.TFrame")
    radio_frame.pack()
    global rButton1, rButton2
    rButton1 = tk.Radiobutton(radio_frame, text="mp3", variable=outputFormat, value="mp3")
    rButton1.pack(side=tk.LEFT)
    rButton2 = tk.Radiobutton(radio_frame, text="mp4", variable=outputFormat, value="mp4")
    rButton2.pack(side=tk.LEFT)

    # confirm button
    confirm_frame = ttk.Frame(root, padding=5, style='YTDL.TFrame')
    confirm_frame.pack()
    global confirmButton
    confirmButton = ttk.Button(confirm_frame, text='Download', command=subprocess)
    confirmButton.pack(side=tk.RIGHT)

    # progress bar

    # icon
    root.wm_iconbitmap(resource_path('image\\icon.ico'))

    # Start
    root.protocol('WM_DELETE_WINDOW', close)
    root.mainloop()


main()
