import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ImageProcessingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🖼️ Обработка изображений с тепловыми картами")
        self.master.geometry("1200x720")
        self.master.configure(bg="#f8f9fa")

        self.original_image = None
        self.gray_image1 = None
        self.gray_image2 = None
        self.heatmap_figures = []

        # Стили
        self.button_style = {
            "bg": "#6c757d",
            "fg": "white",
            "activebackground": "#5a6268",
            "activeforeground": "white",
            "relief": tk.RAISED,
            "bd": 2,
            "font": ("Segoe UI", 10, "bold"),
            "padx": 10,
            "pady": 5,
        }

        # Главный контейнер с прокруткой
        self.main_frame = tk.Frame(master, bg="#f8f9fa")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg="#f8f9fa")
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.image_frame = tk.Frame(self.canvas, bg="#f8f9fa")
        self.canvas.create_window((0, 0), window=self.image_frame, anchor=tk.NW)

        # Панель управления
        self.control_frame = tk.Frame(master, bg="#f8f9fa")
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Кнопки и меню
        self.upload_btn = tk.Button(self.control_frame, text="📂 Загрузить", command=self.load_image, **self.button_style)
        self.upload_btn.pack(side=tk.LEFT, padx=5)

        self.cmap_label = tk.Label(self.control_frame, text="🎨 Цветовая схема:", bg="#f8f9fa", font=("Segoe UI", 10))
        self.cmap_label.pack(side=tk.LEFT, padx=5)

        self.cmap_var = tk.StringVar(value="coolwarm")
        self.cmap_choices = [
            "coolwarm", "viridis", "plasma", "inferno", "magma",
            "cividis", "seismic", "RdYlBu", "Spectral", "hot"
        ]
        self.cmap_menu = ttk.Combobox(
            self.control_frame,
            textvariable=self.cmap_var,
            values=self.cmap_choices,
            state="readonly",
            width=12,
            font=("Segoe UI", 10)
        )
        self.cmap_menu.pack(side=tk.LEFT, padx=5)

        self.process_btn = tk.Button(
            self.control_frame,
            text="🔥 Генерировать",
            command=self.process_image,
            **self.button_style
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        # Метки изображений внутри обрамляющих рамок
        self.image_labels = []
        for i in range(5):  # Исходник, серый 1, серый 2, тепловая карта, шкала
            frame = tk.Frame(self.image_frame, bg="#f8f9fa")
            frame.grid(row=0, column=i, padx=10, pady=5)
            label = tk.Label(frame, bg="white")
            label.pack()
            self.image_labels.append(label)

        self.image_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            try:
                self.original_image = Image.open(file_path)
                self.display_image(self.original_image, self.image_labels[0], "🖼️ Исходное изображение")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{e}")

    def process_image(self):
        if not self.original_image:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение!")
            return

        self.gray_image1 = self.original_image.convert("L")
        self.display_image(self.gray_image1, self.image_labels[1], "⚫ Серый 1")

        self.gray_image2 = ImageOps.invert(self.gray_image1)
        self.display_image(self.gray_image2, self.image_labels[2], "⚪ Серый 2")

        self.create_heatmap(self.cmap_var.get())

    def display_image(self, image, label, title=None):
        preview = image.copy()
        preview.thumbnail((280, 280))
        photo = ImageTk.PhotoImage(preview)
        label.config(image=photo)
        label.image = photo
        if title:
            label.config(text=title, compound='top', font=("Segoe UI", 9, "bold"))

    def create_heatmap(self, cmap_name):
        if not self.original_image:
            return

        img_array = np.array(self.original_image.convert("L"))
        fig_heatmap, ax_heatmap = plt.subplots(figsize=(3, 3))
        heatmap = ax_heatmap.imshow(img_array, cmap=cmap_name)
        ax_heatmap.axis('off')
        fig_heatmap.tight_layout()

        canvas_heatmap = FigureCanvasTkAgg(fig_heatmap, master=self.image_frame)
        canvas_heatmap.draw()

        buf_heatmap = canvas_heatmap.buffer_rgba()
        heatmap_img = Image.frombytes('RGBA', (buf_heatmap.shape[1], buf_heatmap.shape[0]), buf_heatmap).convert('RGB')

        self.display_image(heatmap_img, self.image_labels[3], f"🌡️ {cmap_name}")

        self.create_colorbar(img_array, cmap_name)

    def create_colorbar(self, img_array, cmap_name):
        fig_colorbar = plt.figure(figsize=(3, 0.5))
        ax_colorbar = fig_colorbar.add_axes([0.05, 0.5, 0.9, 0.15])

        norm = plt.Normalize(vmin=img_array.min(), vmax=img_array.max())
        sm = plt.cm.ScalarMappable(cmap=cmap_name, norm=norm)
        sm.set_array([])

        cbar = plt.colorbar(sm, cax=ax_colorbar, orientation='horizontal')
        cbar.set_label('Интенсивность')

        canvas_colorbar = FigureCanvasTkAgg(fig_colorbar, master=self.image_frame)
        canvas_colorbar.draw()

        buf_colorbar = canvas_colorbar.buffer_rgba()
        colorbar_img = Image.frombytes('RGBA', (buf_colorbar.shape[1], buf_colorbar.shape[0]), buf_colorbar).convert('RGB')

        self.display_image(colorbar_img, self.image_labels[4], "🎚️ Шкала")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.mainloop()
