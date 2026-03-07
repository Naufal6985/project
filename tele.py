import os
import time
import threading
import telebot
import yt_dlp

TOKEN = "8649438301:AAFdEMmOgPOdyESmHga2kSI5zB-3qqBIKng"

bot = telebot.TeleBot(TOKEN)

def download_audio(query):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(f"ytsearch1:{query}", download=True)

        video = info['entries'][0]

        filename = ydl.prepare_filename(video)

        filename = filename.rsplit(".",1)[0] + ".mp3"

        title = video.get("title","Unknown Title")

        artist = video.get("uploader","Unknown Artist")

        return filename,title,artist


def download_video(url):

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        filename = ydl.prepare_filename(info)

        return filename


def send_audio(chat_id,file_path,title,artist):

    with open(file_path,"rb") as f:

        bot.send_audio(
            chat_id,
            f,
            title=title,
            performer=artist
        )

    os.remove(file_path)


def send_video(chat_id,file_path):

    with open(file_path,"rb") as f:

        bot.send_video(chat_id,f)

    os.remove(file_path)


def play_music(message,query):

    bot.send_message(message.chat.id,"Mencari lagu...")

    try:

        file,title,artist = download_audio(query)

        send_audio(message.chat.id,file,title,artist)

    except Exception as e:

        bot.send_message(message.chat.id,f"Error: {e}")


def handle_yt(message,url):

    bot.send_message(message.chat.id,"Downloading video...")

    try:

        file = download_video(url)

        send_video(message.chat.id,file)

    except Exception as e:

        bot.send_message(message.chat.id,f"Error: {e}")


def handle_mp3(message,url):

    bot.send_message(message.chat.id,"Downloading audio...")

    try:

        file,title,artist = download_audio(url)

        send_audio(message.chat.id,file,title,artist)

    except Exception as e:

        bot.send_message(message.chat.id,f"Error: {e}")


@bot.message_handler(commands=['start'])
def start(message):

    bot.reply_to(message,
    "BOT DOWNLOADER\n\n"
    "/play judul lagu\n"
    "/yt link youtube\n"
    "/mp3 link youtube\n"
    "/ping")


@bot.message_handler(commands=['ping'])
def ping(message):

    start_time = time.time()

    msg = bot.send_message(message.chat.id,"Ping...")

    ms = int((time.time() - start_time)*1000)

    bot.edit_message_text(f"Pong {ms} ms",message.chat.id,msg.message_id)


@bot.message_handler(func=lambda m: True)
def handle(message):

    text = message.text

    if text.startswith("/play "):

        query = text[6:]

        threading.Thread(target=play_music,args=(message,query)).start()

    elif text.startswith("/yt "):

        url = text[4:]

        threading.Thread(target=handle_yt,args=(message,url)).start()

    elif text.startswith("/mp3 "):

        url = text[5:]

        threading.Thread(target=handle_mp3,args=(message,url)).start()

    else:

        bot.reply_to(message,"Gunakan /play /yt /mp3")


print("Bot berjalan...")

bot.infinity_polling()
