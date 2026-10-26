// 키보드·터치·포커스 이벤트를 GameInput으로 모은다
import type { GameInput } from '../game/types';

export interface InputHandlers {
  /** 지금 플레이 화면인지 (Space/Enter의 의미가 달라진다) */
  isPlaying(): boolean;
  /** 타이틀·결과·일시정지 화면에서 Enter/Space */
  onConfirm(): void;
  /** P/Esc */
  onPause(): void;
  /** 탭이 숨겨짐 */
  onHidden(): void;
}

function isButtonTarget(t: EventTarget | null): boolean {
  return t instanceof HTMLElement && (t.tagName === 'BUTTON' || t.tagName === 'INPUT' || t.isContentEditable);
}

export class InputController {
  private keyDance = false;
  private pointerDance = false;
  /** 시작 직후 Space를 계속 누르고 있으면 뗄 때까지 춤으로 치지 않는다 */
  private suppressSpace = false;
  private breadQueued = false;
  private spaceDown = false;
  private activePointers = new Set<number>();

  constructor(private readonly handlers: InputHandlers) {
    window.addEventListener('keydown', this.onKeyDown, { capture: true });
    window.addEventListener('keyup', this.onKeyUp, { capture: true });
    window.addEventListener('blur', this.releaseAll);
    document.addEventListener('visibilitychange', this.onVisibility);
  }

  /** 이번 프레임 입력. breadPressed는 읽는 순간 소비된다 */
  poll(): GameInput {
    const bread = this.breadQueued;
    this.breadQueued = false;
    return { dance: this.keyDance || this.pointerDance, breadPressed: bread };
  }

  /**
   * 논리적 춤 입력 해제 (일시정지·게임오버·타이틀 복귀용).
   * 물리 키 상태 spaceDown은 건드리지 않는다: 여기서 지우면 Space를 누른 채 재개할 때
   * beginRound()가 '안 누름'으로 읽어 suppressSpace가 꺼지고, autorepeat keydown이 춤을 다시 켠다.
   */
  releaseDance(): void {
    this.keyDance = false;
    this.pointerDance = false;
    this.activePointers.clear();
    this.breadQueued = false;
  }

  /** 포커스 상실·탭 숨김: keyup을 못 받을 수 있으므로 물리 키 상태까지 전부 해제 */
  readonly releaseAll = (): void => {
    this.releaseDance();
    this.spaceDown = false;
  };

  /** 플레이 시작·재개 시: Space를 누른 채였다면 떼기 전까지 춤으로 치지 않는다 */
  beginRound(): void {
    this.releaseDance();
    this.suppressSpace = this.spaceDown;
  }

  /** 터치 춤/빵 버튼 연결 */
  bindTouchButtons(danceBtn: HTMLElement, breadBtn: HTMLElement): void {
    const release = (e: PointerEvent) => {
      this.activePointers.delete(e.pointerId);
      if (this.activePointers.size === 0) this.pointerDance = false;
    };
    danceBtn.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      if (!this.handlers.isPlaying()) return;
      try {
        danceBtn.setPointerCapture(e.pointerId);
      } catch {
        // 캡처 실패는 무시
      }
      this.activePointers.add(e.pointerId);
      this.pointerDance = true;
    });
    for (const type of ['pointerup', 'pointercancel', 'pointerleave', 'lostpointercapture'] as const) {
      danceBtn.addEventListener(type, release);
    }
    breadBtn.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      if (this.handlers.isPlaying()) this.breadQueued = true;
    });
    for (const el of [danceBtn, breadBtn]) {
      el.addEventListener('contextmenu', (e) => e.preventDefault());
    }
  }

  private readonly onKeyDown = (e: KeyboardEvent): void => {
    const playing = this.handlers.isPlaying();
    if (e.code === 'Space' || e.key === ' ') {
      this.spaceDown = true;
      if (playing) {
        e.preventDefault();
        // autorepeat(e.repeat)는 춤을 새로 켜지 않고 이미 켜진 상태만 유지한다.
        // 재개 직후 누른 채인 Space의 반복 입력이 춤으로 이어지는 것을 막는 이중 안전장치
        if (!this.suppressSpace && !e.repeat) this.keyDance = true;
      } else if (!isButtonTarget(e.target)) {
        e.preventDefault();
        if (!e.repeat) this.handlers.onConfirm();
      }
      return;
    }
    if (e.key === 'Enter') {
      if (!playing && !isButtonTarget(e.target)) {
        e.preventDefault();
        if (!e.repeat) this.handlers.onConfirm();
      }
      return;
    }
    if (e.code === 'KeyZ' || e.key === 'z' || e.key === 'Z') {
      if (playing && !e.repeat) {
        e.preventDefault();
        this.breadQueued = true;
      }
      return;
    }
    if (e.code === 'KeyP' || e.key === 'Escape') {
      if (!e.repeat) {
        e.preventDefault();
        this.handlers.onPause();
      }
    }
  };

  private readonly onKeyUp = (e: KeyboardEvent): void => {
    if (e.code === 'Space' || e.key === ' ') {
      this.keyDance = false;
      this.spaceDown = false;
      this.suppressSpace = false;
      if (this.handlers.isPlaying()) e.preventDefault();
    }
  };

  private readonly onVisibility = (): void => {
    if (document.visibilityState === 'hidden') {
      this.releaseAll();
      this.handlers.onHidden();
    }
  };
}
