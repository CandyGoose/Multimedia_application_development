(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const CENTER_X = 200;
  const CENTER_Y = 130;
  const SHELL_COUNT = 72;
  const RING_COUNT = 6;

  const slides = Array.from(document.querySelectorAll(".slide"));
  const totalSlides = slides.length;
  const slideCounter = document.getElementById("slideCounter");
  const dotsNav = document.getElementById("dotsNav");
  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");
  const btnAuto = document.getElementById("btnAuto");
  const timingRange = document.getElementById("timingRange");
  const timingValue = document.getElementById("timingValue");

  const audioEl = document.getElementById("my_audio");
  const soundEnabled = document.getElementById("soundEnabled");
  const trackRadios = document.querySelectorAll('input[name="track"]');
  const audioUpload = document.getElementById("audioUpload");
  const btnPlayPause = document.getElementById("btnPlayPause");
  const trackNameEl = document.getElementById("trackName");
  const audioHint = document.getElementById("audioHint");

  const vizShell = document.getElementById("vizShell");
  const vizOrbs = document.getElementById("vizOrbs");
  const vizRings = document.getElementById("vizRings");
  const vizSpiralPath = document.getElementById("vizSpiralPath");
  const vizCore = document.getElementById("vizCore");

  const TRACK_LABELS = {
    "audio/ambient-flow.wav": "Ambient Flow",
    "audio/digital-pulse.wav": "Digital Pulse",
    "audio/cosmic-arpeggio.wav": "Cosmic Arpeggio"
  };

  const ORB_SLOTS = [
    { cx: 42, cy: 42, grad: "orbGradA", bandStart: 0, bandEnd: 8 },
    { cx: 358, cy: 48, grad: "orbGradB", bandStart: 8, bandEnd: 20 },
    { cx: 362, cy: 218, grad: "orbGradC", bandStart: 20, bandEnd: 40 },
    { cx: 38, cy: 212, grad: "orbGradA", bandStart: 40, bandEnd: 60 },
    { cx: 200, cy: 22, grad: "orbGradB", bandStart: 60, bandEnd: 90 },
    { cx: 200, cy: 248, grad: "orbGradC", bandStart: 90, bandEnd: 120 },
    { cx: 88, cy: 130, grad: "orbGradA", bandStart: 0, bandEnd: 32 },
    { cx: 312, cy: 130, grad: "orbGradB", bandStart: 32, bandEnd: 64 }
  ];

  let currentIndex = 0;
  let autoEnabled = true;
  let autoTimer = null;

  let audioContext = null;
  let analyser = null;
  let sourceNode = null;
  let audioGraphReady = false;
  let vizFrameId = null;
  let frequencyData = null;
  let timeData = null;
  let customTrackUrl = null;
  let shellDots = [];
  let orbCircles = [];
  let ringCircles = [];
  let shellPositions = [];

  function showHint(message, isError) {
    if (!message) {
      audioHint.textContent = "";
      audioHint.classList.remove("is-error");
      return;
    }
    audioHint.textContent = message;
    audioHint.classList.toggle("is-error", !!isError);
  }

  function updatePlayButton(isPlaying) {
    btnPlayPause.textContent = isPlaying ? "Пауза" : "Воспроизвести";
  }

  function initDots() {
    slides.forEach(function (_, i) {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "dot" + (i === 0 ? " active" : "");
      dot.setAttribute("role", "tab");
      dot.setAttribute("aria-label", "Слайд " + (i + 1));
      dot.addEventListener("click", function () {
        goToSlide(i, true);
      });
      dotsNav.appendChild(dot);
    });
  }

  function updateSlideView() {
    slides.forEach(function (slide, i) {
      slide.classList.toggle("active", i === currentIndex);
    });
    dotsNav.querySelectorAll(".dot").forEach(function (dot, i) {
      dot.classList.toggle("active", i === currentIndex);
    });
    slideCounter.textContent = (currentIndex + 1) + " / " + totalSlides;
  }

  function goToSlide(index, fromUser) {
    currentIndex = (index + totalSlides) % totalSlides;
    updateSlideView();
    if (fromUser) {
      resetAutoTimer();
    }
  }

  function nextSlide(fromUser) {
    goToSlide(currentIndex + 1, fromUser);
  }

  function prevSlide(fromUser) {
    goToSlide(currentIndex - 1, fromUser);
  }

  function getTimingMs() {
    return parseInt(timingRange.value, 10) * 1000;
  }

  function resetAutoTimer() {
    if (autoTimer) {
      clearInterval(autoTimer);
      autoTimer = null;
    }
    if (autoEnabled) {
      autoTimer = setInterval(function () {
        nextSlide(false);
      }, getTimingMs());
    }
  }

  function setAutoMode(enabled) {
    autoEnabled = enabled;
    btnAuto.setAttribute("aria-pressed", String(enabled));
    btnAuto.textContent = enabled ? "Авто: вкл" : "Авто: выкл";
    resetAutoTimer();
  }

  function computeShellPositions() {
    shellPositions = [];
    for (let i = 0; i < SHELL_COUNT; i++) {
      const angle = i * 0.42;
      const radius = 6 + i * 1.65;
      shellPositions.push({
        x: CENTER_X + Math.cos(angle) * radius,
        y: CENTER_Y + Math.sin(angle) * radius
      });
    }
  }

  function buildVisualization() {
    computeShellPositions();

    vizRings.innerHTML = "";
    ringCircles = [];
    for (let i = 0; i < RING_COUNT; i++) {
      const ring = document.createElementNS(SVG_NS, "circle");
      ring.setAttribute("cx", String(CENTER_X));
      ring.setAttribute("cy", String(CENTER_Y));
      ring.setAttribute("r", String(18 + i * 16));
      ring.setAttribute("fill", "none");
      ring.setAttribute("stroke", i % 2 === 0 ? "#00f5a0" : "#00d9f5");
      ring.setAttribute("stroke-width", "1");
      vizRings.appendChild(ring);
      ringCircles.push(ring);
    }

    vizShell.innerHTML = "";
    shellDots = [];
    shellPositions.forEach(function (pos, i) {
      const dot = document.createElementNS(SVG_NS, "circle");
      dot.setAttribute("cx", String(pos.x));
      dot.setAttribute("cy", String(pos.y));
      dot.setAttribute("r", "3");
      dot.setAttribute("fill", "url(#shellGrad)");
      dot.setAttribute("opacity", "0.85");
      vizShell.appendChild(dot);
      shellDots.push(dot);
    });

    vizOrbs.innerHTML = "";
    orbCircles = [];
    ORB_SLOTS.forEach(function (slot) {
      const orb = document.createElementNS(SVG_NS, "circle");
      orb.setAttribute("cx", String(slot.cx));
      orb.setAttribute("cy", String(slot.cy));
      orb.setAttribute("r", "6");
      orb.setAttribute("fill", "url(#" + slot.grad + ")");
      orb.setAttribute("opacity", "0.7");
      vizOrbs.appendChild(orb);
      orbCircles.push({ el: orb, slot: slot });
    });
  }

  function bandAverage(data, start, end) {
    let sum = 0;
    let count = 0;
    for (let i = start; i < end && i < data.length; i++) {
      sum += data[i];
      count++;
    }
    return count ? sum / count : 0;
  }

  function resetAudioGraph() {
    /* MediaElementSource создаётся один раз — при смене трека граф не сбрасываем */
  }

  function initAnalyserContext() {
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (!analyser) {
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.78;
      frequencyData = new Uint8Array(analyser.frequencyBinCount);
      timeData = new Uint8Array(analyser.fftSize);
    }
  }

  function setupMediaElementGraph() {
    if (audioGraphReady) {
      return true;
    }

    initAnalyserContext();

    try {
      sourceNode = audioContext.createMediaElementSource(audioEl);
      sourceNode.connect(analyser);
      analyser.connect(audioContext.destination);
      audioGraphReady = true;
      return true;
    } catch (err) {
      if (err.name === "InvalidStateError") {
        audioGraphReady = true;
        return true;
      }
      return false;
    }
  }

  async function prepareAudioEngine() {
    applyMuteState();
    audioEl.volume = 1;
    const graphOk = setupMediaElementGraph();
    await ensureAudioContextRunning();
    return graphOk;
  }

  async function onAudioPlay() {
    if (!soundEnabled.checked) {
      audioEl.pause();
      return;
    }

    const graphOk = await prepareAudioEngine();
    updatePlayButton(true);

    if (graphOk) {
      startVisualization();
      showHint("");
    } else {
      showHint(
        "Web Audio не инициализирован. Откройте Chrome с флагом --disable-web-security для локального теста (см. методичку).",
        true
      );
    }
  }

  function onAudioPause() {
    updatePlayButton(false);
    stopVisualization();
  }

  async function ensureAudioContextRunning() {
    if (!audioContext) {
      return;
    }
    if (audioContext.state === "suspended") {
      await audioContext.resume();
    }
  }

  function startVisualization() {
    if (!analyser || !frequencyData) {
      return;
    }

    function draw() {
      analyser.getByteFrequencyData(frequencyData);
      analyser.getByteTimeDomainData(timeData);

      let bass = 0;
      let mid = 0;
      let treble = 0;
      const len = frequencyData.length;

      for (let i = 0; i < len; i++) {
        if (i < len * 0.15) {
          bass += frequencyData[i];
        } else if (i < len * 0.5) {
          mid += frequencyData[i];
        } else {
          treble += frequencyData[i];
        }
      }
      bass /= len * 0.15;
      mid /= len * 0.35;
      treble /= len * 0.5;

      const spiralPoints = [];
      shellDots.forEach(function (dot, i) {
        const bin = Math.floor((i / SHELL_COUNT) * len);
        const value = frequencyData[bin];
        const base = shellPositions[i];
        const pulse = (value / 255) * 14;
        const wobble = Math.sin(Date.now() * 0.004 + i * 0.3) * (mid / 255) * 4;

        dot.setAttribute("r", String(2 + pulse));
        dot.setAttribute("cx", String(base.x + wobble));
        dot.setAttribute("cy", String(base.y + wobble * 0.6));
        dot.setAttribute("opacity", String(0.35 + value / 255 * 0.65));
        spiralPoints.push((base.x + wobble) + "," + (base.y + wobble * 0.6));
      });

      vizSpiralPath.setAttribute("d", "M" + spiralPoints.join(" L"));

      ringCircles.forEach(function (ring, i) {
        const scale = 1 + (bass / 255) * (0.15 + i * 0.08);
        ring.setAttribute("r", String((18 + i * 16) * scale));
        ring.setAttribute("opacity", String(0.15 + (mid / 255) * 0.35));
      });

      orbCircles.forEach(function (item) {
        const avg = bandAverage(
          frequencyData,
          item.slot.bandStart,
          item.slot.bandEnd
        );
        const drift = Math.sin(Date.now() * 0.003 + item.slot.cx) * (avg / 255) * 6;
        const r = 5 + (avg / 255) * 22;
        item.el.setAttribute("r", String(r));
        item.el.setAttribute("cx", String(item.slot.cx + drift));
        item.el.setAttribute("cy", String(item.slot.cy - drift * 0.7));
        item.el.setAttribute("opacity", String(0.4 + avg / 255 * 0.6));
      });

      const coreR = 6 + (bass / 255) * 18;
      vizCore.setAttribute("r", String(coreR));
      vizCore.setAttribute(
        "opacity",
        String(0.55 + Math.min(1, (bass + treble) / 400))
      );

      vizFrameId = requestAnimationFrame(draw);
    }

    if (vizFrameId) {
      cancelAnimationFrame(vizFrameId);
    }
    draw();
  }

  function stopVisualization() {
    if (vizFrameId) {
      cancelAnimationFrame(vizFrameId);
      vizFrameId = null;
    }

    shellDots.forEach(function (dot, i) {
      dot.setAttribute("cx", String(shellPositions[i].x));
      dot.setAttribute("cy", String(shellPositions[i].y));
      dot.setAttribute("r", "3");
      dot.setAttribute("opacity", "0.5");
    });

    ringCircles.forEach(function (ring, i) {
      ring.setAttribute("r", String(18 + i * 16));
      ring.setAttribute("opacity", "0.25");
    });

    orbCircles.forEach(function (item) {
      item.el.setAttribute("cx", String(item.slot.cx));
      item.el.setAttribute("cy", String(item.slot.cy));
      item.el.setAttribute("r", "6");
      item.el.setAttribute("opacity", "0.5");
    });

    vizSpiralPath.setAttribute("d", "");
    vizCore.setAttribute("r", "8");
    vizCore.setAttribute("opacity", "0.7");
  }

  function applyMuteState() {
    audioEl.muted = !soundEnabled.checked;
  }

  function resolveTrackSrc(value) {
    if (/^(blob:|https?:|data:)/.test(value)) {
      return value;
    }
    try {
      return new URL(value, window.location.href).href;
    } catch (_e) {
      return value;
    }
  }

  function ensureAudioSrc() {
    if (audioEl.src) {
      return;
    }
    const checked = document.querySelector('input[name="track"]:checked');
    if (checked) {
      audioEl.src = resolveTrackSrc(checked.value);
      audioEl.loop = true;
      audioEl.load();
    }
  }

  async function startPlayback() {
    if (!soundEnabled.checked) {
      showHint("Включите переключатель «Звук включён».", true);
      return;
    }
    ensureAudioSrc();
    try {
      await audioEl.play();
    } catch (err) {
      updatePlayButton(false);
      showHint("Ошибка: " + (err.message || "повторите попытку"), true);
    }
  }

  function loadTrack(src, label) {
    const wasPlaying = !audioEl.paused;
    audioEl.pause();
    audioEl.src = resolveTrackSrc(src);
    audioEl.loop = true;
    audioEl.load();
    trackNameEl.textContent = label;
    applyMuteState();
    showHint("");
    if (wasPlaying && soundEnabled.checked) {
      startPlayback();
    }
  }

  function togglePlayback() {
    if (audioEl.paused) {
      startPlayback();
    } else {
      audioEl.pause();
    }
  }

  btnPrev.addEventListener("click", function () {
    prevSlide(true);
  });

  btnNext.addEventListener("click", function () {
    nextSlide(true);
  });

  btnAuto.addEventListener("click", function () {
    setAutoMode(!autoEnabled);
  });

  timingRange.addEventListener("input", function () {
    timingValue.textContent = timingRange.value;
    resetAutoTimer();
  });

  soundEnabled.addEventListener("change", function () {
    applyMuteState();
    if (!soundEnabled.checked) {
      audioEl.pause();
      showHint("");
    }
  });

  trackRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      if (radio.checked) {
        if (customTrackUrl) {
          URL.revokeObjectURL(customTrackUrl);
          customTrackUrl = null;
        }
        audioUpload.value = "";
        loadTrack(radio.value, TRACK_LABELS[radio.value]);
      }
    });
  });

  audioUpload.addEventListener("change", function () {
    const file = audioUpload.files[0];
    if (!file) {
      return;
    }
    if (customTrackUrl) {
      URL.revokeObjectURL(customTrackUrl);
    }
    customTrackUrl = URL.createObjectURL(file);
    trackRadios.forEach(function (r) {
      r.checked = false;
    });
    loadTrack(customTrackUrl, file.name);
  });

  btnPlayPause.addEventListener("click", togglePlayback);

  audioEl.addEventListener("play", onAudioPlay);
  audioEl.addEventListener("pause", onAudioPause);

  audioEl.addEventListener("ended", function () {
    if (audioEl.loop) {
      return;
    }
    onAudioPause();
  });

  audioEl.addEventListener("error", function () {
    showHint("Не удалось загрузить аудиофайл. Проверьте папку audio/.", true);
    updatePlayButton(false);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") {
      prevSlide(true);
    } else if (e.key === "ArrowRight") {
      nextSlide(true);
    } else if (e.key === " ") {
      e.preventDefault();
      togglePlayback();
    }
  });

  buildVisualization();
  initDots();
  updateSlideView();
  resetAutoTimer();

  const defaultTrack = document.querySelector('input[name="track"]:checked');
  if (defaultTrack) {
    audioEl.src = resolveTrackSrc(defaultTrack.value);
    trackNameEl.textContent = TRACK_LABELS[defaultTrack.value];
  }
  audioEl.loop = true;
  audioEl.volume = 1;
  applyMuteState();

  var obj_Audio = document.getElementById("my_audio");
  window.obj_Audio = obj_Audio;
  // obj_Audio = new Audio("audio/ambient-flow.wav");
})();
