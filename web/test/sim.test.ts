// sim.ts 규칙 테스트 (사양서 §9)
import { describe, expect, it } from 'vitest';
import { DEFAULT_CONFIG, type GameConfig } from '../src/config';
import {
  comboMultiplier,
  createGame,
  createRng,
  isSafePhase,
  step,
  type GameInput,
  type GameState,
  type SimEvent,
} from '../src/game/sim';

const IDLE: GameInput = { dance: false, breadPressed: false };
const DANCE: GameInput = { dance: true, breadPressed: false };

/** 조건이 참이 될 때까지 진행. 그동안 발생한 이벤트를 모아 돌려준다 */
function runUntil(
  s: GameState,
  pred: (s: GameState) => boolean,
  input: GameInput | ((s: GameState) => GameInput),
  dt = 1 / 60,
  maxTime = 600,
): SimEvent[] {
  const events: SimEvent[] = [];
  let t = 0;
  while (!pred(s)) {
    if (t > maxTime) throw new Error('runUntil timeout');
    step(s, typeof input === 'function' ? input(s) : input, dt);
    events.push(...s.events);
    t += dt;
  }
  return events;
}

/** 안전 구간(left_safe/turning_right)에서만 춤추는 봇 */
const safeBot = (s: GameState): GameInput => ({ dance: isSafePhase(s.sherum.phase), breadPressed: false });
/** 칠판 보기 구간에서만 춤추는 봇 */
const leftOnlyBot = (s: GameState): GameInput => ({ dance: s.sherum.phase === 'left_safe', breadPressed: false });

describe('fps 독립성', () => {
  it('60fps와 30fps의 점수 오차 <1%, 종료 시각 차 ≤0.05s', () => {
    const runPlan = (fps: number) => {
      const s = createGame(DEFAULT_CONFIG, createRng(1234));
      const dt = 1 / fps;
      const transitions: number[] = [];
      let lastPhase = s.sherum.phase;
      // 40초 동안 안전하게 춤춘 뒤 손을 놓아 지루함으로 종료
      while (s.mode === 'playing') {
        const input = s.elapsed < 40 ? safeBot(s) : IDLE;
        step(s, input, dt);
        if (s.sherum.phase !== lastPhase) {
          transitions.push(s.elapsed);
          lastPhase = s.sherum.phase;
        }
        if (s.elapsed < 40) expect(s.mode).toBe('playing');
      }
      return { s, transitions };
    };
    const a = runPlan(60);
    const b = runPlan(30);
    expect(a.s.result?.reason).toBe('bored');
    expect(b.s.result?.reason).toBe('bored');
    expect(a.s.score).toBeGreaterThan(0);
    expect(Math.abs(a.s.score - b.s.score) / a.s.score).toBeLessThan(0.01);
    expect(Math.abs(a.s.elapsed - b.s.elapsed)).toBeLessThanOrEqual(0.05);
    // 단계 전환 시각: 같은 개수, 각각 1프레임(1/30s) 이내
    const n = Math.min(a.transitions.length, b.transitions.length);
    expect(n).toBeGreaterThan(10);
    for (let i = 0; i < n; i++) {
      expect(Math.abs(a.transitions[i] - b.transitions[i])).toBeLessThanOrEqual(1 / 30 + 1e-9);
    }
  });

  it('계속 춤추면 들키는 시각이 fps와 무관', () => {
    const caughtAt = (fps: number) => {
      const s = createGame(DEFAULT_CONFIG, createRng(77));
      runUntil(s, (x) => x.mode !== 'playing', DANCE, 1 / fps);
      return s.elapsed;
    };
    expect(Math.abs(caughtAt(60) - caughtAt(30))).toBeLessThanOrEqual(0.05);
  });

  it('dt는 0.1초로 클램프된다', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(1));
    step(s, IDLE, 5);
    expect(s.elapsed).toBeCloseTo(0.1, 9);
  });
});

describe('셰럼 감시 판정', () => {
  it('right_watching 진입 후 grace 이내에 손을 떼면 안 들킨다', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(5));
    runUntil(s, (x) => x.sherum.phase === 'turning_right', IDLE);
    runUntil(s, (x) => x.sherum.phase === 'right_watching', DANCE);
    // 진입 직후 0.1초 안에 해제 (grace 0.15)
    expect(s.sherum.timer).toBeLessThan(DEFAULT_CONFIG.graceDuration);
    runUntil(s, (x) => x.sherum.timer >= 0.08, DANCE);
    expect(s.mode).toBe('playing');
    runUntil(s, (x) => x.sherum.phase === 'left_safe', IDLE);
    expect(s.mode).toBe('playing');
  });

  it('grace 이후에도 누르고 있으면 들킨다', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(5));
    runUntil(s, (x) => x.sherum.phase === 'turning_right', IDLE);
    const events = runUntil(s, (x) => x.mode !== 'playing', DANCE);
    expect(s.mode).toBe('caught');
    expect(s.result?.reason).toBe('caught');
    expect(events).toContain('caught');
    expect(s.sherum.phase).toBe('right_watching');
    expect(s.sherum.timer).toBeCloseTo(DEFAULT_CONFIG.graceDuration, 6);
  });

  it('turning_right(예고)에서 춤추면 점수가 오르고 들키지 않는다', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(9));
    const events = runUntil(s, (x) => x.sherum.phase === 'turning_right', IDLE);
    expect(events).toContain('sherum_warn');
    const before = s.score;
    runUntil(s, (x) => x.sherum.timer >= 0.4, DANCE);
    expect(s.sherum.phase).toBe('turning_right');
    expect(s.score).toBeGreaterThan(before);
    expect(s.mode).toBe('playing');
  });

  it('turning_left 구간은 점수·게이지 변화 없이 안전', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(9));
    runUntil(s, (x) => x.sherum.phase === 'turning_left', IDLE);
    const score = s.score;
    const gauge = s.gauge;
    step(s, DANCE, 0.1);
    expect(s.sherum.phase).toBe('turning_left');
    expect(s.score).toBe(score);
    expect(s.gauge).toBe(gauge);
    expect(s.mode).toBe('playing');
  });
});

describe('흥 게이지', () => {
  it('춤추지 않으면 게이지가 줄고 0이 되면 bored', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(3));
    step(s, IDLE, 0.1);
    expect(s.gauge).toBeCloseTo(100 - DEFAULT_CONFIG.gaugeDrainPerSec * 0.1, 9);
    const events = runUntil(s, (x) => x.mode !== 'playing', IDLE);
    expect(s.mode).toBe('over');
    expect(s.gauge).toBe(0);
    expect(s.result?.reason).toBe('bored');
    expect(events).toContain('bored');
    expect(s.elapsed).toBeCloseTo(100 / DEFAULT_CONFIG.gaugeDrainPerSec, 6);
  });

  it('춤추는 동안은 감시 구간이라도 게이지가 줄지 않는다', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(3));
    runUntil(s, (x) => x.sherum.phase === 'right_watching', IDLE);
    const g = s.gauge;
    step(s, DANCE, 0.1); // grace 이내
    expect(s.gauge).toBe(g);
  });
});

describe('빵', () => {
  it('2회만 동작, 3회째 bread_empty, 회복 상한 100', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(4));
    runUntil(s, (x) => x.elapsed >= 2, IDLE); // 게이지 82
    const bread: GameInput = { dance: false, breadPressed: true };

    step(s, bread, 1 / 60);
    expect(s.events).toContain('bread');
    expect(s.breadLeft).toBe(1);
    expect(s.gauge).toBeLessThanOrEqual(100);
    expect(s.gauge).toBeGreaterThan(99);
    expect(s.erpin.eating).toBeGreaterThan(0);
    expect(s.joanne.display).toBe('bread');

    step(s, bread, 1 / 60);
    expect(s.events).toContain('bread');
    expect(s.breadLeft).toBe(0);
    expect(s.gauge).toBeLessThanOrEqual(100);

    const g = s.gauge;
    step(s, bread, 1 / 60);
    expect(s.events).toContain('bread_empty');
    expect(s.events).not.toContain('bread');
    expect(s.breadLeft).toBe(0);
    expect(s.gauge).toBeLessThan(g); // 회복 없이 계속 감소
  });

  it('빵 회복량은 정확히 breadHeal', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(4));
    runUntil(s, (x) => x.gauge <= 50, IDLE);
    const g = s.gauge;
    step(s, { dance: false, breadPressed: true }, 1 / 60);
    const drained = DEFAULT_CONFIG.gaugeDrainPerSec / 60;
    expect(s.gauge).toBeCloseTo(g + DEFAULT_CONFIG.breadHeal - drained, 6);
  });
});

describe('죠안', () => {
  it('60초 이전엔 shocked, 이후엔 dancing, turning_right 진입 즉시 idle', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(42));
    let sawShocked = false;
    let sawDancing = false;
    let checkedWarnEntry = 0;
    let sawJoin = false;
    while (s.elapsed < 100) {
      const prevPhase = s.sherum.phase;
      step(s, leftOnlyBot(s), 1 / 60);
      expect(s.mode).toBe('playing');
      if (s.events.includes('joanne_join')) sawJoin = true;
      if (s.elapsed < DEFAULT_CONFIG.joanneJoinTime) {
        expect(s.joanne.display).not.toBe('dancing');
        if (s.erpin.dancing) {
          expect(s.joanne.display).toBe('shocked');
          sawShocked = true;
        }
      } else {
        if (s.erpin.dancing && s.sherum.phase === 'left_safe') {
          expect(s.joanne.display).toBe('dancing');
          sawDancing = true;
        }
        if (prevPhase === 'left_safe' && s.sherum.phase === 'turning_right') {
          expect(s.joanne.display).toBe('idle');
          checkedWarnEntry++;
        }
        if (s.sherum.phase !== 'left_safe') expect(s.joanne.display).not.toBe('dancing');
      }
    }
    expect(sawShocked).toBe(true);
    expect(sawDancing).toBe(true);
    expect(sawJoin).toBe(true);
    expect(checkedWarnEntry).toBeGreaterThan(3);
  });

  it('멈춘 뒤 shockedLinger 동안 shocked 유지 후 idle', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(42));
    runUntil(s, (x) => x.elapsed >= 0.5, DANCE);
    expect(s.joanne.display).toBe('shocked');
    runUntil(s, (x) => x.elapsed >= 1.2, IDLE);
    expect(s.joanne.display).toBe('shocked');
    runUntil(s, (x) => x.elapsed >= 1.6, IDLE);
    expect(s.joanne.display).toBe('idle');
  });

  it('죠안 상태는 종료 조건에 영향을 주지 않는다 (구조 확인)', () => {
    // 같은 시드·입력으로 한쪽만 죠안 상태를 마구 바꿔도 결과가 동일해야 한다
    const inputRng = createRng(99);
    const inputs: GameInput[] = [];
    for (let i = 0; i < 60 * 120; i++) {
      inputs.push({ dance: inputRng.next() < 0.6, breadPressed: inputRng.next() < 0.002 });
    }
    const a = createGame(DEFAULT_CONFIG, createRng(7));
    const b = createGame(DEFAULT_CONFIG, createRng(7));
    const displays = ['idle', 'shocked', 'dancing', 'bread'] as const;
    for (let i = 0; i < inputs.length && a.mode !== 'over'; i++) {
      b.joanne.display = displays[i % 4];
      b.joanne.offering = (i % 7) * 0.3;
      b.joanne.shockedLinger = (i % 5) * 0.4;
      step(a, inputs[i], 1 / 60);
      step(b, inputs[i], 1 / 60);
      expect(b.mode).toBe(a.mode);
      expect(b.score).toBe(a.score);
      expect(b.gauge).toBe(a.gauge);
    }
    expect(b.result).toEqual(a.result);
  });

  it('무작위 시드 퍼징 200판: reason은 항상 caught|bored', () => {
    for (let seed = 1; seed <= 200; seed++) {
      const s = createGame(DEFAULT_CONFIG, createRng(seed));
      const inRng = createRng(seed * 7919);
      const dt = seed % 2 === 0 ? 1 / 60 : 1 / 30;
      let held = false;
      let guard = 0;
      while (s.mode !== 'over') {
        if (inRng.next() < 0.08) held = !held;
        step(s, { dance: held, breadPressed: inRng.next() < 0.01 }, dt);
        if (++guard > 60 * 600) throw new Error(`seed ${seed} did not end`);
      }
      expect(['caught', 'bored']).toContain(s.result?.reason);
      expect(Number.isInteger(s.result?.score)).toBe(true);
    }
  });
});

describe('콤보', () => {
  it('배율 상한 1.5', () => {
    expect(comboMultiplier(0, DEFAULT_CONFIG)).toBe(1);
    expect(comboMultiplier(4, DEFAULT_CONFIG)).toBeCloseTo(1.2, 9);
    expect(comboMultiplier(10, DEFAULT_CONFIG)).toBeCloseTo(1.5, 9);
    expect(comboMultiplier(1000, DEFAULT_CONFIG)).toBeCloseTo(1.5, 9);
  });

  it('긴 안전 구간에서 점수 증가율도 1.5배에서 멈춘다', () => {
    const cfg: GameConfig = { ...DEFAULT_CONFIG, safeDurationStart: [40, 40], safeDurationEnd: [40, 40] };
    const s = createGame(cfg, createRng(1));
    runUntil(s, (x) => x.elapsed >= 20, DANCE);
    const before = s.score;
    runUntil(s, (x) => x.elapsed >= 21, DANCE);
    expect((s.score - before) / cfg.scoreRate).toBeCloseTo(1.5, 1);
    expect(s.maxStreak).toBeGreaterThanOrEqual(20);
    // 멈추면 streak 초기화
    step(s, IDLE, 1 / 60);
    expect(s.streak).toBe(0);
  });
});

describe('들킴 연출', () => {
  it('caught 중 입력 무시, caughtFreeze 후 over', () => {
    const s = createGame(DEFAULT_CONFIG, createRng(11));
    runUntil(s, (x) => x.mode !== 'playing', DANCE);
    expect(s.mode).toBe('caught');
    const snapshot = { score: s.score, gauge: s.gauge, breadLeft: s.breadLeft, elapsed: s.elapsed };
    let t = 0;
    while (t < DEFAULT_CONFIG.caughtFreeze - 0.05) {
      step(s, { dance: true, breadPressed: true }, 1 / 60);
      t += 1 / 60;
      expect(s.mode).toBe('caught');
      expect(s.events).toEqual([]);
    }
    expect({ score: s.score, gauge: s.gauge, breadLeft: s.breadLeft, elapsed: s.elapsed }).toEqual(snapshot);
    runUntil(s, (x) => x.mode === 'over', { dance: true, breadPressed: true }, 1 / 60, 1);
    expect(s.mode).toBe('over');
    expect(s.result?.reason).toBe('caught');
    expect(t).toBeLessThan(DEFAULT_CONFIG.caughtFreeze + 0.05);
  });
});

describe('구간 분할 상한', () => {
  it('단계 길이가 0.001s여도 MAX_SEGMENTS에서 남은 dt를 버리지 않는다', () => {
    const cfg: GameConfig = {
      ...DEFAULT_CONFIG,
      safeDurationStart: [0.001, 0.001],
      safeDurationEnd: [0.001, 0.001],
      watchDurationStart: [0.001, 0.001],
      watchDurationEnd: [0.001, 0.001],
      warnDurationStart: 0.001,
      warnDurationEnd: 0.001,
      turnBackDuration: 0.001,
      gaugeDrainPerSec: 0,
    };
    const s = createGame(cfg, createRng(21));
    let total = 0;
    for (let i = 0; i < 50; i++) {
      step(s, IDLE, 0.1);
      total += 0.1;
      expect(s.elapsed).toBeCloseTo(total, 9);
    }
    expect(s.mode).toBe('playing');
    expect(s.elapsed).toBeCloseTo(5, 9);
    // 한 step에 단계 전환이 여러 번 일어나야 한다 (상한까지는 정상 분할)
    expect(s.sherum.cycle).toBeGreaterThan(50);
  });
});

describe('게이지 0 시작', () => {
  it('gaugeStart 0이면 첫 step에서 춤춰도 bored로 끝난다', () => {
    const cfg: GameConfig = { ...DEFAULT_CONFIG, gaugeStart: 0 };
    const s = createGame(cfg, createRng(2));
    step(s, DANCE, 1 / 60);
    expect(s.mode).toBe('over');
    expect(s.result?.reason).toBe('bored');
    expect(s.events).toContain('bored');
    expect(s.gauge).toBe(0);
    expect(s.score).toBe(0);
  });

  it('gaugeStart 0이면 빵을 눌러도 살아나지 않는다', () => {
    const cfg: GameConfig = { ...DEFAULT_CONFIG, gaugeStart: 0 };
    const s = createGame(cfg, createRng(2));
    step(s, { dance: true, breadPressed: true }, 1 / 60);
    expect(s.result?.reason).toBe('bored');
    expect(s.breadLeft).toBe(cfg.breadCount);
  });
});

describe('빵 타이머 fps 독립성', () => {
  it('eating·offering이 끝나는 시각이 30/60fps에서 1프레임 이내로 같다', () => {
    const endTimes = (fps: number) => {
      const s = createGame(DEFAULT_CONFIG, createRng(4));
      const dt = 1 / fps;
      runUntil(s, (x) => x.elapsed >= 1, IDLE, dt);
      const pressedAt = s.elapsed; // 이번 step 시작 시각
      step(s, { dance: false, breadPressed: true }, dt);
      expect(s.events).toContain('bread');
      let eatEnd = -1;
      let offerEnd = -1;
      while (eatEnd < 0 || offerEnd < 0) {
        step(s, IDLE, dt);
        if (eatEnd < 0 && s.erpin.eating <= 0) eatEnd = s.elapsed - pressedAt;
        if (offerEnd < 0 && s.joanne.offering <= 0) offerEnd = s.elapsed - pressedAt;
        if (s.elapsed - pressedAt > 5) throw new Error('timer did not end');
      }
      return { eatEnd, offerEnd };
    };
    const a = endTimes(60);
    const b = endTimes(30);
    expect(Math.abs(a.eatEnd - b.eatEnd)).toBeLessThanOrEqual(1 / 60 + 1e-9);
    expect(Math.abs(a.offerEnd - b.offerEnd)).toBeLessThanOrEqual(1 / 60 + 1e-9);
    // 누른 시각 + duration 근처(1프레임 이내)에 끝난다
    expect(Math.abs(a.eatEnd - DEFAULT_CONFIG.eatDuration)).toBeLessThanOrEqual(1 / 60 + 1e-6);
    expect(Math.abs(b.eatEnd - DEFAULT_CONFIG.eatDuration)).toBeLessThanOrEqual(1 / 30 + 1e-6);
  });
});

/** elapsed를 강제한 뒤 현재 단계를 즉시 끝내 다음 단계에 진입시킨다 */
function enterNextAt(s: GameState, elapsed: number): void {
  s.elapsed = elapsed;
  s.sherum.timer = s.sherum.phaseDuration - 1e-6;
  step(s, IDLE, 1e-3);
}

describe('난이도 곡선: 예고·감시 길이', () => {
  it('turning_right 길이는 elapsed 0→120초에 0.5→0.25초로 선형 감소 후 고정', () => {
    const warnAt = (elapsed: number): number => {
      const s = createGame(DEFAULT_CONFIG, createRng(3));
      enterNextAt(s, elapsed);
      expect(s.sherum.phase).toBe('turning_right');
      return s.sherum.phaseDuration;
    };
    expect(warnAt(0)).toBeCloseTo(0.5, 6);
    expect(warnAt(60)).toBeCloseTo(0.375, 6);
    expect(warnAt(120)).toBeCloseTo(0.25, 6);
    expect(warnAt(300)).toBeCloseTo(0.25, 6);
  });

  it('elapsed 120초 이후 right_watching 길이는 2.5~4.0초 범위', () => {
    for (let seed = 1; seed <= 30; seed++) {
      for (const elapsed of [120, 200]) {
        const s = createGame(DEFAULT_CONFIG, createRng(seed));
        enterNextAt(s, elapsed);
        expect(s.sherum.phase).toBe('turning_right');
        enterNextAt(s, s.elapsed);
        expect(s.sherum.phase).toBe('right_watching');
        expect(s.sherum.phaseDuration).toBeGreaterThanOrEqual(2.5);
        expect(s.sherum.phaseDuration).toBeLessThanOrEqual(4.0);
      }
    }
  });
});
