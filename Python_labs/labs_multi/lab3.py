import sys

import pygame, cv2, numpy, time, os
from ffpyplayer.player import MediaPlayer
from tkinter import Tk, filedialog

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# ---------- выбор файла ----------------------------------------------------
def choose_file() -> str | None:
    Tk().withdraw()
    return filedialog.askopenfilename(
        title="Выберите видео",
        filetypes=[("Видео файлы", "*.mp4 *.avi *.mov *.mkv")]
    )


class Video:
    def __init__(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        self.cap = cv2.VideoCapture(path)
        # ff_opts обязательно именованным аргументом!
        self.ff  = MediaPlayer(path, ff_opts={"fast": True, "paused": True})

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.W   = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.H   = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.N   = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.surf = pygame.Surface((self.W, self.H))
        self.playing = self.paused = False
        self._start_t = 0
        self._drawn = 0
        self.muted  = False
        self._vol   = 1.0

    # ---- тайминг ----------------------------------------------------------
    def duration_ms(self) -> float: return self.N / self.fps * 1000
    def current_ms(self)  -> float: return self.cap.get(cv2.CAP_PROP_POS_MSEC)

    # ---- управление -------------------------------------------------------
    def play(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.ff.seek(0, relative=False)
        self.ff.set_pause(False)
        self.playing, self.paused = True, False
        self._start_t = time.time()
        self._drawn = 0

    def stop(self):
        self.playing = False
        self.ff.set_pause(True)

    def toggle_pause(self):
        self.paused = not self.paused
        self.ff.set_pause(self.paused)

    def toggle_mute(self):
        self.muted = not self.muted
        self.ff.set_volume(0 if self.muted else self._vol)

    # ---- получение кадра ---------------------------------------------------
    def frame(self) -> pygame.Surface:
        if not self.playing or self.paused:
            return self.surf

        need = int((time.time() - self._start_t) * self.fps) - self._drawn
        if need <= 0:
            return self.surf

        for _ in range(need):
            ok, fr = self.cap.read()
            if not ok:                  # конец файла
                self.stop()
                return self.surf

        self._drawn += need
        pygame.pixelcopy.array_to_surface(
            self.surf,
            numpy.flip(numpy.rot90(fr[::-1]))     # BGR → RGB + поворот
        )
        return self.surf


# ---------- главный цикл ----------------------------------------------------
def main():
    pygame.init()
    WIN_W, WIN_H = 1280, 720
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    def load_icon(name):
        surf = pygame.image.load(name).convert_alpha()  # теперь ok
        return pygame.transform.smoothscale(surf, (40, 40))
    icon_play = load_icon(resource_path("icons/play.png"))
    icon_pause = load_icon(resource_path("icons/pause.png"))
    icon_vol = load_icon(resource_path("icons/volume.png"))
    icon_mute = load_icon(resource_path("icons/volume_mute.png"))
    icon_stop = load_icon(resource_path("icons/stop.png"))

    icons = [icon_play, icon_pause, icon_vol, icon_mute, icon_stop]
    (icon_play, icon_pause, icon_vol, icon_mute, icon_stop) = icons

    f_text = pygame.font.SysFont(None, 26)

    while True:
        path = choose_file()
        if not path: break           # Cancel → выход

        video = Video(path)
        pygame.display.set_caption(os.path.basename(path))
        video.play()

        # Кнопки (позиции внизу окна)
        btn_y = WIN_H - 60
        play_btn = pygame.Rect(30,  btn_y, 40, 40)
        mute_btn = pygame.Rect(90,  btn_y, 40, 40)
        stop_btn = pygame.Rect(150, btn_y, 40, 40)

        running = True
        while running and video.playing:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); return
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if play_btn.collidepoint(e.pos):
                        video.toggle_pause()
                    elif mute_btn.collidepoint(e.pos):
                        video.toggle_mute()
                    elif stop_btn.collidepoint(e.pos):
                        running = False
                        video.stop()

            screen.fill("black")

            frame = video.frame()
            scale = min(WIN_W / video.W, WIN_H / video.H, 1)
            new_w, new_h = int(video.W * scale), int(video.H * scale)
            offs_x = (WIN_W - new_w) // 2
            offs_y = (WIN_H - new_h) // 2
            screen.blit(pygame.transform.scale(frame, (new_w, new_h)), (offs_x, offs_y))

            # ---- полупрозрачная панель ----
            overlay = pygame.Surface((WIN_W, 70), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, WIN_H - 70))

            # ---- кнопки ----
            screen.blit(icon_pause if not video.paused else icon_play, play_btn.topleft)
            screen.blit(icon_mute  if video.muted   else icon_vol,  mute_btn.topleft)
            pygame.draw.rect(screen, (200, 0, 0), stop_btn, border_radius=5)
            screen.blit(icon_stop, stop_btn.move(11, 0).topleft)

            # ---- таймер ----
            cur = int(video.current_ms() // 1000)
            dur = int(video.duration_ms() // 1000)
            ttxt = f"{cur//60}:{cur%60:02d} / {dur//60}:{dur%60:02d}"
            screen.blit(f_text.render(ttxt, True, "white"), (WIN_W - 170, WIN_H - 50))

            pygame.display.flip()
            clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
