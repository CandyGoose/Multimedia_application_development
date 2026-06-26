"""
Модуль 2: Доступ к медиа-контенту.
Загрузка видео по URL с помощью yt-dlp.
GUI: Tkinter
"""

import os
import re
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class VideoDownloadApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Загрузка видео — Download Video")
        self.root.geometry("720x420")
        self.root.minsize(640, 360)

        self.download_thread: threading.Thread | None = None
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#1a1a2e", padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Download any Video using Python",
            font=("Segoe UI", 14, "bold"),
            fg="#00d9f5",
            bg="#1a1a2e",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="yt-dlp · Tkinter · один файл без FFmpeg (по умолчанию)",
            font=("Segoe UI", 9),
            fg="#8892a8",
            bg="#1a1a2e",
        ).pack(anchor="w")

        form = tk.Frame(self.root, padx=16, pady=16)
        form.pack(fill="x")

        tk.Label(form, text="URL видео:").grid(row=0, column=0, sticky="w", pady=4)
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(form, textvariable=self.url_var, width=70)
        url_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)

        tk.Label(form, text="Папка сохранения:").grid(row=1, column=0, sticky="w", pady=4)
        self.folder_var = tk.StringVar(
            value=os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        )
        folder_entry = tk.Entry(form, textvariable=self.folder_var, width=70)
        folder_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        tk.Button(form, text="Обзор…", command=self.choose_folder).grid(
            row=1, column=2, padx=(8, 0)
        )

        tk.Label(form, text="Формат:").grid(row=2, column=0, sticky="w", pady=4)
        self.format_var = tk.StringVar(value="best (один файл)")
        format_combo = ttk.Combobox(
            form,
            textvariable=self.format_var,
            values=[
                "best (один файл)",
                "mp4 (один файл)",
                "webm (один файл)",
                "лучшее качество (нужен FFmpeg)",
                "audio only (mp3, нужен FFmpeg)",
            ],
            state="readonly",
            width=32,
        )
        format_combo.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=4)

        form.grid_columnconfigure(1, weight=1)

        btn_bar = tk.Frame(self.root, padx=16, pady=8)
        btn_bar.pack(fill="x")
        self.btn_download = tk.Button(
            btn_bar,
            text="Скачать видео",
            command=self.start_download,
            bg="#0f3460",
            fg="white",
            width=18,
        )
        self.btn_download.pack(side="left")

        self.progress = ttk.Progressbar(self.root, mode="indeterminate", length=400)
        self.progress.pack(fill="x", padx=16, pady=8)

        self.status = tk.StringVar(value="Введите URL и нажмите «Скачать видео».")
        tk.Label(self.root, textvariable=self.status, anchor="w", padx=16).pack(fill="x")

        log_frame = tk.LabelFrame(self.root, text="Журнал", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.log = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        scroll = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.folder_var.set(folder)

    def append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_status(self, message: str) -> None:
        self.status.set(message)

    @staticmethod
    def strip_ansi(text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    @staticmethod
    def ffmpeg_installed() -> bool:
        return shutil.which("ffmpeg") is not None

    def build_ydl_opts(self, folder: str, fmt: str) -> dict:
        base = {
            "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
            "progress_hooks": [self.progress_hook],
            "noplaylist": True,
        }

        if fmt == "audio only (mp3, нужен FFmpeg)":
            if not self.ffmpeg_installed():
                raise RuntimeError(
                    "Для MP3 нужен FFmpeg.\n"
                    "Установите: winget install ffmpeg\n"
                    "или скачайте с https://ffmpeg.org и добавьте в PATH."
                )
            base["format"] = "bestaudio/best"
            base["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
            ]
            return base

        if fmt == "лучшее качество (нужен FFmpeg)":
            if not self.ffmpeg_installed():
                raise RuntimeError(
                    "Слияние видео+аудио требует FFmpeg.\n"
                    "Установите: winget install ffmpeg\n"
                    "или выберите формат «один файл»."
                )
            base["format"] = "bestvideo+bestaudio/best"
            return base

        if fmt == "mp4 (один файл)":
            base["format"] = (
                "best[ext=mp4][vcodec!=none][acodec!=none]/"
                "best[ext=mp4]/b"
            )
            return base

        if fmt == "webm (один файл)":
            base["format"] = (
                "best[ext=webm][vcodec!=none][acodec!=none]/"
                "best[ext=webm]/b"
            )
            return base

        # best (один файл) — видео и звук в одном потоке, FFmpeg не нужен
        base["format"] = "best*[vcodec!=none][acodec!=none]/b/best"
        return base

    def progress_hook(self, data: dict) -> None:
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            if total:
                pct = downloaded / total * 100
                msg = f"Загрузка: {pct:.1f}%"
            else:
                msg = "Загрузка…"
            self.root.after(0, lambda: self.set_status(msg))
        elif data.get("status") == "finished":
            filename = data.get("filename", "")
            self.root.after(0, lambda: self.append_log(f"Файл получен: {filename}"))

    def start_download(self) -> None:
        if self.is_downloading:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Внимание", "Введите URL видео.")
            return

        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning("Внимание", "Укажите папку сохранения.")
            return

        os.makedirs(folder, exist_ok=True)

        try:
            import yt_dlp
        except ImportError:
            messagebox.showerror(
                "Ошибка",
                "Библиотека yt-dlp не установлена.\n"
                "Выполните: pip install yt-dlp",
            )
            return

        fmt = self.format_var.get()
        try:
            ydl_opts = self.build_ydl_opts(folder, fmt)
        except RuntimeError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        self.is_downloading = True
        self.btn_download.configure(state="disabled")
        self.progress.start(12)
        self.append_log(f"Начало загрузки: {url}")
        self.set_status("Подключение…")

        def worker() -> None:
            import yt_dlp

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title", "video")
                self.root.after(
                    0,
                    lambda: self._on_success(title, folder),
                )
            except Exception as exc:
                err = str(exc)
                self.root.after(0, lambda: self._on_error(err))

        self.download_thread = threading.Thread(target=worker, daemon=True)
        self.download_thread.start()

    def _on_success(self, title: str, folder: str) -> None:
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.progress.stop()
        self.set_status(f"Готово: {title}")
        self.append_log(f"Успешно сохранено в: {folder}")
        messagebox.showinfo("Готово", f"Видео «{title}» загружено.")

    def _on_error(self, error: str) -> None:
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.progress.stop()
        self.set_status("Ошибка загрузки.")
        clean = self.strip_ansi(error)
        if "ffmpeg" in clean.lower():
            clean += (
                "\n\nВыберите формат «best (один файл)» — FFmpeg не нужен.\n"
                "Или установите: winget install ffmpeg"
            )
        self.append_log(f"Ошибка: {clean}")
        messagebox.showerror("Ошибка", clean)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    VideoDownloadApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
