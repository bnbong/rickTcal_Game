// 정지 포즈 1장으로 만드는 절차적 춤·숨쉬기 애니메이션 (사양서 §7)
import { RENDER_CONFIG } from '../config';

export interface PoseTransform {
  flipX: boolean;
  scaleX: number;
  scaleY: number;
  /** 라디안 */
  rot: number;
  dx: number;
  dy: number;
}

export const IDENTITY_POSE: PoseTransform = { flipX: false, scaleX: 1, scaleY: 1, rot: 0, dx: 0, dy: 0 };

const DEG = Math.PI / 180;

/** 4틱 주기 프레임 시퀀스 */
const SEQUENCE: ReadonlyArray<Pick<PoseTransform, 'flipX' | 'scaleY' | 'rot'>> = [
  { flipX: false, scaleY: 1, rot: 0 },
  { flipX: true, scaleY: 1, rot: 0 },
  { flipX: false, scaleY: 0.92, rot: 8 * DEG },
  { flipX: true, scaleY: 1.06, rot: -8 * DEG },
];

/** 경과 시간에 따른 춤 틱 fps (6→14) */
export function danceFps(elapsed: number): number {
  const c = RENDER_CONFIG;
  return c.danceFpsBase + (Math.min(Math.max(elapsed, 0), c.danceRampTime) / c.danceRampTime) * c.danceFpsBoost;
}

export function isAwakened(elapsed: number): boolean {
  return elapsed >= RENDER_CONFIG.awakenTime;
}

/**
 * 춤 변형. tickPhase는 누적 틱 수(dt*fps를 더해 간다), phaseOffset은 주기(4틱) 대비 비율.
 * 죠안은 phaseOffset 0.5로 에르핀과 엇갈리게 움직인다.
 */
export function danceTransform(tickPhase: number, phaseOffset: number, awakened: boolean): PoseTransform {
  const c = RENDER_CONFIG;
  const amp = awakened ? c.awakenAmpMul : 1;
  const t = tickPhase + phaseOffset * SEQUENCE.length;
  const idx = ((Math.floor(t) % SEQUENCE.length) + SEQUENCE.length) % SEQUENCE.length;
  const f = SEQUENCE[idx];
  // 2틱마다 한 번 튀어 오르는 바운스 + 좌우 미세 흔들림
  const dy = -Math.abs(Math.sin((t * Math.PI) / 2)) * c.bounceAmp * amp;
  const dx = Math.sin(t * Math.PI * 0.65) * c.swayAmp * amp;
  return {
    flipX: f.flipX,
    scaleX: 1,
    scaleY: 1 + (f.scaleY - 1) * amp,
    rot: f.rot * amp,
    dx,
    dy,
  };
}

/** 대기 숨쉬기: scaleY ±1.5%, 1.2초 주기 */
export function idleTransform(time: number, phaseOffset = 0): PoseTransform {
  const c = RENDER_CONFIG;
  const s = Math.sin(((time / c.idleBreathPeriod) + phaseOffset) * Math.PI * 2);
  return { ...IDENTITY_POSE, scaleY: 1 + s * c.idleBreathAmp, scaleX: 1 - s * c.idleBreathAmp * 0.3 };
}
