"""
Модуль 1: Обработка изображений.
Сравнение своего grayscale (DIY) с готовым эталонным серым + Heat Map.
GUI: Tkinter | Библиотека: Pillow (PIL), NumPy
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk


class ImageProcessingApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Обработка изображений — Heat Map Diff")
        self.root.geometry("1200x780")
        self.root.minsize(960, 640)

        self.original: Image.Image | None = None
        self.preview_refs: list[ImageTk.PhotoImage] = []
        self.preview_sources: dict[str, Image.Image] = {}
        self.heatmap_result: Image.Image | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#1a1a2e", padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Heat Map: свой Grayscale vs автоматический (PIL)",
            font=("Segoe UI", 14, "bold"),
            fg="#00f5a0",
            bg="#1a1a2e",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Pillow (PIL) · getpixel/putpixel · NumPy · Tkinter",
            font=("Segoe UI", 9),
            fg="#8892a8",
            bg="#1a1a2e",
        ).pack(anchor="w")

        controls = tk.Frame(self.root, padx=16, pady=10)
        controls.pack(fill="x")

        tk.Button(
            controls,
            text="Оригинал",
            command=self.load_original,
            width=14,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            controls,
            text="Сравнить (Heat Map)",
            command=self.compare_grayscale,
            width=18,
            bg="#0f3460",
            fg="white",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            controls,
            text="Демо-пиксели (putpixel)",
            command=self.create_pixel_demo,
            width=20,
        ).pack(side="left")

        self.status = tk.StringVar(
            value="Загрузите оригинал — готовый серый создаётся автоматически (PIL convert)."
        )
        tk.Label(self.root, textvariable=self.status, anchor="w", padx=16).pack(fill="x")

        preview = tk.Frame(self.root, padx=16, pady=8)
        preview.pack(fill="both", expand=True)

        self.labels: dict[str, tk.Label] = {}
        titles = [
            ("original", "Original"),
            ("diy_gray", "BlackWhite DIY (свой)"),
            ("ready_gray", "BlackWhite PIL (авто)"),
            ("heatmap", "Heat Map"),
        ]
        for idx, (key, title) in enumerate(titles):
            frame = tk.LabelFrame(preview, text=title, padx=6, pady=6)
            frame.grid(row=0, column=idx, sticky="nsew", padx=4, pady=4)
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            lbl = tk.Label(frame, text="—", bg="#222", anchor="center")
            lbl.grid(row=0, column=0, sticky="nsew")
            self.labels[key] = lbl
            lbl.bind("<Configure>", lambda e, k=key: self._on_preview_resize(k))

        for col in range(4):
            preview.grid_columnconfigure(col, weight=1)
        preview.grid_rowconfigure(0, weight=1)

        self.root.bind("<Configure>", self._refresh_all_previews)

        save_bar = tk.Frame(self.root, padx=16, pady=8)
        save_bar.pack(fill="x")
        tk.Button(save_bar, text="Сохранить Heat Map", command=self.save_heatmap).pack(
            side="left"
        )

    def load_original(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите оригинал (цветное изображение)",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("All", "*.*")],
        )
        if path:
            self.original = Image.open(path).convert("RGB")
            self.status.set(f"Оригинал: {path}")
            self._show_preview("original", self.original)
            self.compare_grayscale()

    @staticmethod
    def to_grayscale_ready(image: Image.Image) -> Image.Image:
        """Готовый серый — автоматически через Pillow (convert 'L')."""
        return image.convert("L")

    @staticmethod
    def to_grayscale_diy(image: Image.Image) -> Image.Image:
        """Свой алгоритм: среднее арифметическое каналов R, G, B."""
        rgb = np.array(image.convert("RGB"), dtype=np.float32)
        gray = (rgb[:, :, 0] + rgb[:, :, 1] + rgb[:, :, 2]) / 3.0
        return Image.fromarray(np.clip(gray, 0, 255).astype(np.uint8), mode="L")

    @staticmethod
    def diff_to_heatmap(diff: np.ndarray) -> Image.Image:
        """Тепловая карта: красный — мало различий, синий — много (как в примере)."""
        if diff.max() > 0:
            norm = diff / diff.max()
        else:
            norm = np.zeros_like(diff)

        red = ((1.0 - norm) * 255).astype(np.uint8)
        blue = (norm * 255).astype(np.uint8)
        green = (norm * 80).astype(np.uint8)
        rgb = np.stack([red, green, blue], axis=2)
        return Image.fromarray(rgb, mode="RGB")

    def compare_grayscale(self) -> None:
        if self.original is None:
            messagebox.showwarning("Внимание", "Загрузите оригинал.")
            return

        diy_gray = self.to_grayscale_diy(self.original)
        ready_gray = self.to_grayscale_ready(self.original)

        arr_diy = np.array(diy_gray, dtype=np.float32)
        arr_ready = np.array(ready_gray, dtype=np.float32)
        diff = np.abs(arr_diy - arr_ready)

        heatmap = self.diff_to_heatmap(diff)
        self.heatmap_result = heatmap

        self._show_preview("original", self.original)
        self._show_preview("diy_gray", diy_gray)
        self._show_preview("ready_gray", ready_gray)
        self._show_preview("heatmap", heatmap)

        mean_diff = float(diff.mean())
        max_diff = float(diff.max())
        self.status.set(
            f"DIY (среднее RGB) vs PIL convert('L'). "
            f"Средняя разность: {mean_diff:.2f}, максимум: {max_diff:.0f}"
        )

    def create_pixel_demo(self) -> None:
        """Демонстрация PIL: Image.new, getpixel, putpixel (по методичке)."""
        img = Image.new("RGB", (200, 200), 0x000000)
        pixels = [(10, 15), (11, 15), (10, 16), (11, 16)]
        for x, y in pixels:
            img.putpixel((x, y), (255, 0, 0))

        r = img.getpixel((10, 15))
        self._show_preview("original", img)
        self.status.set(f"Демо putpixel: getpixel(10,15) = {r}")

    @staticmethod
    def fit_image(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
        w, h = image.size
        if w < 1 or h < 1:
            return image.copy()
        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        if new_w == w and new_h == h:
            return image.copy()
        return image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def _on_preview_resize(self, key: str) -> None:
        if key in self.preview_sources:
            self._render_preview(key)

    def _refresh_all_previews(self, _event=None) -> None:
        for key in list(self.preview_sources.keys()):
            self._render_preview(key)

    def _render_preview(self, key: str) -> None:
        if key not in self.preview_sources:
            return

        lbl = self.labels[key]
        max_w = max(lbl.winfo_width() - 4, 220)
        max_h = max(lbl.winfo_height() - 4, 280)
        if max_w < 50 or max_h < 50:
            max_w, max_h = 260, 320

        fitted = self.fit_image(self.preview_sources[key], max_w, max_h)
        photo = ImageTk.PhotoImage(fitted)
        self.preview_refs.append(photo)
        if len(self.preview_refs) > 24:
            self.preview_refs = self.preview_refs[-12:]
        lbl.configure(image=photo, text="")

    def _show_preview(self, key: str, image: Image.Image) -> None:
        display = image
        if display.mode not in ("RGB", "L"):
            display = display.convert("RGB")
        self.preview_sources[key] = display.copy()
        self.root.after_idle(lambda k=key: self._render_preview(k))

    def save_heatmap(self) -> None:
        if self.heatmap_result is None:
            messagebox.showinfo("Сохранение", "Сначала выполните сравнение.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
            title="Сохранить тепловую карту",
        )
        if path:
            self.heatmap_result.save(path)
            self.status.set(f"Heat map сохранён: {path}")


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    ImageProcessingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
