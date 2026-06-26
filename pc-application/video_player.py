"""
Модуль 3: Воспроизведение медиа-контента.
Видеоплеер с поддержкой звука (ffpyplayer + Tkinter).
GUI: Tkinter | Без использования vlc.MediaPlayer
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


class VideoPlayerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Видеоплеер — Video Player")
        self.root.geometry("900x640")
        self.root.minsize(720, 520)

        self.player = None
        self.photo: ImageTk.PhotoImage | None = None
        self.is_paused = False
        self.current_file: str | None = None
        self.after_id: str | None = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#1a1a2e", padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Video Player (Python + ffpyplayer)",
            font=("Segoe UI", 14, "bold"),
            fg="#ffd166",
            bg="#1a1a2e",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Видео и звук · ffpyplayer · Tkinter · без vlc.MediaPlayer",
            font=("Segoe UI", 9),
            fg="#8892a8",
            bg="#1a1a2e",
        ).pack(anchor="w")

        self.video_label = tk.Label(
            self.root,
            text="Откройте видеофайл для воспроизведения",
            bg="#111",
            fg="#666",
            anchor="center",
        )
        self.video_label.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        controls = tk.Frame(self.root, padx=16, pady=8)
        controls.pack(fill="x")

        tk.Button(controls, text="Открыть файл", command=self.open_file, width=14).pack(
            side="left", padx=(0, 6)
        )
        self.btn_play = tk.Button(
            controls, text="Play", command=self.toggle_play, width=10, state="disabled"
        )
        self.btn_play.pack(side="left", padx=6)
        tk.Button(
            controls, text="Stop", command=self.stop, width=10, state="normal"
        ).pack(side="left", padx=6)

        self.status = tk.StringVar(value="Файл не выбран.")
        tk.Label(self.root, textvariable=self.status, anchor="w", padx=16).pack(fill="x")

        hint = tk.Label(
            self.root,
            text="Поддерживаемые форматы: mp4, avi, mkv, webm, mov и др. (зависит от ffpyplayer/ffmpeg)",
            font=("Segoe UI", 8),
            fg="#888",
            padx=16,
        )
        hint.pack(fill="x", pady=(0, 12))

    def _ensure_ffpyplayer(self):
        try:
            from ffpyplayer.player import MediaPlayer
            return MediaPlayer
        except ImportError as exc:
            messagebox.showerror(
                "Ошибка",
                "Библиотека ffpyplayer не установлена.\n"
                "Выполните: pip install ffpyplayer",
            )
            raise exc

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[
                ("Video", "*.mp4 *.avi *.mkv *.webm *.mov *.wmv *.flv"),
                ("All", "*.*"),
            ],
        )
        if not path:
            return

        self.stop()
        MediaPlayer = self._ensure_ffpyplayer()

        try:
            self.player = MediaPlayer(path, ffpyplayer={"sync": "audio"})
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{exc}")
            return

        self.current_file = path
        self.is_paused = False
        self.btn_play.configure(state="normal", text="Pause")
        self.status.set(f"Воспроизведение: {os.path.basename(path)}")
        self._schedule_frame()

    def _schedule_frame(self) -> None:
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.after_id = self.root.after(10, self._update_frame)

    def _update_frame(self) -> None:
        if self.player is None:
            return

        if self.is_paused:
            self.after_id = self.root.after(100, self._update_frame)
            return

        frame, val = self.player.get_frame()

        if val == "eof":
            self.status.set("Воспроизведение завершено.")
            self.btn_play.configure(text="Play")
            self.is_paused = True
            return

        if frame is not None:
            img, _pts = frame
            size = img.get_size()
            data = img.to_bytearray()[0]
            pil_img = Image.frombytes("RGB", size, bytes(data))
            display = pil_img.copy()
            label_w = max(self.video_label.winfo_width(), 640)
            label_h = max(self.video_label.winfo_height(), 360)
            display.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(display)
            self.video_label.configure(image=self.photo, text="")

        delay_ms = 10
        if val is not None and isinstance(val, (int, float)) and val > 0:
            delay_ms = max(1, int(val * 1000))

        self.after_id = self.root.after(delay_ms, self._update_frame)

    def toggle_play(self) -> None:
        if self.player is None:
            return

        self.is_paused = not self.is_paused
        self.player.set_pause(self.is_paused)

        if self.is_paused:
            self.btn_play.configure(text="Play")
            self.status.set("Пауза")
        else:
            self.btn_play.configure(text="Pause")
            name = os.path.basename(self.current_file) if self.current_file else ""
            self.status.set(f"Воспроизведение: {name}")
            self._schedule_frame()

    def stop(self) -> None:
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        if self.player is not None:
            self.player.close_player()
            self.player = None

        self.is_paused = False
        self.btn_play.configure(state="disabled", text="Play")
        self.video_label.configure(
            image="",
            text="Откройте видеофайл для воспроизведения",
        )
        self.photo = None

    def on_close(self) -> None:
        self.stop()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    VideoPlayerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
