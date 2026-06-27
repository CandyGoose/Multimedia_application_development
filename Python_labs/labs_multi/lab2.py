import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import imageio_ffmpeg as ffmpeg

available_resolutions = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']

def list_formats(url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            available_formats = []
            for f in formats:
                if 'height' in f and f['height']:
                    resolution = f"{f['height']}p"
                    if resolution in available_resolutions:
                        available_formats.append(f"{f['format_id']} - {resolution}")
            return available_formats
    except Exception as e:
        return f"Ошибка: {e}"

def fetch_formats():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Ошибка", "Введите ссылку на видео!")
        return

    available_formats = list_formats(url)
    if isinstance(available_formats, str):
        messagebox.showerror("Ошибка", available_formats)
        return

    quality_menu['values'] = available_formats
    quality_menu.set('')

def download_video():
    url = url_entry.get()
    download_dir = dir_var.get()
    selected_format = quality_menu.get()

    if not url:
        messagebox.showerror("Ошибка", "Введите ссылку на видео!")
        return
    if not download_dir:
        messagebox.showerror("Ошибка", "Выберите папку для сохранения видео!")
        return
    if not selected_format:
        messagebox.showerror("Ошибка", "Выберите качество видео!")
        return

    format_id = selected_format.split(" -")[0]
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    if not ffmpeg_path:
        messagebox.showerror("Ошибка", "FFmpeg не найден!")
        return

    ydl_opts = {
        'format': f"{format_id}+bestaudio/best",
        'outtmpl': f'{download_dir}/%(title)s_{format_id}.%(ext)s',
        'ffmpeg_location': ffmpeg_path
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        messagebox.showinfo("✅ Успех", "Видео успешно загружено!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при скачивании:\n{e}")

def choose_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        dir_var.set(folder_selected)

# GUI
root = tk.Tk()
root.title("📥 YouTube Downloader")
root.geometry("500x540")
root.configure(bg="#1e1f29")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")

# Тёмный стиль
style.configure("TFrame", background="#2c2f33")
style.configure("TLabel", background="#2c2f33", foreground="#ffffff", font=("Segoe UI", 10))
style.configure("TButton",
                background="#5865f2",
                foreground="#ffffff",
                font=("Segoe UI", 10, "bold"),
                borderwidth=0,
                focusthickness=3,
                focuscolor="#99aab5")
style.map("TButton",
          background=[("active", "#4752c4")])
style.configure("TCombobox",
                fieldbackground="#ffffff",
                background="#ffffff",
                foreground="#000",
                arrowcolor="#5865f2",
                relief="flat")

main_frame = ttk.Frame(root, padding="20 20 20 20", relief="flat", style="TFrame")
main_frame.pack(fill=tk.BOTH, expand=True)

# ---------- UI ELEMENTS ----------

header = ttk.Label(main_frame, text="🎬 YouTube Загрузчик", font=("Segoe UI", 16, "bold"), anchor="center")
header.pack(pady=10)

# Ссылка
ttk.Label(main_frame, text="🔗 Ссылка на видео:").pack(anchor='w', pady=(15, 3))
url_entry = ttk.Entry(main_frame, width=50, font=("Segoe UI", 10))
url_entry.pack(pady=5, ipady=4)

def paste_from_clipboard(event=None):
    try:
        url_entry.insert(tk.INSERT, root.clipboard_get())
    except tk.TclError:
        pass

# Контекстное меню (ПКМ → Вставить)
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="📋 Вставить", command=paste_from_clipboard)

def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)

url_entry.bind("<Control-v>", paste_from_clipboard)  # Windows/Linux
url_entry.bind("<Command-v>", paste_from_clipboard)  # macOS
url_entry.bind("<Button-3>", show_context_menu)      # ПКМ


# Форматы
fetch_button = ttk.Button(main_frame, text="🔍 Найти доступные форматы", command=fetch_formats)
fetch_button.pack(pady=10, ipadx=6, ipady=3)

ttk.Label(main_frame, text="📺 Качество:").pack(anchor='w', pady=(15, 3))
quality_menu = ttk.Combobox(main_frame, width=48, font=("Segoe UI", 10), state="readonly")
quality_menu.pack(pady=5, ipady=3)

# Папка
ttk.Label(main_frame, text="📁 Папка сохранения:").pack(anchor='w', pady=(15, 3))
dir_var = tk.StringVar()
dir_frame = tk.Frame(main_frame, bg="#2c2f33")
dir_frame.pack(fill=tk.X, pady=5)

dir_entry = ttk.Entry(dir_frame, textvariable=dir_var, font=("Segoe UI", 10), width=42)
dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

dir_btn = ttk.Button(dir_frame, text="Выбрать", command=choose_directory)
dir_btn.pack(side=tk.RIGHT, padx=5)

# Скачать
download_button = ttk.Button(main_frame, text="⬇️ Скачать видео", command=download_video)
download_button.pack(pady=30, ipadx=10, ipady=5)

root.mainloop()
