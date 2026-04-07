import telebot
from telebot import apihelper, types
import os
import time
import platform
import shutil
import yt_dlp
import threading
import urllib.request
import json
from functools import wraps
import tempfile

TOKEN = "PASTE_TOKEN_KAMU_DI_SINI"

apihelper.CONNECT_TIMEOUT = 20
apihelper.READ_TIMEOUT = 20
apihelper.RETRY_ON_ERROR = True

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)

start_time = time.time()

users = set()
broadcast_store = {}
username_db = {}
OWNERS = set()
confess_threads = {}
BOT_RUNNING = True
SOURCE_FILE = os.path.join(os.path.dirname(__file__), "source.py")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "tmp_downloads")
os.makedirs(TEMP_DIR, exist_ok=True)

for file_name, target_set, target_dict in [
    ("users.txt", users, None),
    ("owners.txt", OWNERS, None),
    ("username.txt", None, username_db)
]:
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if file_name == "username.txt":
                    try:
                        uid, uname = line.split("|")
                        username_db[uname] = int(uid)
                    except:
                        pass
                else:
                    try:
                        target_set.add(int(line))
                    except:
                        pass

def save_user(user):
    uid = user.id
    uname = user.username

    if uid not in users:
        users.add(uid)
        with open("users.txt", "a", encoding="utf-8") as f:
            f.write(f"{uid}\n")

    if uname:
        uname = uname.lower()
        username_db[uname] = uid

        existing = set()
        if os.path.exists("username.txt"):
            with open("username.txt", "r", encoding="utf-8") as f:
                existing = set(x.strip() for x in f if x.strip())

        entry = f"{uid}|{uname}"
        if entry not in existing:
            with open("username.txt", "a", encoding="utf-8") as f:
                f.write(entry + "\n")

def check_bot_running(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not BOT_RUNNING and message.from_user.id not in OWNERS:
            bot.reply_to(message, "⛔ Bot sedang dihentikan sementara")
            return
        return func(message, *args, **kwargs)
    return wrapper

def notify_owners(text):
    for o in OWNERS:
        try:
            bot.send_message(o, text)
        except:
            pass

def save_self():
    try:
        with open(__file__, "r", encoding="utf-8") as current, open(SOURCE_FILE, "w", encoding="utf-8") as f:
            f.write(current.read())
    except Exception as e:
        print("Gagal menyimpan source code:", e)

def cleanup_temp():
    try:
        for file in os.listdir(TEMP_DIR):
            path = os.path.join(TEMP_DIR, file)
            if os.path.isfile(path):
                os.remove(path)
    except:
        pass

def get_storage_info():
    try:
        disk = shutil.disk_usage("/")
        total = disk.total // (1024**3)
        used = disk.used // (1024**3)
        free = disk.free // (1024**3)
        percent = int((used / total) * 100) if total else 0
        return total, used, free, percent
    except:
        return 0, 0, 0, 0

save_self()
cleanup_temp()

def get_distro():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "PRETTY_NAME" in line:
                    return line.split("=")[1].replace('"', '').strip()
    except:
        return "Unknown"

def get_isp():
    try:
        data = urllib.request.urlopen("https://ipinfo.io/json").read()
        info = json.loads(data)
        return info.get("org", "Unknown")
    except:
        return "Unknown"

def get_uptime():
    uptime = int(time.time() - start_time)
    d = uptime // 86400
    h = (uptime % 86400) // 3600
    m = (uptime % 3600) // 60
    s = uptime % 60
    return f"{d}d {h}h {m}m {s}s"

def download_video(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": os.path.join(TEMP_DIR, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def download_audio(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(TEMP_DIR, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        video = info["entries"][0]
        filename = ydl.prepare_filename(video)
        title = video["title"]
        artist = video["uploader"]
        return filename, title, artist

def process_music(message, query):
    msg = bot.send_message(message.chat.id, "🎵 mencari lagu...")
    file = None
    try:
        file, title, artist = download_audio(query)
        bot.edit_message_text("📤 uploading audio...", message.chat.id, msg.message_id)
        with open(file, "rb") as f:
            bot.send_audio(message.chat.id, f, title=title, performer=artist)
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        try:
            bot.edit_message_text(f"❌ Error: {e}", message.chat.id, msg.message_id)
        except:
            pass
    finally:
        if file and os.path.exists(file):
            os.remove(file)

def process_play_input(message):
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "❌ Nama lagu kosong")
        return
    threading.Thread(target=process_music, args=(message, query)).start()

def process_video(message, url):
    msg = bot.send_message(message.chat.id, "📥 downloading...")
    file = None
    try:
        file = download_video(url)
        bot.edit_message_text("📤 uploading...", message.chat.id, msg.message_id)
        with open(file, "rb") as f:
            bot.send_video(message.chat.id, f)
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        try:
            bot.edit_message_text(f"❌ Error: {e}", message.chat.id, msg.message_id)
        except:
            pass
    finally:
        if file and os.path.exists(file):
            os.remove(file)

@bot.message_handler(commands=["start"])
@check_bot_running
def start(message):
    save_user(message.from_user)
    bot.reply_to(message, "👋 Welcome\n\nKetik /menu")

@bot.message_handler(commands=["menu"])
@check_bot_running
def menu(message):
    save_user(message.from_user)

    text = """
╔══════════════════╗
🤖 BOT MENU
╚══════════════════╝

🎵 Play lagu
📥 Download video
💌 Confess
📊 Stats

Klik tombol di bawah 👇
"""

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎵 Play", callback_data="play"),
        types.InlineKeyboardButton("📥 Download", callback_data="download")
    )
    markup.row(
        types.InlineKeyboardButton("💌 Confess", callback_data="confess"),
        types.InlineKeyboardButton("📊 Stats", callback_data="stats")
    )
    markup.row(
        types.InlineKeyboardButton("⚡ Ping", callback_data="ping"),
        types.InlineKeyboardButton("🖥 System", callback_data="system")
    )

    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
@check_bot_running
def callback_handler(call):
    bot.answer_callback_query(call.id)

    if call.data == "play":
        msg = bot.send_message(call.message.chat.id, "🎵 Masukkan nama lagu:")
        bot.register_next_step_handler(msg, process_play_input)

    elif call.data == "download":
        bot.send_message(call.message.chat.id, "Gunakan /download link")

    elif call.data == "confess":
        bot.send_message(call.message.chat.id, "Gunakan /confess username pesan")

    elif call.data == "stats":
        stats(call.message)

    elif call.data == "ping":
        ping(call.message)

    elif call.data == "system":
        systeminfo(call.message)

@bot.message_handler(commands=["stats"])
@check_bot_running
def stats(message):
    if message.from_user.id not in OWNERS:
        return
    bot.send_message(message.chat.id, f"📊 Users: {len(users)}\n👑 Owners: {len(OWNERS)}")

@bot.message_handler(commands=["owners"])
@check_bot_running
def owners(message):
    if message.from_user.id not in OWNERS:
        return
    bot.send_message(message.chat.id, "👑 OWNER LIST\n\n" + "\n".join(str(o) for o in OWNERS))

@bot.message_handler(commands=["addowner"])
def addowner(message):
    if message.from_user.id not in OWNERS:
        bot.reply_to(message, "⛔ Kamu bukan owner")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "/addowner id/username")
        return
    target = args[1].replace("@", "").lower()
    try:
        if target.isdigit():
            uid = int(target)
        else:
            if target not in username_db:
                bot.reply_to(message, "❌ Username belum pernah chat bot")
                return
            uid = username_db[target]

        if uid in OWNERS:
            bot.reply_to(message, "❌ User sudah owner")
            return

        OWNERS.add(uid)
        with open("owners.txt", "a", encoding="utf-8") as f:
            f.write(str(uid) + "\n")
        bot.reply_to(message, "✅ Owner ditambahkan")
    except:
        bot.reply_to(message, "❌ ID/Username tidak valid")

@bot.message_handler(commands=["delowner"])
def delowner(message):
    if message.from_user.id not in OWNERS:
        bot.reply_to(message, "⛔ Kamu bukan owner")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "/delowner id/username")
        return
    target = args[1].replace("@", "").lower()
    try:
        if target.isdigit():
            uid = int(target)
        else:
            if target not in username_db:
                bot.reply_to(message, "❌ Username belum pernah chat bot")
                return
            uid = username_db[target]

        if uid not in OWNERS:
            bot.reply_to(message, "❌ User bukan owner")
            return

        OWNERS.remove(uid)
        with open("owners.txt", "w", encoding="utf-8") as f:
            for o in OWNERS:
                f.write(str(o) + "\n")
        bot.reply_to(message, "❌ Owner dihapus")
    except:
        bot.reply_to(message, "❌ ID/Username tidak valid")

@bot.message_handler(commands=["ping"])
@check_bot_running
def ping(message):
    start_t = time.time()
    msg = bot.send_message(message.chat.id, "🏓 Mengukur ping...")
    ms = round((time.time() - start_t) * 1000, 2)
    bot.edit_message_text(f"🏓 Pong: {ms} ms", message.chat.id, msg.message_id)

@bot.message_handler(commands=["systeminfo"])
@check_bot_running
def systeminfo(message):
    distro = get_distro()
    kernel = platform.release()
    cpu = os.cpu_count()
    arch = platform.machine()
    python_ver = platform.python_version()
    uptime = get_uptime()
    isp = get_isp()
    try:
        ip = urllib.request.urlopen("https://api.ipify.org").read().decode()
    except:
        ip = "Unknown"

    mem_total = mem_available = 0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line:
                    mem_total = int(line.split()[1]) // 1024
                if "MemAvailable" in line:
                    mem_available = int(line.split()[1]) // 1024
    except:
        pass

    mem_used = mem_total - mem_available
    ram_percent = int((mem_used / mem_total) * 100) if mem_total else 0

    disk = shutil.disk_usage("/")
    disk_total = disk.total // (1024**3)
    disk_used = disk.used // (1024**3)
    disk_free = disk.free // (1024**3)
    disk_percent = int((disk_used / disk_total) * 100) if disk_total else 0

    ram_bar = "█" * (ram_percent // 10) + "░" * (10 - (ram_percent // 10))
    disk_bar = "█" * (disk_percent // 10) + "░" * (10 - (disk_percent // 10))

    text = f"""
╔════════════════════╗
   🖥 BOT SYSTEM INFO
╚════════════════════╝

System
┣ OS : {distro}
┣ Kernel : {kernel}
┣ CPU : {cpu} Core
┣ Arch : {arch}

Runtime
┣ Python : {python_ver}
┗ Uptime : {uptime}

RAM
┣ Used : {mem_used} MB
┣ Free : {mem_available} MB
┣ Total : {mem_total} MB
┣ Usage : {ram_percent}%
┗ [{ram_bar}]

🗄 Storage
┣ Used : {disk_used} GB
┣ Free : {disk_free} GB
┣ Total : {disk_total} GB
┣ Usage : {disk_percent}%
┗ [{disk_bar}]

🌐 Network
┣ ISP : {isp}
┗ IP : {ip}

🤖 Bot
┗ Status : Online

About
👩🏻‍💻Owner : Naufal Alhakim ( @naufal6985).
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["broadcast"])
@check_bot_running
def broadcast(message):
    if message.from_user.id not in OWNERS:
        bot.reply_to(message, "⛔ Kamu bukan owner")
        return

    sent = 0
    failed = 0
    msg_ids = []

    text = message.text.replace("/broadcast", "", 1).strip()
    owner_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    if not message.reply_to_message and not text:
        bot.reply_to(
            message,
            "❌ Cara pakai:\n\n/broadcast pesan\natau reply pesan lalu kirim /broadcast"
        )
        return

    status = bot.reply_to(message, "📢 Broadcast sedang dikirim...")

    for u in users:
        try:
            header = bot.send_message(u, f"📢 Broadcast From Owner\n👤 {owner_name}")
            msg_ids.append((u, header.message_id))

            if message.reply_to_message:
                copied = bot.copy_message(
                    chat_id=u,
                    from_chat_id=message.chat.id,
                    message_id=message.reply_to_message.message_id
                )
                msg_ids.append((u, copied.message_id))

                if text:
                    extra = bot.send_message(
                        u,
                        text,
                        reply_to_message_id=copied.message_id
                    )
                    msg_ids.append((u, extra.message_id))
            else:
                body = bot.send_message(
                    u,
                    text,
                    reply_to_message_id=header.message_id
                )
                msg_ids.append((u, body.message_id))

            sent += 1
            time.sleep(0.08)
        except:
            failed += 1

    broadcast_store["last"] = msg_ids

    bot.edit_message_text(
        f"✅ Broadcast selesai\n\n📤 Berhasil: {sent}\n❌ Gagal: {failed}",
        message.chat.id,
        status.message_id
    )

@bot.message_handler(commands=["download"])
@check_bot_running
def downloader(message):
    save_user(message.from_user)
    url = message.text.replace("/download", "").strip()
    if not url:
        bot.reply_to(message, "Masukkan link")
        return
    threading.Thread(target=process_video, args=(message, url)).start()

@bot.message_handler(commands=["confess"])
@check_bot_running
def confess_handler(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "❌ Format: /confess @username pesan")
        return

    username = args[1].replace("@", "").lower()
    text = " ".join(args[2:])

    if username not in username_db:
        bot.reply_to(message, "❌ User belum pernah chat bot")
        return

    target_id = username_db[username]
    sender_id = message.from_user.id

    try:
        sent = bot.send_message(target_id, f"💌 Anonymous Confession\n\n{text}\n\n↩ Reply pesan ini untuk membalas")
        confess_threads[(target_id, sent.message_id)] = sender_id
        bot.reply_to(message, "✅ Confess terkirim")
        for owner in OWNERS:
            bot.send_message(owner, f"CONFESS LOG\nSender : @{message.from_user.username}\nID : {sender_id}\nTarget : @{username}\n{text}")
    except:
        bot.reply_to(message, "❌ Gagal mengirim confession, user mungkin belum chat bot")

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
@check_bot_running
def reply_confess(message):
    key = (message.chat.id, message.reply_to_message.message_id)
    if key in confess_threads:
        sender_id = confess_threads[key]
        try:
            sent = bot.send_message(sender_id, f"📩 Balasan Confess\n{message.text}")
            confess_threads[(sender_id, sent.message_id)] = message.chat.id
        except:
            bot.reply_to(message, "❌ Gagal membalas confession")

@bot.message_handler(commands=["stopbot"])
def stopbot(message):
    global BOT_RUNNING
    if message.from_user.id not in OWNERS:
        return
    BOT_RUNNING = False
    bot.reply_to(message, "⛔ Bot dihentikan sementara")
    notify_owners(f"⛔ Bot dihentikan oleh @{message.from_user.username}")

@bot.message_handler(commands=["startbot"])
def startbot(message):
    global BOT_RUNNING
    if message.from_user.id not in OWNERS:
        return
    BOT_RUNNING = True
    bot.reply_to(message, "✅ Bot dinyalakan")
    notify_owners(f"🤖 Bot dinyalakan oleh @{message.from_user.username}")

@bot.message_handler(commands=["statusbot"])
def statusbot(message):
    save_user(message.from_user)
    bot.send_message(message.chat.id, "Status Bot : ✅ RUNNING" if BOT_RUNNING else "⛔ STOPPED")

@bot.message_handler(commands=["sources"])
@check_bot_running
def sources(message):
    if not os.path.exists(SOURCE_FILE):
        bot.send_message(message.chat.id, "❌ File sumber tidak ditemukan")
        return
    if os.path.getsize(SOURCE_FILE) == 0:
        bot.send_message(message.chat.id, "❌ File sumber kosong")
        return
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        shutil.copy2(SOURCE_FILE, temp_file.name)
        temp_file.close()
        doc = telebot.types.InputFile(temp_file.name, file_name="fallv10.py")
        bot.send_document(message.chat.id, doc)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Gagal kirim file: {e}")
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.remove(temp_file.name)

@bot.message_handler(commands=["cleantemp"])
@check_bot_running
def cleantemp(message):
    if message.from_user.id not in OWNERS:
        return
    cleanup_temp()
    bot.reply_to(message, "🧹 Folder tmp_downloads berhasil dibersihkan")

@bot.message_handler(commands=["storage"])
@check_bot_running
def storage(message):
    if message.from_user.id not in OWNERS:
        return
    total, used, free, percent = get_storage_info()
    bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))
    bot.send_message(
        message.chat.id,
        f"🗄 Storage Info\n\n┣ Used : {used} GB\n┣ Free : {free} GB\n┣ Total : {total} GB\n┣ Usage : {percent}%\n┗ [{bar}]"
    )

@bot.message_handler(commands=["cleanupall"])
@check_bot_running
def cleanupall(message):
    if message.from_user.id not in OWNERS:
        return
    removed = 0
    try:
        for file in os.listdir("."):
            path = os.path.join(".", file)
            if os.path.isfile(path):
                lower = file.lower()
                if lower.endswith((".mp3", ".mp4", ".m4a", ".webm", ".mkv", ".part", ".opus")):
                    os.remove(path)
                    removed += 1
    except:
        pass

    try:
        for file in os.listdir(TEMP_DIR):
            path = os.path.join(TEMP_DIR, file)
            if os.path.isfile(path):
                os.remove(path)
                removed += 1
    except:
        pass

    bot.reply_to(message, f"🧹 Cleanup selesai\n📦 File dihapus: {removed}")

@bot.message_handler(func=lambda m: True)
@check_bot_running
def autosave(message):
    save_user(message.from_user)

print("Bot running")
while True:
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
