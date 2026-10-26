// Canvas 2D 렌더러: 1280×720 논리 좌표, DPR 반영 letterbox, 사양서 §6 그리기 순서
import { RENDER_CONFIG } from '../config';
import { comboMultiplier } from '../game/sim';
import type { GameState, SimEvent } from '../game/types';
import { danceFps, danceTransform, IDENTITY_POSE, idleTransform, isAwakened, type PoseTransform } from './dance';
import { CHARACTER_POSES, FALLBACK_SPRITES, LAYOUT, LOGICAL_H, LOGICAL_W, POSE_ANCHOR_X, type CharacterSlot } from './layout';
import { spriteSize, type SpriteBank } from './sprites';

export const FONT_STACK = "'Jua', 'Gaegu', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif";

type CharacterName = keyof typeof CHARACTER_POSES;

/** 각성 번쩍임 주기: 춤 틱 4회(한 사이클)마다 한 번 */
const FLASH_EVERY_TICKS = 4;

interface Popup {
  text: string;
  x: number;
  y: number;
  t: number;
  color: string;
}

export class Renderer {
  private readonly ctx: CanvasRenderingContext2D;
  private bank: SpriteBank;
  private charScale = new Map<CharacterName, number>();

  // 연출 시계 (렌더 전용, sim과 무관)
  private time = 0;
  private erpinTick = 0;
  private joanneTick = 0;
  private shake = 0;
  private flash = 0;
  private darken = 0;
  private popups: Popup[] = [];

  constructor(
    private readonly canvas: HTMLCanvasElement,
    bank: SpriteBank,
  ) {
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D를 사용할 수 없습니다');
    this.ctx = ctx;
    this.bank = bank;
    this.resize();
  }

  setBank(bank: SpriteBank): void {
    this.bank = bank;
    this.charScale.clear();
  }

  /** 캔버스 백버퍼를 CSS 크기 × DPR로 맞춘다 */
  resize(): void {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const w = Math.max(1, Math.round(rect.width * dpr));
    const h = Math.max(1, Math.round(rect.height * dpr));
    if (this.canvas.width !== w) this.canvas.width = w;
    if (this.canvas.height !== h) this.canvas.height = h;
  }

  /** 새 판 시작 시 연출 상태 초기화 */
  reset(): void {
    this.erpinTick = 0;
    this.joanneTick = 0;
    this.shake = 0;
    this.flash = 0;
    this.darken = 0;
    this.popups = [];
  }

  /** sim 이벤트로 시작되는 일회성 연출 */
  handleEvents(events: readonly SimEvent[]): void {
    for (const e of events) {
      if (e === 'caught') this.shake = RENDER_CONFIG.caughtShakeDuration;
      else if (e === 'bread') this.popups.push({ text: '흥 회복!', x: LAYOUT.erpin.footX, y: 200, t: 0, color: '#ffffff' });
      else if (e === 'joanne_join') this.popups.push({ text: '죠안도 신났다!', x: LAYOUT.joanne.footX, y: 170, t: 0, color: '#fff6a8' });
    }
  }

  /** 애니메이션 시계 진행. 일시정지 중엔 dt=0 */
  update(state: GameState, dt: number): void {
    this.time += dt;
    const awakened = isAwakened(state.elapsed);
    const fps = danceFps(state.elapsed);
    const erpinDancing = state.erpin.dancing && !state.erpin.caught && state.erpin.eating <= 0;
    if (erpinDancing) {
      const prev = Math.floor(this.erpinTick);
      this.erpinTick += dt * fps;
      // 각성 번쩍임: 틱마다 리셋하면 상시 글로우처럼 보이므로 춤 한 사이클(4틱)마다 한 번만 트리거
      const tick = Math.floor(this.erpinTick);
      if (awakened && Math.floor(tick / FLASH_EVERY_TICKS) !== Math.floor(prev / FLASH_EVERY_TICKS)) {
        this.flash = 1;
      }
    } else {
      this.erpinTick = 0;
    }
    if (state.joanne.display === 'dancing') this.joanneTick += dt * fps;
    else this.joanneTick = 0;

    this.shake = Math.max(0, this.shake - dt);
    this.flash = Math.max(0, this.flash - dt * 5);
    const caught = state.result?.reason === 'caught';
    const target = caught ? 1 : 0;
    this.darken += (target - this.darken) * Math.min(1, dt * 8);
    for (const p of this.popups) p.t += dt;
    this.popups = this.popups.filter((p) => p.t < 1.4);
  }

  draw(state: GameState, showHud: boolean): void {
    const { ctx, canvas } = this;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#10142a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // letterbox: 비율이 어긋나도 1280×720이 잘리지 않게 가운데 맞춤
    const k = Math.min(canvas.width / LOGICAL_W, canvas.height / LOGICAL_H);
    const ox = (canvas.width - LOGICAL_W * k) / 2;
    const oy = (canvas.height - LOGICAL_H * k) / 2;
    ctx.setTransform(k, 0, 0, k, ox, oy);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, LOGICAL_W, LOGICAL_H);
    ctx.clip();

    ctx.save();
    if (this.shake > 0) {
      const a = RENDER_CONFIG.caughtShakeAmp * (this.shake / RENDER_CONFIG.caughtShakeDuration);
      ctx.translate(Math.sin(this.time * 90) * a, Math.cos(this.time * 77) * a * 0.6);
    }
    this.drawBackground();
    if (this.darken > 0.01) {
      ctx.fillStyle = `rgba(16, 18, 40, ${0.28 * this.darken})`;
      ctx.fillRect(-40, -40, LOGICAL_W + 80, LOGICAL_H + 80);
    }
    this.drawJoanne(state);
    this.drawErpin(state);
    this.drawDeskLong(state);
    this.drawSherum(state);
    this.drawSmallDesk();
    ctx.restore();

    if (showHud) this.drawHud(state);
    this.drawEffects(state);
    ctx.restore();
  }

  // ---------- 장면 ----------

  private drawBackground(): void {
    const { ctx } = this;
    const bg = this.bank.background;
    if (bg) {
      ctx.drawImage(bg, 0, 0, LOGICAL_W, LOGICAL_H);
      return;
    }
    const sky = ctx.createLinearGradient(0, 0, 0, 420);
    sky.addColorStop(0, '#5fb8f0');
    sky.addColorStop(1, '#a9dcf7');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, LOGICAL_W, LOGICAL_H);
    ctx.fillStyle = '#7cc66a';
    ctx.fillRect(0, 420, LOGICAL_W, LOGICAL_H - 420);
    this.placeholderLabel('background', 640, 380);
  }

  private scaleFor(name: CharacterName, slot: CharacterSlot): number {
    let s = this.charScale.get(name);
    if (s === undefined) {
      const maxH = Math.max(...CHARACTER_POSES[name].map((k) => spriteSize(this.bank, k).h));
      s = slot.height / maxH;
      this.charScale.set(name, s);
    }
    return s;
  }

  private drawJoanne(state: GameState): void {
    const slot = LAYOUT.joanne;
    const scale = this.scaleFor('joanne', slot);
    const awakened = isAwakened(state.elapsed);
    let key: string;
    let tf: PoseTransform;
    switch (state.joanne.display) {
      case 'dancing':
        key = 'joanne_dance';
        tf = danceTransform(this.joanneTick, 0.5, awakened);
        break;
      case 'shocked':
        key = 'joanne_shocked';
        tf = { ...IDENTITY_POSE, dx: Math.sin(this.time * 55) * 1.5 };
        break;
      case 'bread':
        key = 'joanne_bread';
        tf = idleTransform(this.time, 0.3);
        break;
      default:
        key = 'joanne_idle';
        tf = idleTransform(this.time, 0.3);
    }
    this.drawCharacter(key, slot, scale, tf);
  }

  private drawErpin(state: GameState): void {
    const slot = LAYOUT.erpin;
    const scale = this.scaleFor('erpin', slot);
    let key: string;
    let tf: PoseTransform;
    // 표시 우선순위: caught > eating > dancing > idle
    if (state.erpin.caught) {
      key = 'erpin_caught';
      tf = IDENTITY_POSE;
    } else if (state.erpin.eating > 0) {
      key = 'erpin_eat';
      tf = { ...IDENTITY_POSE, scaleY: 1 + Math.sin(this.time * Math.PI * 8) * 0.02 };
    } else if (state.erpin.dancing) {
      key = 'erpin_dance';
      tf = danceTransform(this.erpinTick, 0, isAwakened(state.elapsed));
    } else {
      key = 'erpin_idle';
      tf = idleTransform(this.time);
    }
    this.drawCharacter(key, slot, scale, tf);
  }

  private drawDeskLong(state: GameState): void {
    const d = LAYOUT.deskLong;
    const size = spriteSize(this.bank, 'desk_long');
    this.drawSpriteRect('desk_long', d.x, d.y, d.w, (d.w * size.h) / size.w);
    for (let i = 0; i < Math.min(state.breadLeft, LAYOUT.breadPlates.length); i++) {
      const p = LAYOUT.breadPlates[i];
      this.drawSpriteFoot('bread_plate', p.cx, p.footY, p.w);
    }
  }

  private drawSherum(state: GameState): void {
    const slot = LAYOUT.sherum;
    const scale = this.scaleFor('sherum', slot);
    const phase = state.sherum.phase;
    let key = 'sherum_safe';
    if (state.erpin.caught || phase === 'right_watching') key = 'sherum_watching';
    else if (phase === 'turning_right' || phase === 'turning_left') key = 'sherum_turning';
    let tf = idleTransform(this.time, 0.6);
    if (phase === 'turning_right' && !state.erpin.caught) {
      // 예고: 살짝 바운스
      tf = { ...IDENTITY_POSE, dy: -Math.abs(Math.sin(state.sherum.timer * Math.PI * 6)) * 8 };
    }
    // 작은 책상 윗면 아래를 잘라 다리 사이로 긴 머리카락이 비치지 않게 한다.
    // clip은 셰럼 자체 변형(예고 바운스 등) 전에, 책상과 같은 장면 좌표계에서 건다:
    // 들킴 흔들림은 책상과 함께 움직여야 경계가 책상에 붙어 있고, 셰럼 바운스엔 경계가 따라가지 않는다.
    const { ctx } = this;
    ctx.save();
    ctx.beginPath();
    ctx.rect(-LOGICAL_W, -LOGICAL_H, LOGICAL_W * 3, LAYOUT.deskSmallTopBottomY + LAYOUT.sherumClipPad + LOGICAL_H);
    ctx.clip();
    this.drawCharacter(key, slot, scale, tf);
    ctx.restore();
  }

  private drawSmallDesk(): void {
    const d = LAYOUT.deskSmall;
    const size = spriteSize(this.bank, 'desk_small');
    this.drawSpriteRect('desk_small', d.x, d.y, d.w, (d.w * size.h) / size.w);
    // 잉크병이 종이보다 뒤쪽(footY가 작음)이라 먼저 그린다
    this.drawSpriteFoot('ink', LAYOUT.ink.cx, LAYOUT.ink.footY, LAYOUT.ink.w);
    this.drawSpriteFoot('papers', LAYOUT.papers.cx, LAYOUT.papers.footY, LAYOUT.papers.w);
  }

  // ---------- HUD ----------

  private drawHud(state: GameState): void {
    const { ctx } = this;
    const hud = LAYOUT.hud;

    // 빵 아이콘 × 남은 수
    const bi = hud.breadIcon;
    const biSize = spriteSize(this.bank, 'ui_bread_icon');
    const biW = (bi.size * biSize.w) / biSize.h;
    ctx.save();
    if (state.breadLeft === 0) ctx.globalAlpha = 0.45;
    this.drawSpriteRect('ui_bread_icon', bi.x, bi.y, biW, bi.size);
    ctx.restore();
    this.text(`×${state.breadLeft}`, bi.x + biW + 8, bi.y + bi.size / 2, 34, 'left');

    // 흥 게이지: 프레임(불투명 크림 트랙)을 먼저 그리고 그 위에 채움
    const g = hud.gauge;
    const fSize = spriteSize(this.bank, 'ui_gauge_frame');
    const fw = g.w;
    const fh = (g.w * fSize.h) / fSize.w;
    const fx = g.cx - fw / 2;
    const fy = g.y;
    const frameImg = this.bank.images.get('ui_gauge_frame');
    const gm = this.bank.manifest?.gauge;
    let fill: { x: number; y: number; w: number; h: number };
    if (frameImg && gm && gm.fillRect.w > 0) {
      ctx.drawImage(frameImg, fx, fy, fw, fh);
      const s = fw / fSize.w;
      fill = { x: fx + gm.fillRect.x * s, y: fy + gm.fillRect.y * s, w: gm.fillRect.w * s, h: gm.fillRect.h * s };
    } else {
      this.drawSpriteRect('ui_gauge_frame', fx, fy, fw, fh);
      fill = { x: fx + fw * 0.09, y: fy + fh * 0.32, w: fw * 0.82, h: fh * 0.36 };
      ctx.fillStyle = gm?.trackColor ?? '#fbf4dc';
      this.roundRect(fill.x, fill.y, fill.w, fill.h, fill.h / 2);
      ctx.fill();
    }
    const ratio = Math.max(0, Math.min(1, state.gauge / state.config.gaugeMax));
    const fillW = fill.w * ratio;
    if (fillW > 0.5) {
      const low = ratio < 0.25 && Math.sin(this.time * 12) > 0;
      ctx.fillStyle = low ? '#f2885a' : gm?.fillColor ?? '#8bd36a';
      this.roundRect(fill.x, fill.y, fillW, fill.h, Math.min(fill.h / 2, fillW / 2));
      ctx.fill();
    }
    this.text('흥', fx - 6, fy + fh / 2, 30, 'right');

    // 점수 라벨 + 경과 시간
    const lb = hud.label;
    const lSize = spriteSize(this.bank, 'ui_label');
    const lh = (lb.w * lSize.h) / lSize.w;
    const lx = lb.right - lb.w;
    this.drawSpriteRect('ui_label', lx, lb.y, lb.w, lh);
    this.text(Math.round(state.score).toLocaleString('ko-KR'), lx + lb.w / 2, lb.y + lh / 2 + 1, 36, 'center', '#4a2a1a', '#fbf4dc');
    const sec = Math.floor(state.elapsed);
    const time = `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
    const mult = comboMultiplier(state.streak, state.config);
    const sub = mult >= 1.05 && state.mode === 'playing' ? `${time}  콤보 ×${mult.toFixed(2)}` : time;
    this.text(sub, lx + lb.w / 2, lb.y + lh + 18, 24, 'center');

    // 일시정지 아이콘 (클릭 영역은 HTML 버튼이 담당)
    const pz = hud.pause;
    const pSize = spriteSize(this.bank, 'ui_pause_icon');
    this.drawSpriteRect('ui_pause_icon', pz.x, pz.y, (pz.size * pSize.w) / pSize.h, pz.size);
  }

  // ---------- 이펙트 ----------

  private drawEffects(state: GameState): void {
    const { ctx } = this;
    // 셰럼 예고 느낌표 말풍선
    if (state.mode === 'playing' && state.sherum.phase === 'turning_right') {
      const slot = LAYOUT.sherum;
      const b = LAYOUT.warnBubble;
      const headY = slot.footY - slot.height;
      const pop = Math.min(1, state.sherum.timer / 0.08);
      this.drawWarnBubble(slot.footX + b.dx, headY + b.dy, b.r * (0.6 + 0.4 * pop));
    }

    // 각성: 춤 틱마다 노란 번쩍
    if (this.flash > 0 && state.erpin.dancing && isAwakened(state.elapsed)) {
      const cx = LAYOUT.erpin.footX;
      const cy = LAYOUT.erpin.footY - LAYOUT.erpin.height * 0.5;
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, 260);
      grad.addColorStop(0, `rgba(255, 236, 120, ${0.45 * this.flash})`);
      grad.addColorStop(1, 'rgba(255, 236, 120, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(cx - 260, cy - 260, 520, 520);
      ctx.fillStyle = `rgba(255, 240, 150, ${0.07 * this.flash})`;
      ctx.fillRect(0, 0, LOGICAL_W, LOGICAL_H);
      ctx.restore();
      // 주변 반짝이
      ctx.save();
      ctx.fillStyle = `rgba(255, 214, 64, ${0.9 * this.flash})`;
      for (let i = 0; i < 6; i++) {
        const a = this.time * 2 + (i * Math.PI) / 3;
        this.star(cx + Math.cos(a) * 190, cy + Math.sin(a) * 150, 12 + 6 * this.flash);
      }
      ctx.restore();
    }

    for (const p of this.popups) {
      const a = 1 - p.t / 1.4;
      ctx.save();
      ctx.globalAlpha = a;
      this.text(p.text, p.x, p.y - p.t * 40, 32, 'center', p.color);
      ctx.restore();
    }
  }

  private drawWarnBubble(x: number, y: number, r: number): void {
    const { ctx } = this;
    ctx.save();
    ctx.lineWidth = 5;
    ctx.strokeStyle = '#2b2350';
    ctx.fillStyle = '#fffaf0';
    ctx.beginPath();
    ctx.ellipse(x, y, r, r * 0.9, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    // 꼬리 (셰럼 머리 쪽 왼쪽 아래)
    ctx.beginPath();
    ctx.moveTo(x - r * 0.55, y + r * 0.6);
    ctx.lineTo(x - r * 1.05, y + r * 1.25);
    ctx.lineTo(x - r * 0.15, y + r * 0.85);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(x, y, r - 2.5, r * 0.9 - 2.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#e8463c';
    ctx.font = `${Math.round(r * 1.5)}px ${FONT_STACK}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('!', x, y + r * 0.05);
    ctx.restore();
  }

  // ---------- 그리기 도우미 ----------

  /**
   * 발 기준 캐릭터 그리기. 회전·스케일·flipX 축은 포즈별 몸 중심(POSE_ANCHOR_X)이라
   * 포즈 전환·좌우 반전 때 몸이 footX에서 튀지 않는다. 플레이스홀더는 bbox 중앙 기준.
   */
  private drawCharacter(key: string, slot: CharacterSlot, scale: number, tf: PoseTransform): void {
    const { ctx } = this;
    const size = spriteSize(this.bank, key);
    const anchorX = this.bank.images.has(key) ? POSE_ANCHOR_X[key] ?? size.anchorX : size.anchorX;
    const w = size.w * scale;
    const h = size.h * scale;
    ctx.save();
    ctx.translate(slot.footX + tf.dx, slot.footY + tf.dy);
    // scaleY는 발 기준으로 적용해 바닥이 뜨지 않게
    ctx.scale(1, tf.scaleY);
    ctx.translate(0, -h / 2);
    ctx.rotate(tf.rot);
    ctx.scale((tf.flipX ? -1 : 1) * tf.scaleX, 1);
    this.drawImageOrPlaceholder(key, -w * anchorX, -h * size.anchorY + h / 2, w, h);
    ctx.restore();
  }

  /** 바닥 중앙 기준, 폭 지정 */
  private drawSpriteFoot(key: string, cx: number, footY: number, w: number): void {
    const size = spriteSize(this.bank, key);
    const h = (w * size.h) / size.w;
    this.drawSpriteRect(key, cx - w * size.anchorX, footY - h * size.anchorY, w, h);
  }

  private drawSpriteRect(key: string, x: number, y: number, w: number, h: number): void {
    this.drawImageOrPlaceholder(key, x, y, w, h);
  }

  private drawImageOrPlaceholder(key: string, x: number, y: number, w: number, h: number): void {
    const img = this.bank.images.get(key);
    if (img) {
      this.ctx.drawImage(img, x, y, w, h);
      return;
    }
    const { ctx } = this;
    ctx.save();
    ctx.fillStyle = FALLBACK_SPRITES[key]?.color ?? '#cc66cc';
    ctx.globalAlpha = 0.85;
    this.roundRect(x, y, w, h, Math.min(16, w / 4, h / 4));
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#2b2350';
    ctx.stroke();
    ctx.restore();
    this.placeholderLabel(key, x + w / 2, y + h / 2, Math.max(10, Math.min(20, w / 8)));
  }

  private placeholderLabel(text: string, x: number, y: number, size = 20): void {
    const { ctx } = this;
    ctx.save();
    ctx.font = `${size}px monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 3;
    ctx.strokeText(text, x, y);
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  private text(
    str: string,
    x: number,
    y: number,
    size: number,
    align: CanvasTextAlign,
    fill = '#fffaf0',
    stroke = '#2b2350',
  ): void {
    const { ctx } = this;
    ctx.save();
    ctx.font = `${size}px ${FONT_STACK}`;
    ctx.textAlign = align;
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    ctx.lineWidth = Math.max(3, size / 6);
    ctx.strokeStyle = stroke;
    ctx.strokeText(str, x, y);
    ctx.fillStyle = fill;
    ctx.fillText(str, x, y);
    ctx.restore();
  }

  private roundRect(x: number, y: number, w: number, h: number, r: number): void {
    const { ctx } = this;
    const rr = Math.max(0, Math.min(r, w / 2, h / 2));
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.arcTo(x + w, y, x + w, y + h, rr);
    ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr);
    ctx.arcTo(x, y, x + w, y, rr);
    ctx.closePath();
  }

  private star(x: number, y: number, r: number): void {
    const { ctx } = this;
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4;
      const rad = i % 2 === 0 ? r : r * 0.35;
      ctx.lineTo(x + Math.cos(a) * rad, y + Math.sin(a) * rad);
    }
    ctx.closePath();
    ctx.fill();
  }
}
