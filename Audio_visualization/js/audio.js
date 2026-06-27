let song;
let fft;
let fftEq;
let w;

const audioFiles = ['music/muz1.mp3', 'music/muz2.mp3', 'music/muz3.mp3'];
const trackNames = ['Hungarian Dance No. 5', 'The Nutcracker', 'Primavera'];
let currentTrackIndex = 0;
let isPlaying = false;
let intervalId;

function preload() {
  song = loadSound(audioFiles[currentTrackIndex]);
}

function setup() {
  // Создаем пустой канвас, так как визуализация идёт через SVG
  createCanvas(0, 0);
  fft = new p5.FFT(0.9, 64);
  fftEq = new p5.FFT(0.9, 32);

  fft.setInput(song);
  fftEq.setInput(song);

  w = 400 / 32;

  createSquareGrid();
  createRings();


  // Устанавливаем автоматическую смену изображений
  setAutoSwitch();
}

function draw() {
  let spectrum = fft.analyze();
  let spectrumEq = fftEq.analyze();

  updateSquareGrid(spectrum);
  updateRings(spectrumEq);

  // Обновляем прогресс-бар
  const progressBar = document.getElementById('progress-bar');
  if (song.duration() > 0 && !progressBar.dragging) {
    progressBar.value = (song.currentTime() / song.duration()) * 100;
  }
}

function createRings() {
  const svg = document.getElementById("equalizerCanvas");
  svg.innerHTML = "";
  for (let i = 0; i < 32; i++) {
    const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    ring.setAttribute("cx", 200);
    ring.setAttribute("cy", 200);
    ring.setAttribute("r", 10);
    ring.setAttribute("fill", "none");
    ring.setAttribute("stroke", "#D0BCFF");
    ring.setAttribute("stroke-width", "2");
    svg.appendChild(ring);
  }
}

function updateRings(spectrum) {
  const svg = document.getElementById("equalizerCanvas");
  const rings = svg.querySelectorAll("circle");

  for (let i = 0; i < rings.length; i++) {
    const amp = spectrum[i];
    const radius = map(amp, 0, 255, 10, 150);
    rings[i].setAttribute("r", radius);
    rings[i].setAttribute("stroke", `hsl(${i * 10}, 70%, ${amp / 3 + 30}%)`);
  }
}

function createSquareGrid() {
  const svg = document.getElementById("visualizer");
  svg.innerHTML = "";
  const gridSize = 8;
  const squareSize = 20;
  const gap = 8;
  const totalSize = gridSize * (squareSize + gap);
  const centerX = 200;
  const centerY = 200;

  for (let i = 0; i < 64; i++) {
    const col = i % gridSize;
    const row = Math.floor(i / gridSize);

    // Центрируем сетку
    const baseX = col * (squareSize + gap) - totalSize / 2 + centerX;
    const baseY = row * (squareSize + gap) - totalSize / 2 + centerY;

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", baseX);
    rect.setAttribute("y", baseY);
    rect.setAttribute("width", squareSize);
    rect.setAttribute("height", squareSize);
    rect.setAttribute("fill", "#D0BCFF");
    rect.setAttribute("data-x", baseX);
    rect.setAttribute("data-y", baseY);
    rect.setAttribute("data-index", i);
    svg.appendChild(rect);
  }
}

function updateSquareGrid(spectrum) {
  const svg = document.getElementById("visualizer");
  const rects = svg.querySelectorAll("rect");
  const centerX = 200;
  const centerY = 200;

  for (let i = 0; i < rects.length; i++) {
    const rect = rects[i];
    const amp = spectrum[i];
    const baseX = parseFloat(rect.getAttribute("data-x"));
    const baseY = parseFloat(rect.getAttribute("data-y"));

    const dx = baseX - centerX;
    const dy = baseY - centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const normX = dx / (distance || 1);
    const normY = dy / (distance || 1);

    const spread = map(amp, 0, 255, 0, 40);

    const newX = baseX + normX * spread;
    const newY = baseY + normY * spread;

    rect.setAttribute("x", newX);
    rect.setAttribute("y", newY);

    // Меняем цвет от амплитуды
    let color;
    if (amp < 30) color = "#d0bcff";
    else if (amp < 60) color = "#c792ea";
    else if (amp < 120) color = "#bb86fc";
    else color = "#9f5cff";
    rect.setAttribute("fill", color);
  }
}

// ------------------- Управление аудио и плеером -------------------

function togglePlayPause() {
  if (isPlaying) {
    song.pause();
    document.getElementById('play-pause-icon').src = 'icons/play.png';
  } else {
    song.play();
    document.getElementById('play-pause-icon').src = 'icons/pause.png';
  }
  isPlaying = !isPlaying;
}

// Обновление позиции аудио через прогресс-бар
const progressBar = document.getElementById('progress-bar');
progressBar.addEventListener('mousedown', () => {
  progressBar.dragging = true;
});
progressBar.addEventListener('mouseup', () => {
  progressBar.dragging = false;
  changeAudioPosition();
});
progressBar.addEventListener('input', () => {
  if (progressBar.dragging && song.duration()) {
    song.jump((progressBar.value / 100) * song.duration());
  }
});

function changeAudioPosition() {
  if (song.duration()) {
    song.jump((progressBar.value / 100) * song.duration());
  }
}

// Переключение треков
function changeTrack(newIndex) {
  currentTrackIndex = (newIndex + audioFiles.length) % audioFiles.length;
  song.stop();
  loadSound(audioFiles[currentTrackIndex], (loadedSound) => {
    song = loadedSound;
    fft.setInput(song);
    fftEq.setInput(song);
    document.getElementById('audio-filename').textContent = trackNames[currentTrackIndex];
    song.play();
    isPlaying = true;
    document.getElementById('play-pause-icon').src = 'icons/pause.png';
  });
}

function nextTrack() {
  changeTrack(currentTrackIndex + 1);
}

function previousTrack() {
  changeTrack(currentTrackIndex - 1);
}

// Загрузка нового аудиофайла
function uploadAudio(event) {
  const file = event.target.files[0];
  if (file) {
    document.getElementById('audio-filename').textContent = file.name;
    song.stop();
    loadSound(URL.createObjectURL(file), (loadedSound) => {
      song = loadedSound;
      fft.setInput(song);
      fftEq.setInput(song);
      song.play();
      isPlaying = true;
      document.getElementById('play-pause-icon').src = 'icons/pause.png';
    });
  }
}