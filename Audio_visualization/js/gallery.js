// gallery.js

const images = [
    { src: "img/image1.jpg", comment: "Дом" },
    { src: "img/image2.jpg", comment: "Пейзаж" },
    { src: "img/image3.jpg", comment: "Цветок" },
  ];
  
  let currentIndex = 0;
  let intervalId;
  let isSwitching = true;
  
  function updateImage() {
    const imageElement = document.getElementById("current-image");
    const commentElement = document.getElementById("image-comment");
  
    // Плавное исчезновение
    imageElement.style.opacity = 0;
  
    setTimeout(() => {
      imageElement.src = images[currentIndex].src;
      commentElement.textContent = images[currentIndex].comment;
  
      // Дожидаемся загрузки нового изображения для плавного появления
      imageElement.onload = () => {
        imageElement.style.opacity = 1;
      };
    }, 500);
  }
  
  function nextImage() {
    currentIndex = (currentIndex + 1) % images.length;
    updateImage();
  }
  
  function prevImage() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    updateImage();
  }
  
  function toggleImageSwitching() {
    if (isSwitching) {
      stopAutoSwitch();
      document.getElementById("switch-button-text").textContent = "Запустить";
    } else {
      setAutoSwitch();
      document.getElementById("switch-button-text").textContent = "Остановить";
    }
    isSwitching = !isSwitching;
  }
  
  function setAutoSwitch() {
    clearInterval(intervalId);
    const timing = document.getElementById("timing").value * 1000;
    intervalId = setInterval(nextImage, timing);
  }
  
  function stopAutoSwitch() {
    clearInterval(intervalId);
  }
  