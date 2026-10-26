// 순수 게임 시뮬레이션: DOM 의존 없음, 주입된 Rng만 사용하는 결정론적 step
import type { GameConfig, Range } from '../config';
import type { GameInput, GameState, Rng, SherumPhase } from './types';

export type {
  GameInput,
  GameResult,
  GameState,
  JoanneDisplay,
  Rng,
  SherumPhase,
  SimEvent,
  EndReason,
} from './types';

const EPS = 1e-9;
/** 한 step 안에서 경계를 잘라 처리할 최대 구간 수. 넘으면 남은 dt는 한 번에 처리한다 (무한 루프 방지) */
const MAX_SEGMENTS = 32;

const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

export function isSafePhase(phase: SherumPhase): boolean {
  return phase === 'left_safe' || phase === 'turning_right';
}

/** 콤보 배율: 1 + min(streak, 상한) * step (기본 최대 1.5) */
export function comboMultiplier(streak: number, config: GameConfig): number {
  return 1 + Math.min(Math.max(streak, 0), config.comboMaxStreak) * config.comboStep;
}

/** streak s0에서 len초 동안 배율을 적분한 값 (fps 무관 점수 계산용) */
function comboIntegral(s0: number, len: number, config: GameConfig): number {
  const cap = config.comboMaxStreak;
  const f = (s: number): number => (s <= cap ? (s * s) / 2 : (cap * cap) / 2 + cap * (s - cap));
  return len + config.comboStep * (f(s0 + len) - f(s0));
}

/** elapsed 기준 난이도 범위 보간 (rampTime 이후 고정) */
export function rangeAt(start: Range, end: Range, elapsed: number, rampTime: number): [number, number] {
  const t = rampTime > 0 ? clamp(elapsed / rampTime, 0, 1) : 1;
  return [start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t];
}

/** elapsed 기준 스칼라 보간 (rangeAt과 같은 규칙, rampTime 이후 고정) */
export function lerpAt(start: number, end: number, elapsed: number, rampTime: number): number {
  const t = rampTime > 0 ? clamp(elapsed / rampTime, 0, 1) : 1;
  return start + (end - start) * t;
}

/** 단계 진입 시 지속 시간 결정. 랜덤 구간은 rng.next()를 정확히 1회 호출 */
function phaseDurationFor(phase: SherumPhase, elapsed: number, cfg: GameConfig, rng: Rng): number {
  switch (phase) {
    case 'left_safe': {
      const [lo, hi] = rangeAt(cfg.safeDurationStart, cfg.safeDurationEnd, elapsed, cfg.difficultyRampTime);
      return lo + (hi - lo) * rng.next();
    }
    case 'turning_right':
      return lerpAt(cfg.warnDurationStart, cfg.warnDurationEnd, elapsed, cfg.difficultyRampTime);
    case 'right_watching': {
      const [lo, hi] = rangeAt(cfg.watchDurationStart, cfg.watchDurationEnd, elapsed, cfg.difficultyRampTime);
      return lo + (hi - lo) * rng.next();
    }
    case 'turning_left':
      return cfg.turnBackDuration;
  }
}

export function createGame(config: GameConfig, rng: Rng): GameState {
  return {
    config,
    rng,
    mode: 'playing',
    elapsed: 0,
    score: 0,
    gauge: clamp(config.gaugeStart, 0, config.gaugeMax),
    breadLeft: config.breadCount,
    streak: 0,
    maxStreak: 0,
    sherum: {
      phase: 'left_safe',
      timer: 0,
      phaseDuration: phaseDurationFor('left_safe', 0, config, rng),
      cycle: 0,
    },
    erpin: { dancing: false, eating: 0, caught: false },
    joanne: { display: 'idle', shockedLinger: 0, offering: 0 },
    caughtTimer: 0,
    events: [],
  };
}

function enterNextPhase(state: GameState): void {
  const sh = state.sherum;
  const next: Record<SherumPhase, SherumPhase> = {
    left_safe: 'turning_right',
    turning_right: 'right_watching',
    right_watching: 'turning_left',
    turning_left: 'left_safe',
  };
  sh.phase = next[sh.phase];
  sh.timer = 0;
  sh.phaseDuration = phaseDurationFor(sh.phase, state.elapsed, state.config, state.rng);
  if (sh.phase === 'turning_right') state.events.push('sherum_warn');
  else if (sh.phase === 'right_watching') state.events.push('sherum_watch');
  else if (sh.phase === 'left_safe') {
    // 칠판으로 완전히 돌아선 순간: 다시 춤춰도 된다는 신호
    sh.cycle += 1;
    state.events.push('sherum_back');
  }
}

function advanceTime(state: GameState, t: number): void {
  const join = state.config.joanneJoinTime;
  const prev = state.elapsed;
  state.elapsed += t;
  state.sherum.timer += t;
  if (prev < join && state.elapsed >= join) state.events.push('joanne_join');
}

function finish(state: GameState, reason: 'caught' | 'bored'): void {
  state.result = {
    reason,
    score: Math.round(state.score),
    elapsed: state.elapsed,
    maxStreak: state.maxStreak,
  };
  state.events.push(reason);
  if (reason === 'caught') {
    state.mode = 'caught';
    state.caughtTimer = state.config.caughtFreeze;
    state.erpin.caught = true;
    state.erpin.dancing = false;
  } else {
    state.mode = 'over';
    state.erpin.dancing = false;
  }
}

function updateJoanne(state: GameState, dt: number): void {
  const cfg = state.config;
  const j = state.joanne;
  let base: 'idle' | 'shocked' | 'dancing';
  if (state.elapsed < cfg.joanneJoinTime) {
    if (state.erpin.dancing) {
      base = 'shocked';
      j.shockedLinger = cfg.shockedLinger;
    } else if (j.shockedLinger > 0) {
      j.shockedLinger = Math.max(0, j.shockedLinger - dt);
      base = j.shockedLinger > 0 ? 'shocked' : 'idle';
    } else {
      base = 'idle';
    }
  } else {
    // 합류 이후: 셰럼이 칠판을 보는 동안에만 함께 춤추고, 예고가 뜨면 먼저 멈춘다
    j.shockedLinger = 0;
    base = state.erpin.dancing && state.sherum.phase === 'left_safe' ? 'dancing' : 'idle';
  }
  j.display = j.offering > 0 ? 'bread' : base;
}

/**
 * dt초만큼 진행. state를 제자리에서 갱신하고 반환한다.
 * 단계 전환·grace 경계·게이지 고갈 시점에서 구간을 잘라 계산하므로 fps와 무관하게 같은 결과가 나온다.
 */
export function step(state: GameState, input: GameInput, rawDt: number): GameState {
  state.events = [];
  const cfg = state.config;
  const dt = Number.isFinite(rawDt) ? clamp(rawDt, 0, cfg.maxDt) : 0;
  if (dt <= 0 || state.mode === 'over') return state;

  if (state.mode === 'caught') {
    // 들킴 연출 중: 입력 무시
    state.caughtTimer -= dt;
    if (state.caughtTimer <= 0) {
      state.caughtTimer = 0;
      state.mode = 'over';
    }
    return state;
  }

  const erpin = state.erpin;
  const joanne = state.joanne;

  // 종료 판정이 게이지 증가(빵·춤)보다 먼저: 이미 0이면 이번 step의 회복으로 살아나지 않는다
  if (state.gauge <= 0) {
    state.gauge = 0;
    finish(state, 'bored');
    updateJoanne(state, dt);
    return state;
  }

  // 빵: 먹는 동안에도 춤 판정은 그대로 (무적 아님)
  if (input.breadPressed) {
    if (state.breadLeft > 0) {
      state.breadLeft -= 1;
      state.gauge = Math.min(cfg.gaugeMax, state.gauge + cfg.breadHeal);
      erpin.eating = cfg.eatDuration;
      joanne.offering = cfg.offeringDuration;
      state.events.push('bread');
    } else {
      state.events.push('bread_empty');
    }
  }
  // 타이머 감소는 설정 뒤에: 이번 프레임 dt만큼 바로 깎여 fps와 무관하게 누른 시각 + duration에 끝난다
  // 부동소수 잔차(예: 0.8 - 24/30 ≈ 1e-16)로 한 프레임 더 남지 않도록 EPS 이하는 0으로 본다
  erpin.eating = erpin.eating - dt > EPS ? erpin.eating - dt : 0;
  joanne.offering = joanne.offering - dt > EPS ? joanne.offering - dt : 0;

  const dancing = input.dance;
  if (dancing && !erpin.dancing) state.events.push('dance_start');
  else if (!dancing && erpin.dancing) state.events.push('dance_stop');
  erpin.dancing = dancing;
  if (!dancing) state.streak = 0;

  let remaining = dt;
  for (let i = 0; remaining > EPS && state.mode === 'playing'; i++) {
    const sh = state.sherum;
    const watching = sh.phase === 'right_watching';
    if (watching && dancing && sh.timer >= cfg.graceDuration - EPS) {
      finish(state, 'caught');
      break;
    }

    let seg: number;
    if (i >= MAX_SEGMENTS - 1) {
      // 상한 도달: 남은 시간을 버리지 않고 경계(단계·grace) 무시하고 한 번에 처리
      seg = remaining;
    } else {
      seg = Math.min(remaining, Math.max(0, sh.phaseDuration - sh.timer));
      if (watching && dancing) seg = Math.min(seg, cfg.graceDuration - sh.timer);
    }

    if (dancing) {
      if (isSafePhase(sh.phase)) {
        state.score += cfg.scoreRate * comboIntegral(state.streak, seg, cfg);
        state.streak += seg;
        state.maxStreak = Math.max(state.maxStreak, state.streak);
        state.gauge = Math.min(cfg.gaugeMax, state.gauge + cfg.gaugeGainPerSec * seg);
      }
      // 안전하지 않은 구간에서 춤: 점수·게이지 변화 없음
    } else {
      const drain = cfg.gaugeDrainPerSec * seg;
      if (drain >= state.gauge) {
        // 정확한 고갈 시각까지만 진행
        advanceTime(state, cfg.gaugeDrainPerSec > 0 ? state.gauge / cfg.gaugeDrainPerSec : 0);
        state.gauge = 0;
        finish(state, 'bored');
        break;
      }
      state.gauge -= drain;
    }

    advanceTime(state, seg);
    remaining = seg >= remaining ? 0 : remaining - seg;
    if (sh.timer >= sh.phaseDuration - EPS) enterNextPhase(state);
  }

  updateJoanne(state, dt);
  return state;
}

/** 테스트·게임 공용 시드 난수 (mulberry32) */
export function createRng(seed: number): Rng {
  let a = seed >>> 0;
  return {
    next(): number {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    },
  };
}
