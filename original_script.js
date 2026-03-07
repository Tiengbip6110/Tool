const heartsContainer = document.body;
const imageFiles = Array.from(
  { length: 20 },
  (_, i) => `style/img/Anh (${i + 1}).jpg`,
);

let letterText = [];

async function loadLetter() {
  try {
    const response = await fetch("style/letter.txt");
    const text = await response.text();
    letterText = text
      .split(/\n\s*\n/)
      .map((p) => p.trim())
      .filter((p) => p !== "");
  } catch (error) {
    console.error("Error loading letter.txt:", error);
    letterText = ["Mãi yêu em ❤️"];
  }
}

loadLetter();

const songs = [
  {
    title: "In Love x Có Đôi Điều",
    cover: "style/sound/Anh (1).jpg",
    src: "style/sound/In Love x Có Đôi Điều.mp3",
  },
  {
    title: "Ai Ngoài Anh",
    cover: "style/sound/Anh (2).jpg",
    src: "style/sound/Ai Ngoài Anh.mp3",
  },
  {
    title: "Track 06 x Nơi Này Có Anh",
    cover: "style/sound/Anh (3).jpg",
    src: "style/sound/Track 06 x Nơi Này Có Anh.mp3",
  },
  {
    title: "Lỡ Say Bye Là Bye",
    cover: "style/sound/Anh (4).jpg",
    src: "style/sound/Lỡ Say Bye Là Bye.mp3",
  },
  {
    title: "MISSING YOU",
    cover: "style/sound/Anh (5).jpg",
    src: "style/sound/MISSING YOU.mp3",
  },
  {
    title: "Anh Là Ai ?",
    cover: "style/sound/Anh (6).jpg",
    src: "style/sound/Anh là ai.mp3",
  },
];

function createHeart() {
  const heart = document.createElement("div");
  heart.classList.add("heart");

  const icons = ["❤", "💖", "💗", "💓", "💕", "🌸"];
  const gifs = [
    "https://i.pinimg.com/originals/88/23/82/882382f97862c72e60fc06822e36eb55.gif",
    "https://i.pinimg.com/originals/b9/67/4f/b9674f3f995aba177250894d57f42bbf.gif",
    "https://i.pinimg.com/originals/4e/89/d3/4e89d3e4ec4b1f59b1664e880a875c65.gif",
    "https://i.pinimg.com/originals/b6/6b/1b/b66b1bfe70a9ad4f69dea3b620011222.gif",
  ];

  const isGif = Math.random() > 0.5;

  if (isGif) {
    const img = document.createElement("img");
    img.src = gifs[Math.floor(Math.random() * gifs.length)];
    const gifSize = Math.random() * 30 + 30;
    img.style.width = `${gifSize}px`;
    img.style.height = "auto";
    heart.appendChild(img);
  } else {
    heart.innerText = icons[Math.floor(Math.random() * icons.length)];
    const size = Math.random() * 20 + 10;
    heart.style.fontSize = `${size}px`;
  }

  const left = Math.random() * 100;
  const duration = Math.random() * 3 + 3;
  const opacity = Math.random() * 0.5 + 0.5;

  heart.style.left = `${left}%`;
  heart.style.animationDuration = `${duration}s`;
  heart.style.opacity = opacity;
  heartsContainer.appendChild(heart);

  setTimeout(() => {
    heart.remove();
  }, duration * 1000);
}

for (let i = 0; i < 10; i++) {
  setTimeout(createHeart, Math.random() * 3000);
}

setInterval(createHeart, 400);

const btnLetter = document.getElementById("btn-letter");
const letterOverlay = document.getElementById("letter-overlay");
const closeLetter = document.getElementById("close-letter");
const letterBody = document.getElementById("letter-body");

let typingInterval;
let paragraphIndex = 0;
let charIndex = 0;
let isTyping = false;

function typeWriter() {
  if (paragraphIndex < letterText.length) {
    isTyping = true;
    let p = letterBody.lastElementChild;
    if (!p || charIndex === 0) {
      p = document.createElement("p");
      if (paragraphIndex === letterText.length - 1) {
        p.classList.add("letter-footer");
      }
      letterBody.appendChild(p);
    }

    p.textContent += letterText[paragraphIndex][charIndex];
    charIndex++;
    letterBody.scrollTop = letterBody.scrollHeight;

    if (charIndex < letterText[paragraphIndex].length) {
      typingInterval = setTimeout(typeWriter, 30);
    } else {
      paragraphIndex++;
      charIndex = 0;
      typingInterval = setTimeout(typeWriter, 500);
    }
  } else {
    isTyping = false;
  }
}

btnLetter.addEventListener("click", () => {
  letterOverlay.classList.add("active");

  if (!isTyping && paragraphIndex < letterText.length) {
    setTimeout(typeWriter, 500);
  }
});

closeLetter.addEventListener("click", () => {
  letterOverlay.classList.remove("active");
  clearTimeout(typingInterval);
  isTyping = false;
});

const btnMusic = document.getElementById("btn-music");
const musicOverlay = document.getElementById("music-overlay");
const closeMusic = document.getElementById("close-music");
const audioPlayer = document.getElementById("audio-player");
const playPauseBtn = document.getElementById("play-pause-btn");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const progressBar = document.getElementById("progress-bar");
const progress = document.getElementById("progress");
const currentTimeEl = document.getElementById("current-time");
const durationEl = document.getElementById("duration");
const songTitle = document.getElementById("song-title");
const songArtist = document.getElementById("song-artist");
const albumArt = document.querySelector("#album-art img");
const songListContainer = document.getElementById("song-list");

let songIndex = 0;
let isPlaying = false;

function loadSong(song) {
  songTitle.innerText = song.title;
  songArtist.style.display = "none";
  albumArt.src = song.cover;
  audioPlayer.src = song.src;
  updateSongListUI();
}

function updateSongListUI() {
  const items = document.querySelectorAll(".song-item");
  items.forEach((item, index) => {
    if (index === songIndex) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

function playSong() {
  const playPromise = audioPlayer.play();

  if (playPromise !== undefined) {
    playPromise.then(() => {
      isPlaying = true;
      playPauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
      musicStarted = true;
      console.log("Bản quyền thuộc về Dr.Gifter");
      console.log("Tiktok: https://www.tiktok.com/@dr.gifter306");
      console.log("Github: https://github.com/DrGifter");
    }).catch(error => {
      console.log("Phát nhạc bị chặn hoặc lỗi, đang đợi tương tác tiếp theo...");
      isPlaying = false;
      playPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
      musicStarted = false;
    });
  }
}

function pauseSong() {
  isPlaying = false;
  playPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
  audioPlayer.pause();
}

function prevSong() {
  songIndex--;
  if (songIndex < 0) songIndex = songs.length - 1;
  loadSong(songs[songIndex]);
  playSong();
}

function nextSong() {
  songIndex++;
  if (songIndex > songs.length - 1) songIndex = 0;
  loadSong(songs[songIndex]);
  playSong();
}

function updateProgress(e) {
  const { duration, currentTime } = e.srcElement;
  if (isNaN(duration)) return;
  const progressPercent = (currentTime / duration) * 100;
  progress.style.width = `${progressPercent}%`;
  currentTimeEl.innerText = formatTime(currentTime);
  durationEl.innerText = formatTime(duration);
}

function formatTime(seconds) {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${min}:${sec < 10 ? "0" : ""}${sec}`;
}

function setProgress(e) {
  const width = this.clientWidth;
  const clickX = e.offsetX;
  const duration = audioPlayer.duration;
  audioPlayer.currentTime = (clickX / width) * duration;
}

// Populate Song List
songs.forEach((song, index) => {
  const item = document.createElement("div");
  item.classList.add("song-item");
  item.innerHTML = `
    <img src="${song.cover}" alt="${song.title}">
    <div class="song-item-info">
      <div class="song-item-title">${song.title}</div>
    </div>
  `;
  item.addEventListener("click", () => {
    songIndex = index;
    loadSong(songs[songIndex]);
    playSong();
  });
  songListContainer.appendChild(item);
});

const btnImage = document.getElementById("btn-image");
const imageOverlay = document.getElementById("image-overlay");
const closeImage = document.getElementById("close-image");
const galleryTop = document.getElementById("gallery-top");
const galleryBottom = document.getElementById("gallery-bottom");
const lightboxOverlay = document.getElementById("lightbox-overlay");
const lightboxImg = document.getElementById("lightbox-img");
const closeLightbox = document.getElementById("close-lightbox");

function populateGallery() {
  galleryTop.innerHTML = "";
  galleryBottom.innerHTML = "";

  const topImages = imageFiles.slice(0, 9);
  const bottomImages = imageFiles.slice(9);

  const createImg = (src) => {
    const img = document.createElement("img");
    img.src = src;
    img.loading = "lazy";
    img.addEventListener("click", (e) => {
      e.stopPropagation();
      openLightbox(src);
    });
    return img;
  };

  [...topImages, ...topImages].forEach((src) =>
    galleryTop.appendChild(createImg(src)),
  );
  [...bottomImages, ...bottomImages].forEach((src) =>
    galleryBottom.appendChild(createImg(src)),
  );
}

function openLightbox(src) {
  lightboxImg.src = src;
  lightboxOverlay.classList.add("active");
}

closeLightbox.addEventListener("click", () => {
  lightboxOverlay.classList.remove("active");
});

lightboxOverlay.addEventListener("click", (e) => {
  if (e.target === lightboxOverlay) lightboxOverlay.classList.remove("active");
});

function makeDraggable(element) {
  let isDown = false;
  let startX;
  let scrollLeft;

  element.addEventListener("mousedown", (e) => {
    isDown = true;
    element.style.cursor = "grabbing";
    element.querySelector(".gallery-row").style.animationPlayState = "paused";
  });

  window.addEventListener("mouseup", () => {
    isDown = false;
    element.style.cursor = "grab";
    const row = element.querySelector(".gallery-row");
    if (row) row.style.animationPlayState = "running";
  });

  element.addEventListener("mouseleave", () => {
    isDown = false;
    const row = element.querySelector(".gallery-row");
    if (row) row.style.animationPlayState = "running";
  });
}

btnImage.addEventListener("click", () => {
  populateGallery();
  imageOverlay.classList.add("active");
});

const btnGift = document.getElementById("btn-gift");
const giftOverlay = document.getElementById("gift-overlay");
const closeGift = document.getElementById("close-gift");
const fullscreenGiftBtn = document.getElementById("fullscreen-gift");
const giftModalElement = document.getElementById("gift-modal-element");

const giftIframe = document.querySelector(".gift-iframe");

btnGift.addEventListener("click", () => {
  if (giftIframe) {
    giftIframe.src = giftIframe.src;
  }
  giftOverlay.classList.add("active");
});

closeGift.addEventListener("click", () => {
  giftOverlay.classList.remove("active");
});

fullscreenGiftBtn.addEventListener("click", () => {
  if (!document.fullscreenElement) {
    if (giftModalElement.requestFullscreen) {
      giftModalElement.requestFullscreen();
    } else if (giftModalElement.webkitRequestFullscreen) {
      giftModalElement.webkitRequestFullscreen();
    } else if (giftModalElement.msRequestFullscreen) {
      giftModalElement.msRequestFullscreen();
    }
    fullscreenGiftBtn.innerHTML = '<i class="fa-solid fa-compress"></i>';
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
    fullscreenGiftBtn.innerHTML = '<i class="fa-solid fa-expand"></i>';
  }
});

document.addEventListener("fullscreenchange", () => {
  if (!document.fullscreenElement) {
    fullscreenGiftBtn.innerHTML = '<i class="fa-solid fa-expand"></i>';
  }
});

closeImage.addEventListener("click", () => {
  imageOverlay.classList.remove("active");
});

btnMusic.addEventListener("click", () => musicOverlay.classList.add("active"));
closeMusic.addEventListener("click", () => {
  musicOverlay.classList.remove("active");
});

playPauseBtn.addEventListener("click", () => {
  if (isPlaying) {
    pauseSong();
  } else {
    playSong();
  }
});

prevBtn.addEventListener("click", prevSong);
nextBtn.addEventListener("click", nextSong);
audioPlayer.addEventListener("timeupdate", updateProgress);
audioPlayer.addEventListener("ended", nextSong);
progressBar.addEventListener("click", setProgress);
const popSound = document.getElementById("pop-sound");
let musicStarted = false;

function startMusic() {
  if (!musicStarted) {
    playSong();
    musicStarted = true;
  }
}

function handleInteraction() {
  if (popSound) {
    const sound = popSound.cloneNode();
    sound.play().catch(() => { });
  }
  startMusic();
}

window.addEventListener("click", handleInteraction, { capture: true });
window.addEventListener("touchstart", handleInteraction, { capture: true });


loadSong(songs[songIndex]);

const lockScreen = document.getElementById("lock-screen");
const mainContent = document.getElementById("main-content");
const passDots = document.querySelectorAll(".dot");
const numBtns = document.querySelectorAll(".num-btn[data-value]");
const deleteBtn = document.querySelector(".num-btn.delete-btn");

let enteredPin = "";
const correctPin = "0803";

function updateDots() {
  passDots.forEach((dot, index) => {
    if (index < enteredPin.length) {
      dot.classList.add("active");
    } else {
      dot.classList.remove("active");
    }
  });
}

function handleInput(num) {
  if (!lockScreen || lockScreen.classList.contains("unlocked")) return;

  if (enteredPin.length < 4) {
    enteredPin += num;
    updateDots();

    if (enteredPin.length === 4) {
      checkPin(); // Call immediately, no setTimeout to preserve user gesture
    }
  }
}

function checkPin() {
  if (enteredPin === correctPin) {
    unlock();
  } else {
    fail();
  }
}

function unlock() {
  lockScreen.classList.add("unlocked");
  mainContent.classList.remove("main-content-hidden");
  mainContent.classList.add("main-content-visible");
  enteredPin = "";
  updateDots();
  startMusic(); // Trigger music immediately upon unlock
}

function fail() {
  const dotsContainer = document.getElementById("pass-dots");
  dotsContainer.classList.add("shake");

  if (navigator.vibrate) {
    navigator.vibrate(200);
  }

  setTimeout(() => {
    dotsContainer.classList.remove("shake");
    enteredPin = "";
    updateDots();
  }, 500);
}

function deleteLastDigit() {
  if (enteredPin.length > 0) {
    enteredPin = enteredPin.slice(0, -1);
    updateDots();
  }
}

if (numBtns) {
  numBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      // e.stopPropagation(); // Removed to allow global click listener to catch interaction
      handleInput(btn.getAttribute("data-value"));
    });
  });
}

if (deleteBtn) {
  deleteBtn.addEventListener("click", (e) => {
    // e.stopPropagation(); // Removed
    deleteLastDigit();
  });
}

document.addEventListener("keydown", (e) => {
  if (!lockScreen || lockScreen.classList.contains("unlocked")) return;

  if (e.key >= "0" && e.key <= "9") {
    handleInput(e.key);
  } else if (e.key === "Backspace") {
    deleteLastDigit();
  }
});

const resetLockBtn = document.getElementById("btn-reset-lock");
if (resetLockBtn) {
  resetLockBtn.addEventListener("click", () => {
    window.location.reload();
  });
}
