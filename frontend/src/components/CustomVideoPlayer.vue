<template>
  <div
    ref="playerContainer"
    class="custom-player"
    :class="{ 'hide-cursor': !showControls && isPlaying }"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <video
      ref="videoRef"
      :src="src"
      class="video-element"
      preload="metadata"
      @click="togglePlay"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @progress="onProgress"
      @ended="onEnded"
      @play="onNativePlay"
      @pause="onNativePause"
      @volumechange="syncVolumeState"
    />

    <div v-if="activeSubtitleText" class="subtitle-overlay">
      <div class="subtitle-chip">{{ activeSubtitleText }}</div>
    </div>

    <div v-if="!isPlaying && !isEnded" class="center-overlay" @click="togglePlay">
      <div class="play-icon-bg">
        <el-icon size="40" color="#fff"><VideoPlay /></el-icon>
      </div>
    </div>

    <div v-if="showEndScreenOverlay" class="end-screen-overlay">
      <div class="end-screen-content">
        <div class="end-grid">
          <div
            v-for="item in endScreenOverlayList"
            :key="item.id"
            class="end-card"
            @click.stop="playNext(item.id)"
          >
            <div class="end-card-img">
              <img :src="item.cover_url" />
              <span class="end-duration">{{ formatDuration(item.duration) }}</span>
            </div>
            <div class="end-card-info">
              <div class="end-title">{{ item.title }}</div>
              <div class="end-author">{{ item.uploader_name }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showPostRoll" class="post-roll-overlay">
      <div class="post-roll-header">接下来播放</div>
      <div class="post-roll-grid">
        <div
          v-for="item in postRollList"
          :key="item.id"
          class="post-card"
          @click.stop="playNext(item.id)"
        >
          <div class="post-thumb">
            <img :src="item.cover_url" />
            <span class="post-duration">{{ formatDuration(item.duration) }}</span>
          </div>
          <div class="post-info">
            <div class="post-title">{{ item.title }}</div>
            <div class="post-author">{{ item.uploader_name }}</div>
          </div>
        </div>
      </div>
      <div class="post-replay-btn" @click.stop="togglePlay">
        <el-icon><RefreshRight /></el-icon>
        重播
      </div>
    </div>

    <div class="controls-bar" :class="{ visible: showControls || !isPlaying }">
      <div
        ref="progressRef"
        class="progress-container"
        @mousedown="startDrag"
        @click="seek"
      >
        <div class="progress-bg"></div>
        <div class="progress-buffered" :style="{ width: `${bufferedPercentage}%` }"></div>
        <div class="progress-current" :style="{ width: `${currentPercentage}%` }">
          <div class="progress-handle"></div>
        </div>
      </div>

      <div class="controls-row">
        <div class="left-controls">
          <el-icon class="ctrl-btn" size="24" @click="togglePlay">
            <VideoPause v-if="isPlaying" />
            <VideoPlay v-else />
          </el-icon>

          <div class="volume-box">
            <el-icon class="ctrl-btn" size="24" @click="toggleMute">
              <Mute v-if="isMuted || volume === 0" />
              <Microphone v-else />
            </el-icon>
            <input
              v-model="volume"
              class="volume-slider"
              type="range"
              min="0"
              max="1"
              step="0.05"
              @input="updateVolume"
            />
          </div>

          <div class="time-display">
            {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
          </div>
        </div>

        <div class="right-controls">
          <el-icon
            v-if="hasSubtitleControl"
            class="ctrl-btn"
            size="24"
            :color="showSubtitle ? '#fff' : '#909090'"
            @click="toggleSubtitle"
          >
            <ChatLineSquare />
          </el-icon>
          <el-icon class="ctrl-btn" size="24" @click="toggleFullscreen">
            <FullScreen />
          </el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  ChatLineSquare,
  FullScreen,
  Microphone,
  Mute,
  RefreshRight,
  VideoPause,
  VideoPlay
} from '@element-plus/icons-vue';

const props = defineProps({
  src: String,
  autoplay: { type: Boolean, default: false },
  endScreenData: { type: Array, default: () => [] },
  postRollData: { type: Array, default: () => [] },
  subtitleUrl: { type: String, default: '' }
});

const emit = defineEmits(['timeupdate', 'play', 'pause', 'ended', 'navigate']);

const videoRef = ref(null);
const playerContainer = ref(null);
const progressRef = ref(null);

const isPlaying = ref(false);
const isEnded = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const currentPercentage = ref(0);
const bufferedPercentage = ref(0);
const volume = ref(1);
const isMuted = ref(false);
const showControls = ref(true);
const isDragging = ref(false);
const showSubtitle = ref(true);
const subtitleCues = ref([]);
const lastNonZeroVolume = ref(1);

let controlTimer = null;
let subtitleRequestId = 0;

const hasSubtitleControl = computed(() => Boolean(props.subtitleUrl && subtitleCues.value.length > 0));

const activeSubtitleText = computed(() => {
  if (!showSubtitle.value || !subtitleCues.value.length) {
    return '';
  }

  const cue = subtitleCues.value.find((item) => {
    return currentTime.value >= item.start && currentTime.value <= item.end;
  });

  return cue?.text || '';
});

const showEndScreenOverlay = computed(() => {
  if (!duration.value || isEnded.value) return false;
  return duration.value - currentTime.value <= 10 && props.endScreenData.length > 0;
});

const showPostRoll = computed(() => {
  return isEnded.value && (props.postRollData.length > 0 || props.endScreenData.length > 0);
});

const endScreenOverlayList = computed(() => props.endScreenData.slice(0, 2));
const postRollList = computed(() => props.postRollData.slice(0, 12));

const formatTime = (time) => {
  if (!time || Number.isNaN(time)) return '0:00';
  const minutes = Math.floor(time / 60);
  const seconds = Math.floor(time % 60);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const formatDuration = (seconds) => {
  if (!seconds) return '0:00';
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

const syncVolumeState = () => {
  if (!videoRef.value) return;
  volume.value = Number(videoRef.value.volume ?? 1);
  isMuted.value = Boolean(videoRef.value.muted || volume.value === 0);
  if (volume.value > 0) {
    lastNonZeroVolume.value = volume.value;
  }
};

const togglePlay = async () => {
  if (!videoRef.value) return;

  if (isEnded.value) {
    videoRef.value.currentTime = 0;
    isEnded.value = false;
  }

  if (videoRef.value.paused) {
    try {
      await videoRef.value.play();
    } catch (error) {
      console.error('Play failed:', error);
    }
    return;
  }

  videoRef.value.pause();
};

const onNativePlay = () => {
  isPlaying.value = true;
  isEnded.value = false;
  emit('play');
  handleMouseMove();
};

const onNativePause = () => {
  isPlaying.value = false;
  emit('pause');
  showControls.value = true;
};

const onEnded = () => {
  isEnded.value = true;
  isPlaying.value = false;
  currentTime.value = duration.value;
  currentPercentage.value = 100;
  showControls.value = true;
  emit('ended');
};

const onTimeUpdate = () => {
  if (!videoRef.value || isDragging.value) return;
  currentTime.value = videoRef.value.currentTime;
  currentPercentage.value = duration.value ? (currentTime.value / duration.value) * 100 : 0;
  emit('timeupdate', currentTime.value);
};

const onProgress = () => {
  if (!videoRef.value || !duration.value) return;
  const buffered = videoRef.value.buffered;
  if (!buffered?.length) {
    bufferedPercentage.value = 0;
    return;
  }

  const end = buffered.end(buffered.length - 1);
  bufferedPercentage.value = Math.min((end / duration.value) * 100, 100);
};

const updateSeekByPointer = (event) => {
  if (!progressRef.value || !videoRef.value || !duration.value) return;
  const rect = progressRef.value.getBoundingClientRect();
  let position = (event.clientX - rect.left) / rect.width;
  position = Math.max(0, Math.min(1, position));
  currentPercentage.value = position * 100;
  currentTime.value = position * duration.value;
  videoRef.value.currentTime = currentTime.value;
  if (isEnded.value) isEnded.value = false;
};

const startDrag = (event) => {
  isDragging.value = true;
  updateSeekByPointer(event);
  document.addEventListener('mousemove', handleDrag);
  document.addEventListener('mouseup', stopDrag);
};

const handleDrag = (event) => {
  updateSeekByPointer(event);
};

const stopDrag = (event) => {
  if (!isDragging.value) return;
  updateSeekByPointer(event);
  isDragging.value = false;
  document.removeEventListener('mousemove', handleDrag);
  document.removeEventListener('mouseup', stopDrag);
};

const seek = (event) => {
  if (isDragging.value) return;
  updateSeekByPointer(event);
};

const updateVolume = () => {
  if (!videoRef.value) return;
  const nextVolume = Math.max(0, Math.min(1, Number(volume.value)));
  volume.value = nextVolume;
  videoRef.value.volume = nextVolume;
  videoRef.value.muted = nextVolume === 0;
  isMuted.value = videoRef.value.muted;
  if (nextVolume > 0) {
    lastNonZeroVolume.value = nextVolume;
  }
};

const toggleMute = () => {
  if (!videoRef.value) return;

  if (videoRef.value.muted || volume.value === 0) {
    const restoredVolume = lastNonZeroVolume.value > 0 ? lastNonZeroVolume.value : 1;
    volume.value = restoredVolume;
    videoRef.value.volume = restoredVolume;
    videoRef.value.muted = false;
  } else {
    if (volume.value > 0) {
      lastNonZeroVolume.value = volume.value;
    }
    videoRef.value.muted = true;
  }

  syncVolumeState();
};

const toggleSubtitle = () => {
  showSubtitle.value = !showSubtitle.value;
};

const toggleFullscreen = async () => {
  if (!playerContainer.value) return;

  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
      return;
    }
    await playerContainer.value.requestFullscreen();
  } catch (error) {
    console.error('Fullscreen failed:', error);
  }
};

const playNext = (id) => {
  isEnded.value = false;
  emit('navigate', id);
};

const playVideo = async () => {
  if (!videoRef.value) return;
  try {
    await videoRef.value.play();
  } catch (error) {
    console.warn('Autoplay blocked, retrying muted:', error);
    videoRef.value.muted = true;
    syncVolumeState();
    try {
      await videoRef.value.play();
    } catch (retryError) {
      console.error('Autoplay failed:', retryError);
    }
  }
};

const setCurrentTime = (time) => {
  if (!videoRef.value) return;
  videoRef.value.currentTime = time;
  currentTime.value = time;
  currentPercentage.value = duration.value ? (time / duration.value) * 100 : 0;
};

const handleMouseMove = () => {
  showControls.value = true;
  if (controlTimer) clearTimeout(controlTimer);
  if (isPlaying.value) {
    controlTimer = setTimeout(() => {
      showControls.value = false;
    }, 3000);
  }
};

const handleMouseLeave = () => {
  if (isPlaying.value) {
    showControls.value = false;
  }
};

const shouldIgnoreHotkey = (event) => {
  const target = event.target;
  return Boolean(
    target &&
    (target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable)
  );
};

const handleKeydown = (event) => {
  if (!videoRef.value || shouldIgnoreHotkey(event)) return;

  if (event.code === 'Space' || event.key.toLowerCase() === 'k') {
    event.preventDefault();
    togglePlay();
    return;
  }

  if (event.key.toLowerCase() === 'm') {
    event.preventDefault();
    toggleMute();
    return;
  }

  if (event.key === 'ArrowRight') {
    event.preventDefault();
    setCurrentTime(Math.min(currentTime.value + 5, duration.value || currentTime.value + 5));
    return;
  }

  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    setCurrentTime(Math.max(currentTime.value - 5, 0));
    return;
  }

  if (event.key === 'ArrowUp') {
    event.preventDefault();
    volume.value = Math.min(Number(volume.value) + 0.05, 1);
    updateVolume();
    return;
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    volume.value = Math.max(Number(volume.value) - 0.05, 0);
    updateVolume();
  }
};

const parseTimestamp = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value !== 'string') return null;

  const raw = value.trim();
  if (!raw) return null;

  if (/^\d+(\.\d+)?$/.test(raw)) {
    return Number(raw);
  }

  const normalized = raw.replace(',', '.');
  const parts = normalized.split(':').map((item) => item.trim());
  if (parts.some((item) => item === '' || Number.isNaN(Number(item)))) {
    return null;
  }

  let seconds = 0;
  for (const part of parts) {
    seconds = seconds * 60 + Number(part);
  }
  return seconds;
};

const normalizeCueText = (text) => {
  return String(text || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\{\\an\d\}/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
};

const parseTextSubtitle = (rawText) => {
  const blocks = rawText
    .replace(/\r/g, '')
    .replace(/^WEBVTT\s*/i, '')
    .split(/\n{2,}/);

  const cues = [];

  for (const block of blocks) {
    const lines = block
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);

    if (!lines.length) continue;

    const timingIndex = lines.findIndex((line) => line.includes('-->'));
    if (timingIndex === -1) continue;

    const [startRaw, endRaw] = lines[timingIndex].split('-->').map((line) => line.trim().split(/\s+/)[0]);
    const start = parseTimestamp(startRaw);
    const end = parseTimestamp(endRaw);
    const text = normalizeCueText(lines.slice(timingIndex + 1).join(' '));

    if (start === null || end === null || !text) continue;
    cues.push({ start, end, text });
  }

  return cues;
};

const collectJsonCues = (value, cues) => {
  if (Array.isArray(value)) {
    value.forEach((item) => collectJsonCues(item, cues));
    return;
  }

  if (!value || typeof value !== 'object') {
    return;
  }

  const textCandidate =
    value.text ??
    value.content ??
    value.subtitle ??
    value.caption ??
    value.sentence ??
    value.line ??
    value.value;

  const startCandidate =
    value.start ??
    value.start_time ??
    value.startTime ??
    value.from ??
    value.begin ??
    value.timestamp;

  const endCandidate =
    value.end ??
    value.end_time ??
    value.endTime ??
    value.to ??
    value.finish;

  const start = parseTimestamp(startCandidate);
  const end = parseTimestamp(endCandidate);
  const text = normalizeCueText(textCandidate);

  if (start !== null && end !== null && text) {
    cues.push({ start, end, text });
  }

  Object.values(value).forEach((nested) => {
    if (typeof nested === 'object' && nested !== null) {
      collectJsonCues(nested, cues);
    }
  });
};

const parseJsonSubtitle = (rawText) => {
  try {
    const data = JSON.parse(rawText);
    const cues = [];
    collectJsonCues(data, cues);
    return cues;
  } catch (error) {
    return [];
  }
};

const dedupeAndSortCues = (cues) => {
  const seen = new Set();
  return cues
    .filter((cue) => cue.end > cue.start)
    .sort((a, b) => a.start - b.start)
    .filter((cue) => {
      const key = `${cue.start}-${cue.end}-${cue.text}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
};

const parseSubtitleContent = (rawText) => {
  const jsonCues = parseJsonSubtitle(rawText);
  if (jsonCues.length) {
    return dedupeAndSortCues(jsonCues);
  }

  return dedupeAndSortCues(parseTextSubtitle(rawText));
};

const loadSubtitleCues = async () => {
  const currentId = ++subtitleRequestId;
  subtitleCues.value = [];

  if (!props.subtitleUrl) {
    return;
  }

  try {
    const response = await fetch(props.subtitleUrl);
    if (!response.ok) {
      throw new Error(`Subtitle request failed: ${response.status}`);
    }

    const rawText = await response.text();
    if (currentId !== subtitleRequestId) return;
    subtitleCues.value = parseSubtitleContent(rawText);
  } catch (error) {
    if (currentId !== subtitleRequestId) return;
    subtitleCues.value = [];
    console.warn('Subtitle parse failed:', error);
  }
};

const resetPlayerState = () => {
  isPlaying.value = false;
  isEnded.value = false;
  currentTime.value = 0;
  currentPercentage.value = 0;
  bufferedPercentage.value = 0;
  showControls.value = true;
};

const onLoadedMetadata = () => {
  if (!videoRef.value) return;
  duration.value = videoRef.value.duration || 0;
  currentTime.value = videoRef.value.currentTime || 0;
  currentPercentage.value = duration.value ? (currentTime.value / duration.value) * 100 : 0;
  bufferedPercentage.value = 0;
  isEnded.value = false;
  showControls.value = true;
  syncVolumeState();
  if (props.autoplay) {
    playVideo();
  }
};

watch(
  () => props.subtitleUrl,
  () => {
    loadSubtitleCues();
  },
  { immediate: true }
);

watch(
  () => props.src,
  () => {
    resetPlayerState();
  }
);

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown);
  document.removeEventListener('mousemove', handleDrag);
  document.removeEventListener('mouseup', stopDrag);
  if (controlTimer) clearTimeout(controlTimer);
});

defineExpose({ playVideo, setCurrentTime });
</script>

<style scoped>
.custom-player {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
  user-select: none;
  font-family: Roboto, Arial, sans-serif;
}

.custom-player.hide-cursor {
  cursor: none;
}

.video-element {
  display: block;
  width: 100%;
  height: 100%;
}

.subtitle-overlay {
  position: absolute;
  left: 50%;
  bottom: 78px;
  z-index: 18;
  width: min(80%, 760px);
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  pointer-events: none;
}

.subtitle-chip {
  padding: 10px 16px;
  border-radius: 18px;
  background: rgba(8, 10, 18, 0.68);
  color: #fff;
  text-align: center;
  line-height: 1.65;
  font-size: 15px;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(12px);
}

.center-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
}

.play-icon-bg {
  display: flex;
  width: 60px;
  height: 60px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.controls-bar {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 12px 12px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.controls-bar.visible {
  opacity: 1;
}

.progress-container {
  position: relative;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: height 0.15s;
}

.progress-container:hover {
  height: 10px;
}

.progress-bg,
.progress-buffered,
.progress-current {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  border-radius: inherit;
}

.progress-bg {
  width: 100%;
}

.progress-buffered {
  background: rgba(255, 255, 255, 0.38);
}

.progress-current {
  display: flex;
  align-items: center;
  background: #ff2d55;
}

.progress-handle {
  width: 12px;
  height: 12px;
  margin-right: -6px;
  margin-left: auto;
  border-radius: 50%;
  background: #ff2d55;
  transform: scale(0);
  transition: transform 0.1s;
}

.progress-container:hover .progress-handle {
  transform: scale(1);
}

.controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.left-controls,
.right-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ctrl-btn {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.ctrl-btn:hover {
  transform: scale(1.08);
}

.time-display {
  margin-left: 5px;
  font-size: 13px;
}

.volume-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.volume-slider {
  width: 0;
  height: 4px;
  overflow: hidden;
  accent-color: #fff;
  transition: width 0.2s ease;
}

.volume-box:hover .volume-slider {
  width: 60px;
}

.end-screen-overlay {
  position: absolute;
  top: 10%;
  right: 5%;
  bottom: 15%;
  left: 5%;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.end-screen-content {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: flex-end;
  gap: 20px;
}

.end-grid {
  display: flex;
  gap: 20px;
}

.end-card {
  display: flex;
  width: 200px;
  flex-direction: column;
  overflow: hidden;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: transform 0.2s, background 0.2s;
}

.end-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.end-card-img {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
}

.end-card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.end-duration,
.post-duration {
  position: absolute;
  right: 4px;
  bottom: 4px;
  padding: 1px 4px;
  border-radius: 2px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 10px;
}

.end-card-info {
  padding: 8px;
}

.end-title {
  display: -webkit-box;
  overflow: hidden;
  margin-bottom: 4px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.end-author {
  color: #ccc;
  font-size: 10px;
}

.post-roll-overlay {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 40px;
  left: 0;
  z-index: 15;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: rgba(0, 0, 0, 0.85);
}

.post-roll-header {
  margin-bottom: 15px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.post-roll-grid {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 15px;
  overflow-y: auto;
}

.post-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
  cursor: pointer;
}

.post-card:hover .post-thumb img {
  opacity: 0.8;
}

.post-thumb {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 4px;
  aspect-ratio: 16 / 9;
}

.post-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.post-info {
  color: #fff;
}

.post-title {
  display: -webkit-box;
  overflow: hidden;
  margin-bottom: 2px;
  font-size: 13px;
  font-weight: 500;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.post-author {
  color: #aaa;
  font-size: 11px;
}

.post-replay-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  display: flex;
  width: 80px;
  height: 80px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transform: translate(-50%, -50%);
  transition: transform 0.2s, background 0.2s;
  backdrop-filter: blur(5px);
}

.post-replay-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: translate(-50%, -50%) scale(1.1);
}

.post-replay-btn .el-icon {
  margin-bottom: 5px;
  font-size: 32px;
}

@media (max-width: 768px) {
  .subtitle-overlay {
    bottom: 70px;
    width: calc(100% - 28px);
  }

  .subtitle-chip {
    padding: 8px 12px;
    font-size: 13px;
  }

  .left-controls,
  .right-controls {
    gap: 12px;
  }
}
</style>
