import time
import sys

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

def type_text(text, color=RESET, letter_delay=0.08, animate=True):
    if animate:
        for char in text:
            sys.stdout.write(color + char + RESET)
            sys.stdout.flush()
            time.sleep(letter_delay)
        print()
    else:
        print(color + text + RESET)

lyrics = [
    (CYAN, " Aku mau cari jalan tengah", 0.06, 0, True),
    (CYAN, " Buat kamu, apa yang nggak bisa? ", 0.06, 0, True),
    (CYAN, " Ajak kamu ke angkasa", 0.06, 0, True),
    (YELLOW," Go to the moon, kita berdansa", 0.06, 0.6, True),
    (RESET, "Aku wish you best", 0.06, 1.8, False),
    (RESET, "Kamu yang the best", 0.06, 1.6, False),
    (RESET, "Kata mamaku", 0.06, 1.7, False),
    (RESET, "Masih muda", 0.06, 0.8, False), 
    (RESET, "Banyak Waktu", 0.06, 1.5, False),
    (CYAN, "KU MERASAKAN APA", 0.06, 0, True), 
    (RED, "YANG KAU RASAKAN", 0.06, 0.6, True), 
    (RED, "  TANPA RAGU", 0.06, 1, False), 
    (RED, "  KU BILANG", 0.06, 1, False), 
    (RED, "  KAMU YANG PALING", 0.06, 0.7, False), 
    (RED, "PAHAM AKU", 0.06, 0.6, False)
]

for color, line, letter_delay, line_delay, animate in lyrics:
    type_text(line, color, letter_delay, animate)
    time.sleep(line_delay)
    if "Go to the moon, kita berdansa" in line:
        print("\n" * 2)
    if "Banyak Waktu" in line:
        print("\n" * 2)
