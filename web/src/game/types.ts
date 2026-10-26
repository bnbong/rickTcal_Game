// 시뮬레이션 상태·입력·이벤트 타입 정의
import type { GameConfig } from '../config';

export interface GameInput {
  /** 춤 버튼(스페이스/터치)을 누르고 있는지 */
  dance: boolean;
  /** 이번 프레임에 빵 버튼이 눌렸는지(에지) */
  breadPressed: boolean;
}

export interface Rng {
  /** [0, 1) */
  next(): number;
}

export type SherumPhase = 'left_safe' | 'turning_right' | 'right_watching' | 'turning_left';
export type JoanneDisplay = 'idle' | 'shocked' | 'dancing' | 'bread';
export type EndReason = 'caught' | 'bored';

export type SimEvent =
  | 'sherum_warn'
  | 'sherum_watch'
  | 'sherum_back'
  | 'caught'
  | 'bored'
  | 'bread'
  | 'bread_empty'
  | 'dance_start'
  | 'dance_stop'
  | 'joanne_join';

export interface GameResult {
  reason: EndReason;
  /** 반올림 정수 점수 */
  score: number;
  elapsed: number;
  maxStreak: number;
}

export interface GameState {
  /** step이 참조하는 설정과 난수원 (createGame에서 주입) */
  readonly config: GameConfig;
  readonly rng: Rng;
  mode: 'playing' | 'caught' | 'over';
  elapsed: number;
  score: number;
  gauge: number;
  breadLeft: number;
  streak: number;
  maxStreak: number;
  sherum: { phase: SherumPhase; timer: number; phaseDuration: number; cycle: number };
  erpin: { dancing: boolean; eating: number; caught: boolean };
  joanne: { display: JoanneDisplay; shockedLinger: number; offering: number };
  /** caught 모드 남은 연출 시간 */
  caughtTimer: number;
  result?: GameResult;
  events: SimEvent[];
}
