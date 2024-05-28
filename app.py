from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, safe_join
from pytube import YouTube, Playlist
from threading import Thread
import os
import time
import moviepy.editor as mp

app = Flask(__name__)
app.secret_key = 'your_secret_key'
default_download_folder = 'downloads'

if not os.path.exists(default_download_folder):
    os.makedirs(default_download_folder)

def download_video_thread(url, save_path, convert, audio_format):
    try:
        start_time = time.time()
        yt = YouTube(url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video_path = os.path.join(save_path, f"{yt.title}.mp4")
        video.download(save_path)
        elapsed_time = time.time() - start_time
        flash(f"Video '{yt.title}' downloaded successfully in {elapsed_time:.2f} seconds.", 'success')

        if convert:
            convert_to_audio(video_path, audio_format)
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')

def download_playlist_thread(url, save_path, convert, audio_format):
    try:
        start_time = time.time()
        playlist = Playlist(url)
        for video_url in playlist.video_urls:
            yt = YouTube(video_url)
            video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            video_path = os.path.join(save_path, f"{yt.title}.mp4")
            video.download(save_path)
            if convert:
                convert_to_audio(video_path, audio_format)
        elapsed_time = time.time() - start_time
        flash(f"Playlist downloaded successfully in {elapsed_time:.2f} seconds.", 'success')
    except Exception as e:
        flash(f"An error occurred: {e}", 'danger')

def convert_to_audio(video_path, audio_format):
    try:
        audio_path = os.path.splitext(video_path)[0] + f".{audio_format}"
        video_clip = mp.VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_path)
        audio_clip.close()
        video_clip.close()
        flash(f"Converted '{os.path.basename(video_path)}' to audio format '{audio_format}'.", 'success')
    except Exception as e:
        flash(f"Error converting video to audio: {e}", 'danger')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    download_type = request.form['download_type']
    convert = 'convert' in request.form
    audio_format = request.form['audio_format']
    save_path = request.form['save_path'] if request.form['save_path'] else default_download_folder

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    if url:
        if 'video' in download_type:
            thread = Thread(target=download_video_thread, args=(url, save_path, convert, audio_format))
        else:
            thread = Thread(target=download_playlist_thread, args=(url, save_path, convert, audio_format))
        thread.start()
        flash('Download started...', 'info')
    else:
        flash('Please enter a valid URL', 'danger')
    return redirect(url_for('index'))

@app.route('/downloads/<filename>')
def downloads(filename):
    return send_from_directory(default_download_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)

