// 부트스트랩: 로딩 → 타이틀 → 플레이 → 결과 흐름과 requestAnimationFrame 메인 루프
/// <reference types="vite/client" />
import './style.css';
import { AudioManager } from './audio/audio';
import { DEFAULT_CONFIG } from './config';
import { createGame, createRng, step } from './game/sim';
import type { GameState, SimEvent } from './game/types';
import { InputController } from './input/input';
import { Renderer } from './render/renderer';
import { loadSprites, type SpriteBank } from './render/sprites';
import { loadBest, loadMuted, loadVolume, saveBest, saveMuted, saveVolume, storageFailed } from './storage';
import { Screens, type ScreenName } from './ui/screens';

type SfxName = Parameters<AudioManager['playSfx']>[0];

/** sim 이벤트 → 효과음 */
const EVENT_SFX: Partial<Record<SimEvent, SfxName>> = {
  sherum_warn: 'warn',
  sherum_watch: 'watch',
  sherum_back: 'back',
  caught: 'caught',
  bored: 'bored',
  bread: 'bread',
  bread_empty: 'ui',
  dance_start: 'dance_start',
};

const MAX_FRAME_DT = 0.1;

const audio = new AudioManager();
let screen: ScreenName = 'loading';
let paused = false;
let state: GameState = newGame();
let volume = loadVolume();
let muted = loadMuted();
let lastIntensity = -1;
let lastTs = 0;

/**
 * 개발용 디버그 훅: DEV 서버이거나 ?debug=1일 때만 동작.
 * ?t=95 → 시작 elapsed 강제, ?phase=turning_right → 셰럼 단계를 강제하고 그 단계에 머물게 한다.
 */
const DEBUG_PARAMS = (() => {
  const q = new URLSearchParams(window.location.search);
  return import.meta.env.DEV || q.get('debug') === '1' ? q : null;
})();

function applyDebugStart(s: GameState): void {
  if (!DEBUG_PARAMS) return;
  const t = Number(DEBUG_PARAMS.get('t'));
  if (Number.isFinite(t) && t > 0) s.elapsed = t;
  const phase = DEBUG_PARAMS.get('phase');
  if (phase === 'left_safe' || phase === 'turning_right' || phase === 'right_watching' || phase === 'turning_left') {
    s.sherum.phase = phase;
    s.sherum.timer = 0;
    s.sherum.phaseDuration = 1e6;
  }
}

function newGame(): GameState {
  const seed = (Date.now() ^ Math.floor(Math.random() * 0xffffffff)) >>> 0;
  return createGame(DEFAULT_CONFIG, createRng(seed));
}

function sfx(name: SfxName): void {
  try {
    audio.playSfx(name);
  } catch {
    // 오디오 오류는 게임에 영향 주지 않음
  }
}

const emptyBank: SpriteBank = {
  manifest: null,
  images: new Map(),
  background: null,
  manifestFailed: false,
  missing: [],
};

const canvas = document.getElementById('game') as HTMLCanvasElement;
const renderer = new Renderer(canvas, emptyBank);

const screens = new Screens({
  onStart: startGame,
  onResume: resume,
  onTitle: goTitle,
  onPause: pause,
  onMuteToggle: () => {
    muted = !muted;
    audio.setMuted(muted);
    saveMuted(muted);
    screens.setSound(volume, muted);
    sfx('ui');
  },
  onVolume: (v) => {
    volume = v;
    audio.setVolume(v);
    saveVolume(v);
  },
});

const input = new InputController({
  isPlaying: () => screen === 'playing' && !paused,
  onConfirm: () => {
    if (screen === 'title' || screen === 'result') startGame();
    else if (screen === 'playing' && paused) resume();
  },
  onPause: () => {
    if (screen !== 'playing') return;
    if (paused) resume();
    else pause();
  },
  onHidden: () => {
    if (screen === 'playing' && !paused) pause();
  },
});
input.bindTouchButtons(screens.danceBtn, screens.breadBtn);

function startGame(): void {
  if (screen === 'loading') return;
  state = newGame();
  applyDebugStart(state);
  renderer.reset();
  paused = false;
  screen = 'playing';
  lastIntensity = -1;
  screens.show('playing');
  input.beginRound();
  // AudioContext는 사용자 제스처 안에서 생성·재개
  audio
    .unlock()
    .catch(() => undefined)
    .finally(() => {
      sfx('ui');
      if (screen === 'playing' && !paused) audio.startBgm();
    });
}

function pause(): void {
  if (screen !== 'playing' || paused) return;
  paused = true;
  // Space 물리 상태는 유지해야 재개 시 누른 채인 Space를 억제할 수 있다
  input.releaseDance();
  audio.stopBgm();
  screens.show('playing', true);
}

function resume(): void {
  if (screen !== 'playing' || !paused) return;
  paused = false;
  screens.show('playing');
  input.beginRound();
  void audio.unlock().finally(() => {
    sfx('ui');
    if (screen === 'playing' && !paused) audio.startBgm();
  });
}

function goTitle(): void {
  sfx('ui');
  audio.stopBgm();
  input.releaseDance();
  paused = false;
  state = newGame();
  renderer.reset();
  screen = 'title';
  screens.setBest(loadBest());
  screens.show('title');
}

function endGame(): void {
  const r = state.result;
  if (!r) return;
  const prevBest = loadBest();
  const isNewBest = r.score > prevBest;
  if (isNewBest) saveBest(r.score);
  audio.stopBgm();
  input.releaseDance();
  screen = 'result';
  screens.showResult({
    reason: r.reason,
    score: r.score,
    elapsed: r.elapsed,
    best: Math.max(prevBest, r.score),
    isNewBest,
    maxStreak: r.maxStreak,
    storageFailed: storageFailed(),
  });
}

function handleEvents(events: readonly SimEvent[]): void {
  renderer.handleEvents(events);
  for (const e of events) {
    const name = EVENT_SFX[e];
    if (name) sfx(name);
  }
}

function frame(ts: number): void {
  const dt = lastTs ? Math.min(Math.max((ts - lastTs) / 1000, 0), MAX_FRAME_DT) : 0;
  lastTs = ts;
  const active = screen === 'playing' && !paused;
  if (active) {
    step(state, input.poll(), dt);
    handleEvents(state.events);
    // 시간이 지날수록 BGM 강도 상승 (0.05 단위로만 갱신)
    const intensity = Math.round(Math.min(1, state.elapsed / DEFAULT_CONFIG.difficultyRampTime) * 20) / 20;
    if (intensity !== lastIntensity) {
      lastIntensity = intensity;
      audio.setBgmIntensity(intensity);
    }
    if (state.mode === 'over') endGame();
  }
  renderer.update(state, screen === 'playing' && paused ? 0 : dt);
  renderer.draw(state, screen === 'playing' || screen === 'result');
  requestAnimationFrame(frame);
}

function setupEnvironment(): void {
  // 터치 기기 표시: 터치 버튼 노출용
  const markTouch = () => document.body.classList.add('touch');
  if (window.matchMedia('(pointer: coarse)').matches) markTouch();
  window.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch') markTouch();
  });

  // 세로로 돌리면 일시정지
  const portrait = window.matchMedia('(orientation: portrait)');
  portrait.addEventListener('change', () => {
    if (portrait.matches && screen === 'playing' && !paused) pause();
  });

  const onResize = () => renderer.resize();
  window.addEventListener('resize', onResize);
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(onResize).observe(canvas);
}

async function boot(): Promise<void> {
  setupEnvironment();
  audio.setVolume(volume);
  audio.setMuted(muted);
  screens.setSound(volume, muted);
  screens.setBest(loadBest());
  screens.show('loading');
  requestAnimationFrame(frame);

  const bank = await loadSprites((done, total) => screens.setLoading(done, total));
  renderer.setBank(bank);

  if (bank.manifestFailed) {
    screens.setAssetNote('그림 자료를 불러오지 못해 임시 도형으로 표시해요. 새로고침하면 다시 시도해요.');
  } else if (bank.missing.length > 0) {
    screens.setAssetNote(`일부 그림(${bank.missing.length}개)을 불러오지 못해 임시 도형으로 표시해요.`);
  }
  const iconSrc = (key: string) =>
    bank.images.has(key) && bank.manifest ? `./assets/${bank.manifest.sprites[key].src}` : null;
  screens.setTouchIcons(iconSrc('ui_dance_icon'), iconSrc('ui_bread_icon'));

  screen = 'title';
  screens.show('title');
}

void boot();
