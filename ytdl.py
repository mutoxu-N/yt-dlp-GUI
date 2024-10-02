import datetime
import math
import os
import sys
import tkinter
import tkinter as tk
import tkinter.filedialog as tkFDialog
import tkinter.font as tkFont
from tkinter import ttk, messagebox

import ffmpeg
import re
import threading
from PIL import Image
from mutagen.id3 import ID3, APIC, TIT2
from yt_dlp import YoutubeDL, DownloadError
from typing import Optional

# constants
APP_NAME = 'yt-dlp GUI'
CURRENT_DIRECTORY = os.getcwd()
MAX_LOG_COUNT = 10
WIN_WIDTH = 1280
WIN_HEIGHT = 720
COLOR_BG = '#f2f6fc'
DURATION_FLAG = False

# variables
root: Optional[tk.Tk] = None
processingFlag = False
consoleLogText = ''
urlEntry: Optional[tk.Entry] = None
outputEntry: Optional[tk.Entry] = None
browseOutDirButton: Optional[tk.Button] = None
outputFormat: Optional[tk.StringVar] = None
rButtonMP3: Optional[tk.Radiobutton] = None
rButtonMP4: Optional[tk.Radiobutton] = None
rButtonSplit: Optional[tk.Radiobutton] = None
cookieCheckBoxValue: Optional[tk.BooleanVar] = None
cookieCheckBox: Optional[tk.Checkbutton] = None
cookieEntry: Optional[tk.Entry] = None
browseCookieButton: Optional[tk.Button] = None
stEntry: Optional[tk.Entry] = None
edEntry: Optional[tk.Entry] = None
consoleText: Optional[tk.Text] = None
confirmButton: Optional[tk.Button] = None


# prohibit running download on UI thread
def subprocess():
    thread = threading.Thread(target=start)
    thread.start()


# calc seconds from 000:00:00
def convert_to_seconds(string):
    nums = list(map(lambda a: int(a or 0), string.split(':')))[::-1]
    t, i = 0, 0
    for num in nums:
        t += num * (60 ** i)
        i += 1
    return t


# calc seconds from 000:00:00
def convert_to_timestamp(sec, sp=':'):
    return f"{sec // 3600}{sp}{sec % 3600 // 60}{sp}{sec % 60}"


# prepare download
def start():
    # exclusive processing
    global processingFlag
    if processingFlag:
        create_log('Another process is running.')
        return
    else:
        processingFlag = True

    # disable buttons
    global confirmButton, rButtonMP3, rButtonMP4, rButtonSplit, urlEntry, outputEntry, stEntry, edEntry, cookieCheckBox, cookieEntry, browseCookieButton
    urlEntry["state"], outputEntry["state"], rButtonMP3["state"], rButtonMP4["state"], rButtonSplit["state"], \
        confirmButton["state"], stEntry["state"], edEntry["state"], browseOutDirButton["state"], \
        cookieCheckBox["state"], cookieEntry["state"], browseCookieButton["state"],  = ["disable"] * 12

    # load download URLs
    global outputFormat, DURATION_FLAG
    download_list = []  # list of [url, format(mp3/mp4), start, end] or [url, format]
    if urlEntry.get() == "":
        # load download_list.txt
        if os.path.isfile(f"{outputEntry.get()}\\download_list.txt"):
            with open(f"{outputEntry.get()}\\download_list.txt", encoding="UTF-8", mode="r") as f:
                lines = list(map(lambda a: a.split(','), f.readlines()))
                for l in lines:
                    if len(l) == 1:
                        download_list.append([l[0], "mp3"])
                    elif len(l) == 2:
                        download_list.append(l)
                    # TODO it doesn't work correctly, so disabled.
                    elif len(l) == 4 and DURATION_FLAG:
                        download_list.append([l[0], l[1], convert_to_seconds(l[2]), convert_to_seconds(l[3])])
                    else:
                        download_list.append([None, ','.join(l)])

    else:
        # clac seconds
        st, ed = convert_to_seconds(stEntry.get()), convert_to_seconds(edEntry.get())
        if st == 0 and ed == 0:
            download_list.append([urlEntry.get(), outputFormat.get()])
        else:
            download_list.append([urlEntry.get(), outputFormat.get(), st, ed])

    # run download 1 by 1.
    process_history = ""
    for i in range(len(download_list)):
        if not download_list[i][0]:
            create_log(f"setting({download_list[i][1]}) is invalid.")
            process_history += f"X setting({download_list[i][1]}) is invalid."
            continue

        # 5 attempts
        success_flag = False
        error_msgs = None
        for j in range(5):
            # check format
            if "mp4" in download_list[i][1]:
                download_list[i][1] = "mp4"
            elif "webm" in download_list[i][1]:
                download_list[i][1] = "webm"
            else:
                download_list[i][1] = "mp3"

            # run download()
            try:
                if len(download_list[i]) == 4:
                    result, msgs = download(download_list[i][0], download_list[i][1], cnt=i + 1,
                                            st=download_list[i][2], ed=download_list[i][3])
                else:
                    result, msgs = download(download_list[i][0], download_list[i][1], cnt=i + 1)
            except Exception as e:
                result, msgs = False, [str(e)]

            # write logs
            if result:
                # success
                create_log(f"O {download_list[i][0]} / {msgs[0]} >> DOWNLOAD SUCCESS")
                process_history += f"O {download_list[i][0]} / {msgs[0]} >> DOWNLOAD SUCCESS ({i + 1}/{len(download_list)})\n"
                success_flag = True
                break
            else:
                # failed
                error_msgs = msgs
                print(msgs[0].find("This video is only available to Music Premium members"))
                if msgs[0].find("This video is only available to Music Premium members"):
                    create_log(f"X {download_list[i][0]} / {msgs[0]} >> DOWNLOAD FAILED")
                    break
                create_log(f"X {download_list[i][0]} / {msgs[0]} >> DOWNLOAD FAILED (attempt: {j + 1})")

        if not success_flag:
            process_history += f"X {download_list[i][0]} / {error_msgs[0]} >> DOWNLOAD FAILED ({i + 1}/{len(download_list)})\n"

    create_log(process_history)

    # enable buttons
    urlEntry["state"], outputEntry["state"], rButtonMP3["state"], rButtonMP4["state"], rButtonSplit["state"], \
        confirmButton["state"], stEntry["state"], edEntry["state"], browseOutDirButton["state"], cookieCheckBox["state"] = ["normal"] * 10
    global cookieCheckBoxValue
    if cookieCheckBoxValue.get():
        cookieEntry["state"], browseCookieButton["state"] = ["normal"]*2
    stEntry.delete(0, tk.END)
    edEntry.delete(0, tk.END)
    processingFlag = False

    # dialog
    messagebox.showinfo(APP_NAME, "Downloads finished!!")


def download(url, f, st=0, ed=-1, cnt=-1):
    global CURRENT_DIRECTORY
    # download options
    is_full = True
    opts = {}
    global cookieCheckBoxValue, cookieEntry
    if cookieCheckBoxValue.get():
        opts["cookiefile"] = cookieEntry.get().replace("\n", "")


    # get metadata
    with YoutubeDL(opts) as ydl:
        data = ydl.extract_info(url, download=False)
        title = data['title']
        thumb_url = data['thumbnail']
        webpage_url = data['webpage_url']
        duration = data['duration']  # sec

        if cnt < 0:
            text = ">>  META DATA  <<"
        else:
            text = f">>  META DATA (No.{cnt})  <<"

        # calc clip duration
        if st < ed:
            if duration < ed: ed = duration
            # TODO this may not be correct.
            # `download_ranges` does not work correctly.
            # downloaded audio and video are different range.
            # This makes gap between audio and video.
            opts['download_ranges'] = lambda _, __: [{'start_time': st, 'end_time': ed}]
            is_full = False

            text = f"{text}\nURL: {webpage_url}\ntitle: {title}\nlength: {duration} sec\n" \
                   f"clip: {convert_to_timestamp(st)} - {convert_to_timestamp(ed)}\nformat: {f}\nthumbnail: {thumb_url}\n"
        else:
            text = f"{text}\nURL: {webpage_url}\ntitle: {title}\nlength: {duration} sec\n" \
                   f"clip: ALL\nformat: {f}\nthumbnail: {thumb_url}\n"
        create_log(text)

    # display sync
    outputFormat.set(f)
    global stEntry, edEntry
    stEntry["state"], edEntry["state"] = ["normal"] * 2
    stEntry.delete(0, tk.END)
    stEntry.insert(0, convert_to_timestamp(st))
    edEntry.delete(0, tk.END)
    if ed < 0:
        edEntry.insert(0, convert_to_timestamp(duration))
    else:
        edEntry.insert(0, convert_to_timestamp(ed))
    stEntry["state"], edEntry["state"] = ["disable"] * 2

    # download audio
    opts['format'] = 'm4a/bestaudio/best'
    opts['outtmpl'] = f"{outputEntry.get()}\\a.m4a"
    opts['overwrite'] = "true"
    if f == "mp3":
        opts['writethumbnail'] = "true"

    with YoutubeDL(opts) as ydl:
        try:
            ydl.download(url)
        except DownloadError:
            if not os.path.exists(f"{outputEntry.get()}\\a.m4a"):
                return False, ["Download failed!"]

            elif f == "mp3" and not os.path.exists(f"{outputEntry.get()}\\a.webp"):
                return False, ["Download failed!"]

    # convert to jpg from webp
    if f == "mp3":
        Image.open(f"{outputEntry.get()}\\a.webp").convert('RGB').save(f"{outputEntry.get()}\\t.jpg", 'jpeg')

        # convert to mp3 from m4a
        stream = ffmpeg.input(f"{outputEntry.get()}\\a.m4a")
        ffmpeg.run(ffmpeg.output(stream, f"{outputEntry.get()}\\a.mp3"), overwrite_output=True)

        # set thumbnail to mp3
        tags = ID3(f"{outputEntry.get()}\\a.mp3")
        with open(f"{outputEntry.get()}\\t.jpg", 'rb') as album_art:
            tags.add(
                APIC(
                    mime="image/jpg",
                    type=3,
                    data=album_art.read()
                )
            )
        tags.add(TIT2(encoding=3, text=title))
        tags.save(v2_version=3)

        # file rename
        if is_full:
            output_file_name = re.sub(r'[\\/:*?"<>|]+', ' ', title) + ".mp3"
        else:
            output_file_name = re.sub(r'[\\/:*?"<>|]+', ' ', title) + \
                               f"{convert_to_timestamp(st, sp='.')}-{convert_to_timestamp(ed, sp='.')}" + ".mp3"

        if os.path.exists(f"{outputEntry.get()}\\{output_file_name}") and output_file_name != "a.mp3":
            # remove old file
            os.remove(f"{outputEntry.get()}\\{output_file_name}")

        if output_file_name != "a.mp3":
            # rename if needed
            os.rename(f"{outputEntry.get()}\\a.mp3",
                      f"{outputEntry.get()}\\{output_file_name}")

        # delete tmp files
        if os.path.exists(f"{outputEntry.get()}\\a.m4a"): os.remove(f"{outputEntry.get()}\\a.m4a")
        if os.path.exists(f"{outputEntry.get()}\\a.webp"): os.remove(f"{outputEntry.get()}\\a.webp")
        if os.path.exists(f"{outputEntry.get()}\\t.jpg"): os.remove(f"{outputEntry.get()}\\t.jpg")

    # download mp4 or webm
    if f != "mp3":
        opts['format'] = 'webm/bestvideo/best'
        opts['outtmpl'] = f"{outputEntry.get()}\\v.webm"
        opts['overwrite'] = "true"

        with YoutubeDL(opts) as ydl:
            try:
                ydl.download(url)
            except DownloadError:
                if not os.path.exists(f"{outputEntry.get()}\\v.webm"):
                    return False, ["Download failed!"]

        if f == "mp4":
            # convert to mp4 from webm and combine audio
            ffmpeg.output(ffmpeg.input(f"{outputEntry.get()}\\v.webm"), f"{outputEntry.get()}\\v.mp4") \
                .global_args('-i', f"{outputEntry.get()}\\a.m4a").global_args('-vcodec', 'copy')\
                .global_args('-map', '0:v').global_args('-map', '1:a').run(overwrite_output=True)

        # file rename
        if is_full:
            output_file_name = re.sub(r"[\\/:*?'<>|]+\n", '', title) + f".{f}"
        else:
            output_file_name = re.sub(r"[\\/:*?'<>|]+\n", '', title) + \
                               f"{convert_to_timestamp(st, sp='.')}-{convert_to_timestamp(ed, sp='.')}" + f".{f}"

        # remove old file
        if os.path.exists(f"{outputEntry.get()}\\{output_file_name}") and output_file_name != f"c.{f}":
            os.remove(f"{outputEntry.get()}\\{output_file_name}")

        # rename if needed
        if output_file_name != f"v.{f}":
            os.rename(f"{outputEntry.get()}\\v.{f}",
                      f"{outputEntry.get()}\\{output_file_name}")
        if output_file_name != f"a.m4a" and f == "webm":
            os.rename(f"{outputEntry.get()}\\a.m4a",
                      f"{outputEntry.get()}\\{output_file_name[:-4]}.m4a")

        # delete tmp file
        if os.path.exists(f"{outputEntry.get()}\\a.m4a"): os.remove(f"{outputEntry.get()}\\a.m4a")
        if os.path.exists(f"{outputEntry.get()}\\v.{f}"): os.remove(f"{outputEntry.get()}\\v.{f}")
        if os.path.exists(f"{outputEntry.get()}\\v.webm") and output_file_name != "v.webm":
            os.remove(f"{outputEntry.get()}\\v.webm")

    return True, [title]


def select_output_dir():
    global outputEntry
    output_file_path = tkFDialog.askdirectory().replace("\n", "")
    if output_file_path != "":
        outputEntry.delete(0, tk.END)
        outputEntry.insert(0, output_file_path)

def select_cookie_file():
    global cookieEntry
    cookie_file_path = tkFDialog.askopenfilename().replace("\n", "")
    if cookie_file_path != "":
        cookieEntry.delete(0, tk.END)
        cookieEntry.insert(0, cookie_file_path)


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
        global outputEntry, cookieEntry, cookieCheckBoxValue
        out = ["\n"]*3
        if isinstance(outputEntry, tk.Entry): out[0] = outputEntry.get().replace("\n", "") + "\n"
        if isinstance(cookieEntry, tk.Entry): out[1] = cookieEntry.get().replace("\n", "") + "\n"
        if isinstance(cookieCheckBoxValue, tk.BooleanVar): out[2] = str(cookieCheckBoxValue.get()) + "\n"
        f.writelines(out)

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


# check entry inputs express time
def on_validate(text):
    # 000:00:00 is max length
    if len(text) >= 10: return False

    try:
        # create nums = [sec, min, hour]
        nums = list(map(lambda a: int(a or 0), text.split(':')))[::-1]
    except ValueError:
        return False

    # number of ':' must be less than 3.
    if 3 < len(nums): return False
    return True


def create_log(msgs, is_display=True):
    # make timestamp
    timestamp = f"[{datetime.datetime.now().strftime('%H:%M:%S.')}" \
                f"{str(math.floor(datetime.datetime.now().microsecond / 10000)).zfill(2)}]"

    # disassemble text
    msgs = msgs.split('\n') + ['']

    global consoleText, consoleLogText
    # for log file
    for msg in msgs:
        consoleLogText += f"{timestamp} {msg}\n"

    if is_display:
        for msg in reversed(msgs):
            consoleText['state'] = 'normal'
            consoleText.insert('0.0', f"{timestamp} {msg}\n")
            consoleText['state'] = 'disable'


def main():
    # get config
    output_dir = CURRENT_DIRECTORY
    use_cookie = True
    cookie_filepath = ""
    if os.path.isfile(CURRENT_DIRECTORY + '/config.cfg'):
        with open(CURRENT_DIRECTORY + '/config.cfg', encoding='UTF-8', mode='r') as f:
            lines = f.readlines()
            if len(lines) > 0 and lines[0] not in ["", "\n"]: output_dir = lines[0]
            if len(lines) > 1 and lines[1] not in ["", "\n"]: cookie_filepath = lines[1]
            if len(lines) > 2 and lines[2] not in ["", "\n"]: use_cookie = lines[2].replace("\n", "") == True
            f.close()

    # create window
    global root
    root = tk.Tk()
    # window settings
    root.resizable(width=False, height=False)
    root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
    root.config(bg=COLOR_BG)
    root.title(APP_NAME)

    # style
    normal_text_font = tkFont.Font(family='Mgen+ 1c medium', size=15)
    s = ttk.Style()
    s.configure('YTDL.TFrame', background=COLOR_BG)
    s.configure('YTDL.TLabel', background=COLOR_BG)
    s.configure('YTDL.TRadioButton', background=COLOR_BG)
    s.configure('YTDL.TCheckBox', background=COLOR_BG)
    s.configure('YTDL.TEntry', background=COLOR_BG)

    # url
    url_frame = ttk.Frame(root, padding=0, style='YTDL.TFrame')
    url_frame.pack(pady=15)
    ttk.Label(url_frame, text='URL: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global urlEntry
    urlEntry = ttk.Entry(url_frame, width=150, style="YTDL.TEntry")
    urlEntry.pack(side=tk.LEFT)

    # output config
    output_frame = ttk.Frame(root, padding=3, style='YTDL.TFrame')
    output_frame.pack()
    ttk.Label(output_frame, text='Output Folder: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global outputEntry
    outputEntry = ttk.Entry(output_frame, width=150, style="YTDL.TEntry")
    outputEntry.insert(0, output_dir)
    outputEntry.pack(side=tk.LEFT)
    global browseOutDirButton
    browseOutDirButton = ttk.Button(output_frame, text='Browse', command=select_output_dir)
    browseOutDirButton.pack(side=tk.LEFT)

    # option 
    options_frame = ttk.Frame(root, padding=5, style="YTDL.TFrame")
    options_frame.pack()
    # radio button
    bottom_frame = ttk.Frame(options_frame, padding=5, style="YTDL.TFrame")
    bottom_frame.pack(side=tk.LEFT)
    ttk.Label(bottom_frame, text='Format: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global rButtonMP3, rButtonMP4, rButtonSplit, outputFormat
    outputFormat = tk.StringVar(value="mp3")
    rButtonMP3 = tk.Radiobutton(bottom_frame, text="mp3", variable=outputFormat, value="mp3", bg=COLOR_BG)
    rButtonMP3.pack(side=tk.LEFT)
    rButtonMP4 = tk.Radiobutton(bottom_frame, text="mp4", variable=outputFormat, value="mp4", bg=COLOR_BG)
    rButtonMP4.pack(side=tk.LEFT)
    rButtonSplit = tk.Radiobutton(bottom_frame, text="webm&m4a", variable=outputFormat, value="webm", bg=COLOR_BG)
    rButtonSplit.pack(side=tk.LEFT)

    # Auth
    cookie_frame = ttk.Frame(options_frame, padding=5, style='YTDL.TFrame')
    cookie_frame.pack(side=tk.RIGHT)
    ttk.Label(cookie_frame, text="Cookie: ", font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
    global cookieEntry, cookieCheckBox, cookieCheckBoxValue, browseCookieButton
    def on_cookie_checkbox_changed():
        if isinstance(cookieCheckBoxValue, tk.BooleanVar) and cookieCheckBoxValue.get():
            cookieEntry.config(state="normal")
            browseCookieButton.config(state="normal")
        else:
            cookieEntry.config(state="disable")
            browseCookieButton.config(state="disable")
    cookieCheckBoxValue = tk.BooleanVar(value=use_cookie)
    cookieCheckBox = tk.Checkbutton(cookie_frame, variable=cookieCheckBoxValue, command=on_cookie_checkbox_changed, bg=COLOR_BG)
    cookieCheckBox.pack(side=tk.LEFT)
    cookieEntry = ttk.Entry(cookie_frame, width=50, style="YTDL.TEntry")
    cookieEntry.insert(0, cookie_filepath)
    cookieEntry.config(state="normal" if use_cookie else "disable")
    cookieEntry.pack(side=tk.LEFT)
    browseCookieButton = ttk.Button(cookie_frame, text="Browse", command=select_cookie_file)
    browseCookieButton.config(state="normal" if use_cookie else "disable")
    browseCookieButton.pack(side=tk.LEFT)


    # duration
    # TODO it doesn't work correctly, so disabled.
    global stEntry, edEntry, DURATION_FLAG
    if DURATION_FLAG:
        vc = root.register(on_validate)
        ttk.Label(bottom_frame, text='Duration: ', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT,
                                                                                                    padx=(30, 0))
        stEntry = tk.Entry(bottom_frame, width=9, validate="key", validatecommand=(vc, "%P"))
        stEntry.pack(side=tk.LEFT)
        ttk.Label(bottom_frame, text='-', font=normal_text_font, style='YTDL.TLabel').pack(side=tk.LEFT)
        edEntry = tk.Entry(bottom_frame, width=9, validate="key", validatecommand=(vc, "%P"))
        edEntry.pack(side=tk.LEFT)
    else:
        vc = root.register(on_validate)
        ttk.Label(bottom_frame, text='Duration: ', font=normal_text_font, style='YTDL.TLabel')
        stEntry = tk.Entry(bottom_frame, width=9, validate="key", validatecommand=(vc, "%P"))
        ttk.Label(bottom_frame, text='-', font=normal_text_font, style='YTDL.TLabel')
        edEntry = tk.Entry(bottom_frame, width=9, validate="key", validatecommand=(vc, "%P"))

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
    root.wm_iconbitmap('image\\icon.ico')

    # Start
    root.protocol('WM_DELETE_WINDOW', close)
    root.mainloop()


main()
