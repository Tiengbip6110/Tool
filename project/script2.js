let explosionIcon = "💗";
let isGifting = true;
let giftInterval = null;
let isMessaging = true;
let messageInterval = null;

let messages = [];

async function loadMessages() {
        try {
                const response = await fetch("style/mess.txt");
                const text = await response.text();
                messages = text
                        .split(/\n/)
                        .map((line) => line.trim())
                        .filter((line) => line !== "");
        } catch (error) {
                console.error("Error loading mess.txt:", error);
                // Fallback if file not found
                messages = ["Anh yêu em ❤️"];
        }
}

loadMessages();

const mainContent = document.getElementById("mainContent");

function startExperience() {
        if (mainContent.classList.contains('hidden')) {
                mainContent.classList.remove("hidden");
        }
        document.body.classList.remove("container");
        setTimeout(() => {
                createFallingImage();
                giftInterval = setInterval(createFallingImage, 1000);
                createFallingMessage();
                messageInterval = setInterval(createFallingMessage, 1500);
        }, 5000);
}

window.addEventListener("load", startExperience);

function createFallingImage() {
        if (!isGifting) return;

        const img = document.createElement("img");
        const randomNum = Math.floor(Math.random() * 20) + 1;
        img.src = `../img/Anh (${randomNum}).jpg`;
        img.className = "falling-image";

        const width = window.innerWidth;
        const size = width < 600 ? Math.random() * 40 + 50 : Math.random() * 60 + 60;
        const startX = Math.random() * (width - size);
        const duration = Math.random() * 4 + 4;

        img.style.left = startX + "px";
        img.style.width = size + "px";
        img.style.height = "auto";
        img.style.animationDuration = duration + "s";

        document.body.appendChild(img);

        setTimeout(() => {
                img.remove();
        }, duration * 1000);
}

function createFallingMessage() {
        if (!isMessaging) return;

        const msgDiv = document.createElement("div");
        msgDiv.className = "falling-message";
        msgDiv.innerText = messages[Math.floor(Math.random() * messages.length)];

        const colors = [
                { text: "#ff69b4", border: "#ffb6c1" },
                { text: "#9370db", border: "#e6e6fa" },
                { text: "#40e0d0", border: "#afeeee" },
                { text: "#ff8c00", border: "#ffe4b5" },
                { text: "#20b2aa", border: "#e0ffff" },
                { text: "#ff1493", border: "#ffc0cb" }
        ];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];

        const width = window.innerWidth;
        const padding = 20;
        const startX = Math.random() * (width - 180 - padding * 2) + padding;
        const duration = Math.random() * 5 + 5;
        const fontSize = width < 600 ? Math.random() * 4 + 14 : Math.random() * 6 + 16;

        msgDiv.style.left = Math.max(padding, startX) + "px";
        msgDiv.style.fontSize = fontSize + "px";
        msgDiv.style.color = randomColor.text;
        msgDiv.style.borderColor = randomColor.border;
        msgDiv.style.animationDuration = duration + "s";

        document.body.appendChild(msgDiv);

        setTimeout(() => {
                msgDiv.remove();
        }, duration * 1000);
}

// Explosion Effect
document.addEventListener("click", (e) => {
        createHearts(e.clientX, e.clientY);
});

document.addEventListener("touchstart", (e) => {
        createHearts(e.touches[0].clientX, e.touches[0].clientY);
});

function createHearts(x, y) {
        const numHearts = 15;
        const icons = Array.from(explosionIcon).filter(char => char.trim() !== "");

        for (let i = 0; i < numHearts; i++) {
                const heart = document.createElement("div");
                heart.innerHTML = icons[Math.floor(Math.random() * icons.length)] || "💗";
                heart.className = "heart";

                const angle = Math.random() * Math.PI * 2;
                const distance = 50 + Math.random() * 150;
                const dx = Math.cos(angle) * distance;
                const dy = Math.sin(angle) * distance;

                heart.style.setProperty("--x", dx);
                heart.style.setProperty("--y", dy);
                heart.style.left = x + "px";
                heart.style.top = y + "px";
                heart.style.fontSize = Math.random() * 20 + 10 + "px";
                heart.style.setProperty("--r", Math.random() * 360 - 180 + "deg");

                document.body.appendChild(heart);

                setTimeout(() => {
                        heart.remove();
                }, 1000);
        }
}

// Global Click Pop Sound
const popSound = document.getElementById("pop-sound");
window.addEventListener("mousedown", () => {
        if (popSound) {
                const sound = popSound.cloneNode(true);
                sound.play();
        }
}, true);
