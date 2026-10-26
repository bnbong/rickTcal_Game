// 타이틀/결과/일시정지/로딩 HTML 오버레이 제어 (회전 안내는 CSS 미디어쿼리)
import type { EndReason } from '../game/types';

export type ScreenName = 'loading' | 'title' | 'playing' | 'result';

export interface ResultView {
  reason: EndReason;
  score: number;
  elapsed: number;
  best: number;
  isNewBest: boolean;
  maxStreak: number;
  storageFailed: boolean;
}

export interface ScreenHandlers {
  onStart(): void;
  onResume(): void;
  onTitle(): void;
  onPause(): void;
  onMuteToggle(): void;
  onVolume(v: number): void;
}

const RESULT_TITLE: Record<EndReason, string> = {
  caught: '들켰다…!',
  bored: '너무 지루해서 쓰러졌다…',
};

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`#${id} 요소가 없습니다`);
  return el;
}

function formatTime(sec: number): string {
  const s = Math.floor(sec);
  return s >= 60 ? `${Math.floor(s / 60)}분 ${s % 60}초` : `${s}초`;
}

export class Screens {
  readonly stage = $('stage');
  readonly danceBtn = $('btn-dance');
  readonly breadBtn = $('btn-bread');
  private readonly overlays = {
    loading: $('screen-loading'),
    title: $('screen-title'),
    pause: $('screen-pause'),
    result: $('screen-result'),
  };
  private readonly volume = $('volume') as HTMLInputElement;
  private readonly muteBtn = $('btn-mute');

  constructor(handlers: ScreenHandlers) {
    $('btn-start').addEventListener('click', handlers.onStart);
    $('btn-retry').addEventListener('click', handlers.onStart);
    $('btn-resume').addEventListener('click', handlers.onResume);
    $('btn-pause-title').addEventListener('click', handlers.onTitle);
    $('btn-result-title').addEventListener('click', handlers.onTitle);
    $('btn-pause').addEventListener('click', handlers.onPause);
    this.muteBtn.addEventListener('click', handlers.onMuteToggle);
    this.volume.addEventListener('input', () => handlers.onVolume(Number(this.volume.value) / 100));
  }

  /** 화면 전환. paused는 playing 위의 일시정지 오버레이 */
  show(screen: ScreenName, paused = false): void {
    this.stage.dataset.screen = screen;
    this.stage.dataset.paused = String(paused);
    this.overlays.loading.hidden = screen !== 'loading';
    this.overlays.title.hidden = screen !== 'title';
    this.overlays.result.hidden = screen !== 'result';
    this.overlays.pause.hidden = !(screen === 'playing' && paused);
    // 숨겨진 버튼에 포커스가 남아 Space가 버튼을 누르지 않도록
    if (screen === 'playing' && !paused && document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
    const focusTarget =
      screen === 'title' ? 'btn-start' : screen === 'result' ? 'btn-retry' : paused ? 'btn-resume' : null;
    if (focusTarget) $(focusTarget).focus({ preventScroll: true });
  }

  setLoading(done: number, total: number): void {
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    $('loading-bar').style.width = `${pct}%`;
    $('loading-text').textContent = `불러오는 중… ${pct}%`;
  }

  setAssetNote(message: string | null): void {
    const el = $('asset-note');
    el.hidden = !message;
    el.textContent = message ?? '';
  }

  setBest(best: number): void {
    $('title-best').textContent = best.toLocaleString('ko-KR');
  }

  showResult(r: ResultView): void {
    $('result-title').textContent = RESULT_TITLE[r.reason];
    $('result-score').textContent = r.score.toLocaleString('ko-KR');
    $('result-time').textContent = formatTime(r.elapsed);
    $('result-best').textContent = r.best.toLocaleString('ko-KR');
    $('result-streak').textContent = `${r.maxStreak.toFixed(1)}초`;
    $('result-new-best').hidden = !r.isNewBest;
    $('storage-note').hidden = !r.storageFailed;
    this.setBest(r.best);
    this.show('result');
  }

  setSound(volume: number, muted: boolean): void {
    this.volume.value = String(Math.round(volume * 100));
    this.muteBtn.textContent = muted ? '소리 꺼짐' : '소리 켜짐';
    this.muteBtn.setAttribute('aria-pressed', String(muted));
  }

  /** 터치 버튼 배경에 아이콘 그림 적용 (없으면 글자만) */
  setTouchIcons(danceSrc: string | null, breadSrc: string | null): void {
    if (danceSrc) this.danceBtn.style.backgroundImage = `url("${danceSrc}")`;
    if (breadSrc) this.breadBtn.style.backgroundImage = `url("${breadSrc}")`;
  }
}
