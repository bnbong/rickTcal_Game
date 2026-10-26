// 효과음 합성: 오실레이터·노이즈 버퍼·게인 엔벨로프만 사용 (외부 음원 없음)

export type SfxName = 'warn' | 'watch' | 'back' | 'caught' | 'bored' | 'bread' | 'ui' | 'dance_start';

/** 1초 길이 화이트 노이즈 버퍼 (하이햇·노이즈 SFX 공용) */
export function createNoiseBuffer(ctx: BaseAudioContext): AudioBuffer {
  const len = Math.floor(ctx.sampleRate);
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
  return buf;
}

interface ToneOpts {
  type: OscillatorType;
  freq: number;
  /** 끝 주파수 (지정 시 지수 글라이드) */
  freqEnd?: number;
  start: number;
  dur: number;
  peak: number;
  attack?: number;
}

/** 단일 오실레이터 + 퍼커시브 엔벨로프 */
export function tone(ctx: BaseAudioContext, dest: AudioNode, o: ToneOpts): void {
  const osc = ctx.createOscillator();
  const g = ctx.createGain();
  const attack = o.attack ?? 0.005;
  const end = o.start + o.dur;
  osc.type = o.type;
  osc.frequency.setValueAtTime(o.freq, o.start);
  if (o.freqEnd !== undefined) {
    osc.frequency.exponentialRampToValueAtTime(Math.max(1, o.freqEnd), end);
  }
  g.gain.setValueAtTime(0.0001, o.start);
  g.gain.exponentialRampToValueAtTime(o.peak, o.start + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, end);
  osc.connect(g).connect(dest);
  osc.start(o.start);
  osc.stop(end + 0.02);
  osc.onended = () => g.disconnect();
}

interface NoiseOpts {
  start: number;
  dur: number;
  peak: number;
  filter: BiquadFilterType;
  cutoff: number;
  /** 필터 컷오프 끝값 (지정 시 지수 이동) */
  cutoffEnd?: number;
  q?: number;
}

/** 필터를 거친 노이즈 버스트 */
export function noise(ctx: BaseAudioContext, dest: AudioNode, buf: AudioBuffer, o: NoiseOpts): void {
  const src = ctx.createBufferSource();
  const f = ctx.createBiquadFilter();
  const g = ctx.createGain();
  const end = o.start + o.dur;
  src.buffer = buf;
  f.type = o.filter;
  f.frequency.setValueAtTime(o.cutoff, o.start);
  if (o.cutoffEnd !== undefined) f.frequency.exponentialRampToValueAtTime(o.cutoffEnd, end);
  f.Q.value = o.q ?? 1;
  g.gain.setValueAtTime(0.0001, o.start);
  g.gain.exponentialRampToValueAtTime(o.peak, o.start + 0.003);
  g.gain.exponentialRampToValueAtTime(0.0001, end);
  src.connect(f).connect(g).connect(dest);
  // 버퍼 안에서 시작 위치를 무작위로 잡아 매번 조금씩 다른 질감
  src.start(o.start, Math.random() * 0.5);
  src.stop(end + 0.02);
  src.onended = () => g.disconnect();
}

/** 이름별 SFX 재생. 모든 소리는 dest(마스터 경로)로 나간다 */
export function playSfxAt(ctx: BaseAudioContext, dest: AudioNode, buf: AudioBuffer, name: SfxName): void {
  const t = ctx.currentTime + 0.005;
  switch (name) {
    case 'warn':
      // 삐빅: 사각파 2음 상승(A5→E6), 사인 한 옥타브 아래를 겹쳐 또렷하게. 총 0.2s
      tone(ctx, dest, { type: 'square', freq: 880, start: t, dur: 0.075, peak: 0.22 });
      tone(ctx, dest, { type: 'sine', freq: 440, start: t, dur: 0.075, peak: 0.2 });
      tone(ctx, dest, { type: 'square', freq: 1319, start: t + 0.095, dur: 0.1, peak: 0.24 });
      tone(ctx, dest, { type: 'sine', freq: 659, start: t + 0.095, dur: 0.1, peak: 0.2 });
      break;
    case 'watch':
      // 쿵: 사인 140→45Hz 하강 + 저역 노이즈 타격음. 0.3s
      tone(ctx, dest, { type: 'sine', freq: 140, freqEnd: 45, start: t, dur: 0.3, peak: 0.7, attack: 0.004 });
      noise(ctx, dest, buf, { start: t, dur: 0.08, peak: 0.25, filter: 'lowpass', cutoff: 600 });
      break;
    case 'back':
      // 틱: 3kHz 대역 노이즈 + 1.8kHz 사인 클릭. 0.035s
      noise(ctx, dest, buf, { start: t, dur: 0.035, peak: 0.15, filter: 'bandpass', cutoff: 3000, q: 4 });
      tone(ctx, dest, { type: 'sine', freq: 1800, start: t, dur: 0.025, peak: 0.08, attack: 0.002 });
      break;
    case 'caught':
      // 하강 글리산도(사각파 900→110Hz) + 저역으로 닫히는 노이즈. 0.55s
      tone(ctx, dest, { type: 'square', freq: 900, freqEnd: 110, start: t, dur: 0.55, peak: 0.2, attack: 0.01 });
      tone(ctx, dest, { type: 'triangle', freq: 450, freqEnd: 55, start: t, dur: 0.55, peak: 0.25, attack: 0.01 });
      noise(ctx, dest, buf, { start: t, dur: 0.45, peak: 0.22, filter: 'lowpass', cutoff: 5000, cutoffEnd: 300 });
      break;
    case 'bored':
      // 느린 하강 3음(G4→E4→C4) 삼각파, 음마다 0.18s. 총 0.56s
      tone(ctx, dest, { type: 'triangle', freq: 392, start: t, dur: 0.17, peak: 0.3, attack: 0.02 });
      tone(ctx, dest, { type: 'triangle', freq: 330, start: t + 0.18, dur: 0.17, peak: 0.28, attack: 0.02 });
      tone(ctx, dest, { type: 'triangle', freq: 262, freqEnd: 247, start: t + 0.36, dur: 0.2, peak: 0.26, attack: 0.02 });
      break;
    case 'bread':
      // 통통: 피치가 살짝 떨어지는 사인 2음(520→380, 700→520Hz). 0.22s
      tone(ctx, dest, { type: 'sine', freq: 520, freqEnd: 380, start: t, dur: 0.09, peak: 0.4, attack: 0.003 });
      tone(ctx, dest, { type: 'sine', freq: 700, freqEnd: 520, start: t + 0.12, dur: 0.1, peak: 0.4, attack: 0.003 });
      break;
    case 'ui':
      // 클릭: 1.2kHz 사각파 0.03s
      tone(ctx, dest, { type: 'square', freq: 1200, start: t, dur: 0.03, peak: 0.1, attack: 0.002 });
      break;
    case 'dance_start':
      // 띵: 짧은 G5 꾸밈음 뒤 C6(삼각파+사인 2배음). 0.26s
      tone(ctx, dest, { type: 'triangle', freq: 784, start: t, dur: 0.04, peak: 0.18, attack: 0.002 });
      tone(ctx, dest, { type: 'triangle', freq: 1047, start: t + 0.04, dur: 0.22, peak: 0.25, attack: 0.003 });
      tone(ctx, dest, { type: 'sine', freq: 2093, start: t + 0.04, dur: 0.12, peak: 0.06, attack: 0.003 });
      break;
  }
}
