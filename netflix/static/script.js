// Navbar background on scroll
window.addEventListener("scroll", () => {
    const navbar = document.getElementById("navbar");
    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});

// Row Slider functionality
const sliders = document.querySelectorAll(".row-container");

sliders.forEach((sliderContainer) => {
    const slider = sliderContainer.querySelector(".slider");
    const leftHandle = sliderContainer.querySelector(".left-handle");
    const rightHandle = sliderContainer.querySelector(".right-handle");

    // Scroll amount is roughly one view width minus padding
    const scrollAmount = window.innerWidth * 0.8;

    leftHandle.addEventListener("click", () => {
        slider.scrollBy({ left: -scrollAmount, behavior: "smooth" });
    });

    rightHandle.addEventListener("click", () => {
        slider.scrollBy({ left: scrollAmount, behavior: "smooth" });
    });
});

// Video Modal Context
const modal = document.getElementById("video-modal");
const youtubePlayer = document.getElementById("youtube-player");

function openPlayer(videoId) {
    if (!videoId) return;
    
    document.body.style.overflow = "hidden"; // Prevent background scrolling
    
    // Set iframe src with autoplay and no controls for realism
    // modestbranding=1, rel=0, controls=0 removes most YT branding
    const embedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&controls=0&modestbranding=1&rel=0&showinfo=0&fs=0`;
    youtubePlayer.src = embedUrl;
    
    modal.classList.add("active");
}

function closePlayer(event) {
    // Only close if clicking the backdrop, not the video itself
    if (event.target === modal) {
        forceClosePlayer();
    }
}

function forceClosePlayer() {
    modal.classList.remove("active");
    document.body.style.overflow = "auto";
    // Stop video and clear src immediately
    youtubePlayer.src = "";
}

// Close on escape key
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("active")) {
        forceClosePlayer();
    }
});
