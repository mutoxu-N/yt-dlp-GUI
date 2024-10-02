# GUI for yt-dlp
This software is GUI display for yt-dlp and provides multiple downloads.
このソフトは yt-dlp にGUIと一括処理を提供します。

## Installation / インストール
REQUIREMENTS: Python 3.11<br>
必要事項: Python 3.11

#### 1. DOWNLOAD Python / Pythonのダウンロード
Download and install Python3.11 from [here](https://www.python.org/downloads/).<br>
Python3.11を[ここ](https://www.python.org/downloads/)からダウンロードしてインストールしてください。
<br>

#### 2. DOWNLOAD Software / ソフトのダウンロード
Download Source code(zip) from [here](https://github.com/mutoxu-N/yt-dlp-GUI/releases) and unzip it.<br>
ソースコードのZipファイルを[ここ](https://github.com/mutoxu-N/yt-dlp-GUI/releases)からダウンロードして解凍して下さい。
![image](https://user-images.githubusercontent.com/55544957/221342354-944c1c70-9eda-4034-8465-57b1a2b2ad92.png)

#### 3. Install FFmpeg / FFmpegのインストール
Download FFmpeg from [here](https://ffmpeg.org/download.html). Unzip it and copy exes in the "fin" directory to yt-dlp folder.<br>
解凍後のフォルダ内に[FFmpeg](https://ffmpeg.org/download.html)をダウンロードしてください。 ファイルを解凍し, "bin"フォルダ内のexeファイルを"start.bat"と同じ場所に配置してください。

Example Image below. 以下のようにしてください。<br>
![image](https://github.com/mutoxu-N/yt-dlp-GUI/assets/55544957/468cd041-6ff6-4383-8b46-98bfca87197f)

#### 4. Setup / セットアップ
Run(click) "setup.bat".<br>
"setup.bat" を実行して下さい。

#### 5. Start / 実行
To start the software, run(click) "start.bat".<br>
"start.bat" を実行して、ソフトを起動します。


## Batch Download / 一括ダウンロード
You can process multiple videos at once. If you want to do it, you should make "download_list.txt" in output folder. YTDL will detect the download list.<br>
YTDL では、download_list.txt にURLを入力することで一括処理を行うことができます。 download_list は出力先フォルダ内に入れておくと勝手に認識されます。<br>
<br>
The way to set lists is like this.<br>
リストの設定は以下のように行います。<br>
![image](https://user-images.githubusercontent.com/55544957/221341313-bc4e9d92-8184-44d4-aa21-6aafcd5cebd3.png)

The format is "＜YouTube URL＞,＜extension＞".<br>
フォーマットは "＜YouTubeのURL＞,＜ファイルの種類＞" です。<br>

|extension|English|Japanese|
|:-:|:-:|:-:|
|mp3|mp3 audio only|mp3音声のみ|
|mp4|mp4 audio&video|mp4の動画(音声付き)|
|webm|2 files of webm video-only and m4a audio|webm動画のみとm4a音声|
| |same as mp3|mp3 と同じ|

## Download with using Cookie / クッキー用いたダウンロード
You can download premium videos and membership videos by using cookie. 
Then, you need to prepare the cookie data.
1. Export Cookie data of "youtube.com" into file. (Recommend: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc))
2. Select the file.

YouTubeプレミアムやメンバーシップ限定の動画は、ブラウザのCookieデータを指定することでダウンロードすることができます。
1. "youtube.com"のCookieデータを出力する. (拡張機能: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc))
2. 出力したファイルを選択する
