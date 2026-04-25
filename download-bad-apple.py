import yt_dlp

global download_name

def download_video(url):
    ydl_opts = {
        'format': 'best',  # Downloads the best available quality
        'outtmpl': '%(title)s.%(ext)s',  # Saves file with the video title
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

video_url = "https://youtube.com"
video_url = r"https://youtu.be/FtutLA63Cp8?si=Z7x8UZuOYAfJCATl"
download_video(video_url)
