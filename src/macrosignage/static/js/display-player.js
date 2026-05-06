(() => {
  const player = document.querySelector("[data-display-player]");
  if (!player) return;

  const slides = Array.from(player.querySelectorAll("[data-player-slide]"));
  let activeIndex = 0;
  let timerId = null;
  let sliderTimerId = null;
  let lastContentVersion = null;

  const reloadForContentUpdate = (event) => {
    try {
      const payload = JSON.parse(event.data || "{}");
      if (payload.contentVersion && payload.contentVersion !== lastContentVersion) {
        if (lastContentVersion !== null) {
          window.location.reload();
        }
        lastContentVersion = payload.contentVersion;
      }
    } catch (_error) {
      window.location.reload();
    }
  };

  if (player.dataset.eventsUrl && "EventSource" in window) {
    const events = new EventSource(player.dataset.eventsUrl);
    events.addEventListener("content.updated", reloadForContentUpdate);
  }

  const scheduleRefreshAt = Date.parse(player.dataset.scheduleRefreshAt || "");
  if (Number.isFinite(scheduleRefreshAt)) {
    const refreshDelay = scheduleRefreshAt - Date.now() + 1000;
    if (refreshDelay > 0) {
      window.setTimeout(() => {
        window.location.reload();
      }, Math.min(refreshDelay, 2147483647));
    }
  }

  if (slides.length === 0) return;

  const stopVideo = (slide) => {
    const video = slide.querySelector("video");
    if (!video) return;
    video.pause();
    video.currentTime = 0;
    video.onended = null;
  };

  const stopYouTube = (slide) => {
    const iframe = slide.querySelector("[data-player-youtube]");
    if (!iframe) return;
    iframe.removeAttribute("src");
  };

  const playVideo = (slide, onEnded) => {
    const video = slide.querySelector("video");
    if (!video) return false;
    video.muted = true;
    video.currentTime = 0;
    video.onended = onEnded;
    video.play().catch(() => {});
    return true;
  };

  const playYouTube = (slide) => {
    const iframe = slide.querySelector("[data-player-youtube]");
    if (!iframe) return false;
    if (!iframe.getAttribute("src")) {
      iframe.setAttribute("src", iframe.dataset.src || "");
    }
    return true;
  };

  const stopSlider = (slide) => {
    window.clearTimeout(sliderTimerId);
    sliderTimerId = null;
    const innerSlides = Array.from(slide.querySelectorAll("[data-slider-inner-slide]"));
    innerSlides.forEach((innerSlide, index) => {
      innerSlide.classList.toggle("active", index === 0);
    });
  };

  const sliderSlideDuration = (slide) => {
    const parsedDuration = Number.parseInt(slide.dataset.duration || "10", 10);
    const duration = Number.isFinite(parsedDuration) && parsedDuration > 0 ? parsedDuration : 10;
    return duration * 1000;
  };

  const restartAnimations = (slide) => {
    const animatedElements = Array.from(slide.querySelectorAll("[data-animate-target]"));
    animatedElements.forEach((element) => {
      const animationClass = element.dataset.animateClass;
      if (!animationClass) return;
      element.classList.remove("animate__animated", animationClass);
      void element.offsetWidth;
      element.classList.add("animate__animated", animationClass);
    });
  };

  const playSlider = (slide) => {
    const slider = slide.querySelector("[data-player-slider]");
    if (!slider) return false;

    const innerSlides = Array.from(slider.querySelectorAll("[data-slider-inner-slide]"));
    if (innerSlides.length === 0) return false;

    let innerIndex = 0;
    const setInnerSlide = (nextIndex) => {
      innerSlides.forEach((innerSlide, index) => {
        const active = index === nextIndex;
        innerSlide.classList.toggle("active", active);
        if (active) {
          restartAnimations(innerSlide);
        }
      });
      innerIndex = nextIndex;
    };

    const scheduleInnerSlide = () => {
      window.clearTimeout(sliderTimerId);
      sliderTimerId = window.setTimeout(() => {
        setInnerSlide((innerIndex + 1) % innerSlides.length);
        scheduleInnerSlide();
      }, sliderSlideDuration(innerSlides[innerIndex]));
    };

    setInnerSlide(0);
    if (innerSlides.length > 1) {
      scheduleInnerSlide();
    }
    return true;
  };

  const slideDuration = (slide) => {
    const parsedDuration = Number.parseInt(slide.dataset.duration || "30", 10);
    const duration = Number.isFinite(parsedDuration) && parsedDuration > 0 ? parsedDuration : 30;
    return duration * 1000;
  };

  const setActiveSlide = (nextIndex) => {
    slides.forEach((slide, index) => {
      const active = index === nextIndex;
      slide.classList.toggle("active", active);
      slide.setAttribute("aria-hidden", active ? "false" : "true");
      if (!active) {
        stopVideo(slide);
        stopYouTube(slide);
        stopSlider(slide);
      }
    });
    activeIndex = nextIndex;
  };

  const showNextSlide = () => {
    window.clearTimeout(timerId);
    const nextIndex = (activeIndex + 1) % slides.length;
    setActiveSlide(nextIndex);
    scheduleNextSlide();
  };

  const scheduleNextSlide = () => {
    const activeSlide = slides[activeIndex];
    const videoIsPlaying = playVideo(activeSlide, showNextSlide);
    playYouTube(activeSlide);
    playSlider(activeSlide);
    timerId = window.setTimeout(showNextSlide, slideDuration(activeSlide));
    if (videoIsPlaying) {
      activeSlide.querySelector("video").onended = showNextSlide;
    }
  };

  setActiveSlide(0);
  if (slides.length > 1) {
    scheduleNextSlide();
  } else {
    playVideo(slides[0], () => {});
    playYouTube(slides[0]);
    playSlider(slides[0]);
  }
})();
