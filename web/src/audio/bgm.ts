// BGM: 8비트풍 4마디 루프 (사각파 멜로디 + 삼각파 베이스 + 노이즈 하이햇), 직접 작곡
import { noise, tone } from './sfx';

const LOOKAHEAD_MS = 25; // 스케줄러 호출 간격
const SCHEDULE_AHEAD = 0.1; // 선예약 구간(초)
const STEPS_PER_BAR = 16; // 16분음표 격자
const BARS = 4;
const TOTAL_STEPS = STEPS_PER_BAR * BARS;
const BPM_MIN = 128;
const BPM_MAX = 140;

/** [음이름, 8분음표 길이]; 음이름 null = 쉼표. 코드 진행 C - Am - F - G, 다장조 */
type Note = [string | null, number];
const MELODY: Note[] = [
  // 1마디 C
  ['E5', 1], ['G5', 1], ['C6', 1], ['G5', 1], ['A5', 1], ['G5', 1], ['E5', 2],
  // 2마디 Am
  ['C5', 1], ['E5', 1], ['A5', 1], ['E5', 1], ['G5', 1], ['E5', 1], ['C5', 1], ['D5', 1],
  // 3마디 F
  ['F5', 1], ['A5', 1], ['C6', 1], ['A5', 1], ['D6', 1], ['C6', 1], ['A5', 2],
  // 4마디 G
  ['G5', 1], [null, 1], ['B5', 1], ['D6', 1], ['C6', 1], ['B5', 1], ['G5', 1], [null, 1],
];
/** 마디별 베이스 근음 (8분음표마다 옥타브 왕복) */
const BASS_ROOTS = ['C3', 'A2', 'F2', 'G2'];

const NOTE_INDEX: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

/** 'C#5' 형식 음이름 → 주파수(Hz) */
function noteFreq(name: string): number {
  const m = /^([A-G])(#?)(-?\d)$/.exec(name);
  if (!m) throw new Error(`bad note: ${name}`);
  const midi = (Number(m[3]) + 1) * 12 + (NOTE_INDEX[m[1] ?? 'C'] ?? 0) + (m[2] ? 1 : 0);
  return 440 * Math.pow(2, (midi - 69) / 12);
}

/** 16분음표 step → [주파수, 길이(step)] 표. 모듈 로드 시 1회 계산 */
const MELODY_TABLE: Array<[number, number] | undefined> = (() => {
  const table: Array<[number, number] | undefined> = new Array(TOTAL_STEPS);
  let step = 0;
  for (const [name, eighths] of MELODY) {
    const len = eighths * 2;
    if (name) table[step] = [noteFreq(name), len];
    step += len;
  }
  return table;
})();
const BASS_FREQS = BASS_ROOTS.map(noteFreq);

export class BgmPlayer {
  private bus: GainNode | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  private step = 0;
  private nextTime = 0;
  private bpm = BPM_MIN;
  private hatOn = false;
  private intensity = 0;

  constructor(
    private readonly ctx: AudioContext,
    private readonly dest: AudioNode,
    private readonly noiseBuf: AudioBuffer,
  ) {}

  get playing(): boolean {
    return this.bus !== null;
  }

  start(): void {
    if (this.bus) return;
    // 재생마다 새 버스: stop 시 이미 예약된 음까지 함께 페이드아웃하기 위함
    const bus = this.ctx.createGain();
    bus.gain.value = 0.55;
    bus.connect(this.dest);
    this.bus = bus;
    this.step = 0;
    this.applyIntensity();
    this.nextTime = this.ctx.currentTime + 0.05;
    this.startTimer();
  }

  stop(): void {
    this.stopTimer();
    const bus = this.bus;
    if (!bus) return;
    this.bus = null;
    const now = this.ctx.currentTime;
    bus.gain.cancelScheduledValues(now);
    bus.gain.setTargetAtTime(0, now, 0.03);
    setTimeout(() => bus.disconnect(), 400);
  }

  /** 0..1. 실제 반영(하이햇·템포)은 다음 마디 경계에서 */
  setIntensity(v: number): void {
    this.intensity = Math.min(1, Math.max(0, Number.isFinite(v) ? v : 0));
  }

  /** 탭 숨김: 타이머만 멈춘다 (컨텍스트 suspend는 AudioManager 담당) */
  pause(): void {
    this.stopTimer();
  }

  resume(): void {
    if (!this.bus || this.timer !== null) return;
    // 밀린 예약을 몰아서 재생하지 않도록 기준 시각을 현재로 당긴다
    this.nextTime = Math.max(this.nextTime, this.ctx.currentTime + 0.05);
    this.startTimer();
  }

  private startTimer(): void {
    this.stopTimer();
    this.timer = setInterval(() => this.tick(), LOOKAHEAD_MS);
    this.tick();
  }

  private stopTimer(): void {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
  }

  private applyIntensity(): void {
    this.hatOn = this.intensity >= 0.5;
    this.bpm = BPM_MIN + (BPM_MAX - BPM_MIN) * this.intensity;
  }

  private tick(): void {
    if (!this.bus) return;
    const now = this.ctx.currentTime;
    // 백그라운드 스로틀 등으로 크게 뒤처졌으면 따라잡지 말고 건너뛴다
    if (this.nextTime < now - 0.2) this.nextTime = now + 0.02;
    while (this.nextTime < now + SCHEDULE_AHEAD) {
      if (this.step % STEPS_PER_BAR === 0) this.applyIntensity();
      const stepDur = 60 / this.bpm / 4;
      this.scheduleStep(this.step, this.nextTime, stepDur, this.bus);
      this.nextTime += stepDur;
      this.step = (this.step + 1) % TOTAL_STEPS;
    }
  }

  private scheduleStep(step: number, t: number, stepDur: number, bus: GainNode): void {
    const ctx = this.ctx;
    const mel = MELODY_TABLE[step];
    if (mel) {
      // 사각파 멜로디: 음 길이의 85%만 울려 스타카토 느낌
      tone(ctx, bus, { type: 'square', freq: mel[0], start: t, dur: mel[1] * stepDur * 0.85, peak: 0.07, attack: 0.004 });
    }
    if (step % 2 === 0) {
      // 삼각파 베이스: 8분음표마다 근음/옥타브 위 교대
      const root = BASS_FREQS[Math.floor(step / STEPS_PER_BAR)] ?? BASS_FREQS[0] ?? 130.81;
      const freq = step % 4 === 0 ? root : root * 2;
      tone(ctx, bus, { type: 'triangle', freq, start: t, dur: stepDur * 1.8, peak: 0.22, attack: 0.004 });
      if (this.hatOn) {
        // 하이햇: 오프비트(8분 뒷박)를 조금 더 강하게
        const accent = step % 4 === 2;
        noise(ctx, bus, this.noiseBuf, {
          start: t, dur: accent ? 0.06 : 0.035, peak: accent ? 0.07 : 0.04, filter: 'highpass', cutoff: 7000,
        });
      }
    }
  }
}
