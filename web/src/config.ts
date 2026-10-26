// 모든 튜닝 수치 (사양서 §4). 다른 모듈은 여기 값만 참조한다
export type Range = readonly [number, number];

export interface GameConfig {
  scoreRate: number;
  gaugeGainPerSec: number;
  gaugeDrainPerSec: number;
  gaugeMax: number;
  gaugeStart: number;
  breadCount: number;
  breadHeal: number;
  eatDuration: number;
  offeringDuration: number;
  /** 회전 예고 길이: elapsed 0초 → rampTime초 사이 선형 보간 */
  warnDurationStart: number;
  warnDurationEnd: number;
  graceDuration: number;
  turnBackDuration: number;
  /** 난이도 보간: elapsed 0초 → rampTime초 사이 선형, 이후 고정 */
  difficultyRampTime: number;
  safeDurationStart: Range;
  safeDurationEnd: Range;
  watchDurationStart: Range;
  watchDurationEnd: Range;
  joanneJoinTime: number;
  shockedLinger: number;
  caughtFreeze: number;
  /** 콤보: 배율 = 1 + min(streak, comboMaxStreak) * comboStep */
  comboStep: number;
  comboMaxStreak: number;
  maxDt: number;
}

export const DEFAULT_CONFIG: GameConfig = {
  scoreRate: 100,
  gaugeGainPerSec: 14,
  gaugeDrainPerSec: 9,
  gaugeMax: 100,
  gaugeStart: 100,
  breadCount: 2,
  breadHeal: 35,
  eatDuration: 0.8,
  offeringDuration: 0.8,
  warnDurationStart: 0.5,
  warnDurationEnd: 0.25,
  graceDuration: 0.15,
  turnBackDuration: 0.3,
  difficultyRampTime: 120,
  safeDurationStart: [2.5, 4.5],
  safeDurationEnd: [1.2, 2.5],
  watchDurationStart: [1.5, 3.0],
  watchDurationEnd: [2.5, 4.0],
  joanneJoinTime: 60,
  shockedLinger: 1.0,
  caughtFreeze: 1.2,
  comboStep: 0.05,
  comboMaxStreak: 10,
  maxDt: 0.1,
};

/** 렌더 전용 연출 수치 */
export const RENDER_CONFIG = {
  /** 춤 틱 fps = base + min(elapsed, rampTime)/rampTime * boost (6→14fps) */
  danceFpsBase: 6,
  danceFpsBoost: 8,
  danceRampTime: 120,
  /** 이 시각 이후 '각성': 흔들림 진폭 배율 + 노란 번쩍 */
  awakenTime: 90,
  awakenAmpMul: 1.5,
  bounceAmp: 10,
  swayAmp: 6,
  idleBreathAmp: 0.015,
  idleBreathPeriod: 1.2,
  caughtShakeDuration: 0.3,
  caughtShakeAmp: 12,
};
