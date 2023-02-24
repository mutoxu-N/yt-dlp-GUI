import datetime
import math
import os
import sys
import tkinter
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
WIN_WIDTH = 1280
WIN_HEIGHT = 720
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
consoleText: Optional[tk.Text] = None
confirmButton: Optional[tk.Button] = None


# prohibit running download on UI thread
def subprocess():
    thread = threading.Thread(target=start)
    thread.start()


# prepare download
def start():
    # exclusive processing
    global processingFlag
    if processingFlag:
        return
    else:
        processingFlag = True

    # disable buttons
    global confirmButton, rButton1, rButton2, urlEntry, outputEntry
    urlEntry["state"], outputEntry["state"], rButton1["state"], rButton2["state"], confirmButton["state"] = ["disable"] * 5

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
        print("aaa", i)
        # text format
        if "mp3" in download_list[i][1]: download_list[i][1] = "mp3"
        else: download_list[i][1] = "mp4"
        outputFormat.set(download_list[i][1])

        success_flag = False
        error_msgs = None
        for j in range(5):
            result, msgs = download(download_list[i][0], download_list[i][1], cnt=i+1)
            if result:
                # success
                create_log(f"O {download_list[i][0]} / {msgs[0]} >> DOWNLOAD SUCCESS")
                success_flag = True
                break
            else:
                # failed
                error_msgs = msgs
                create_log(f"X {download_list[i][0]} / {msgs[0]} >> DOWNLOAD FAILED (attempt: {j+1})")

    # enable buttons
    urlEntry["state"], outputEntry["state"], rButton1["state"], rButton2["state"], confirmButton["state"] = [
                                                                                                                "active"] * 5
    processingFlag = False


def download(url, f, st=0, ed=-1, cnt=-1):
    global CURRENT_DIRECTORY
    # get metadata
    with YoutubeDL() as ydl:
        data = ydl.extract_info(url, download=False)
        title = data['title']
        thumb_url = data['thumbnail']
        webpage_url = data['webpage_url']
        duration = data['duration']  # sec

        text = ""
        if cnt < 0:
            text = ">>  META DATA  <<"
        else:
            text = f">>  META DATA ({cnt}本目)  <<"
        create_log(f"{text}\nURL: {webpage_url}\ntitle: {title}\nduration: {duration} sec\nthumbnail: {thumb_url}\n" + \
                   "-"*100)

    # download mp3
    if f == "mp3":
        opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': f"{CURRENT_DIRECTORY}\\a.m4a",
            'writethumbnail': "true",
        }
        with YoutubeDL(opts) as ydl:
            try:
                ydl.download(url)
            except DownloadError:
                if not (os.path.exists(f"{CURRENT_DIRECTORY}\\a.m4a") and
                        os.path.exists(f"{CURRENT_DIRECTORY}\\a.webp")):
                    return False, ["Download failed!"]

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
                    return False, ["Download failed!"]

            # file rename
            output_file_name = re.sub(r"[\\/:*?'<>|]+\n", '', title) + ".mp4"
            if os.path.exists(f"{CURRENT_DIRECTORY}\\{output_file_name}") and output_file_name != "v.mp4":
                # remove old file
                os.remove(f"{CURRENT_DIRECTORY}\\{output_file_name}")

            if output_file_name != "v.mp4":
                # rename if needed
                os.rename(f"{CURRENT_DIRECTORY}\\v.mp4",
                          f"{CURRENT_DIRECTORY}\\{output_file_name}")

    return True, [title]


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


def create_log(msgs, is_display=True):
    # make timestamp
    timestamp = f"[{datetime.datetime.now().strftime('%H:%M:%S.')}" \
                f"{str(math.floor(datetime.datetime.now().microsecond/10000)).zfill(2)}]"

    # disassemble text
    msgs = msgs.split('\n') + ['']*2

    global consoleText, consoleLogText
    # for log file
    for msg in msgs:
        consoleLogText += f"{timestamp} {msg}\n"

    if is_display:
        for msg in reversed(msgs):
            consoleText['state'] = 'normal'
            consoleText.insert('0.0', f"{timestamp} {msg}\n")
            consoleText['state'] = 'disable'


# get resource for Pyinstaller
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
    urlEntry = ttk.Entry(url_frame, width=150)
    urlEntry.pack(side=tk.LEFT)

    # output config
    output_frame = ttk.Frame(root, padding=3, style='YTDL.TFrame')
    output_frame.pack()
    ttk.Label(output_frame, text='Output Folder: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global outputEntry
    outputEntry = ttk.Entry(output_frame, width=150)
    outputEntry.insert(0, config_txt)
    outputEntry.pack(side=tk.LEFT)
    ttk.Button(output_frame, text='Browse', command=select).pack(side=tk.LEFT)

    # radio button
    bottom_frame = ttk.Frame(root, padding=5, style="YTDL.TFrame")
    bottom_frame.pack()
    ttk.Label(bottom_frame, text='Format: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global rButton1, rButton2
    rButton1 = tk.Radiobutton(bottom_frame, text="mp3", variable=outputFormat, value="mp3")
    rButton1.pack(side=tk.LEFT)
    rButton2 = tk.Radiobutton(bottom_frame, text="mp4", variable=outputFormat, value="mp4")
    rButton2.pack(side=tk.LEFT)

    # confirm button
    confirm_frame = ttk.Frame(root, padding=5, style='YTDL.TFrame')
    confirm_frame.pack()
    global confirmButton
    confirmButton = ttk.Button(confirm_frame, text='Download', command=subprocess)
    confirmButton.pack(side=tk.RIGHT, padx=(20, 0))

    # console
    console_frame = ttk.Frame(root, width=1200, height=500, style='YTDL.TFrame')
    console_frame.pack(pady=(10, 20))
    global consoleText
    consoleText = tk.Text(console_frame, width=160, height=50, wrap=tk.NONE, state="disabled")

    v_scroll = tkinter.Scrollbar(console_frame, orient=tkinter.VERTICAL, command=consoleText.yview)
    v_scroll.pack(side=tk.RIGHT, fill="y")
    consoleText['yscrollcommand'] = v_scroll.set
    h_scroll = tkinter.Scrollbar(console_frame, orient=tkinter.HORIZONTAL, command=consoleText.xview)
    h_scroll.pack(side=tk.BOTTOM, fill="x")
    consoleText['xscrollcommand'] = h_scroll.set
    consoleText.pack()

    # icon
    root.wm_iconbitmap(resource_path('image\\icon.ico'))

    # Start
    root.protocol('WM_DELETE_WINDOW', close)
    root.mainloop()


main()
