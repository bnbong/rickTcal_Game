// 오디오 매니저: Web Audio 합성 SFX·BGM. 외부 음원 파일 없음
import { BgmPlayer } from './bgm';
import { createNoiseBuffer, playSfxAt, type SfxName } from './sfx';

export type { SfxName } from './sfx';

type AudioContextCtor = new () => AudioContext;

function getAudioContextCtor(): AudioContextCtor | null {
  if (typeof window === 'undefined') return null;
  const w = window as unknown as { AudioContext?: AudioContextCtor; webkitAudioContext?: AudioContextCtor };
  return w.AudioContext ?? w.webkitAudioContext ?? null;
}

const clamp01 = (v: number): number => Math.min(1, Math.max(0, Number.isFinite(v) ? v : 0));

/**
 * 모든 소리는 master GainNode 하나를 거친다.
 * unlock() 전이거나 AudioContext가 없으면 재생 호출은 전부 조용히 무시한다.
 * 생성자는 아무 것도 만들거나 재생하지 않는다(자동재생 정책).
 */
export class AudioManager {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private noiseBuf: AudioBuffer | null = null;
  private bgm: BgmPlayer | null = null;
  private volume = 0.8;
  private muted = false;
  private intensity = 0;
  private suspended = false;
  /** startBgm()이 컨텍스트가 running이 아니어서 미뤄졌는지. unlock/resume 성공 시 시작한다 */
  private bgmPending = false;

  /** 사용자 제스처 핸들러 안에서 호출. AudioContext 생성 또는 resume */
  async unlock(): Promise<void> {
    try {
      if (!this.ctx) {
        const Ctor = getAudioContextCtor();
        if (!Ctor) return;
        const ctx = new Ctor();
        const master = ctx.createGain();
        master.gain.value = this.targetGain();
        master.connect(ctx.destination);
        this.ctx = ctx;
        this.master = master;
        this.noiseBuf = createNoiseBuffer(ctx);
        this.bgm = new BgmPlayer(ctx, master, this.noiseBuf);
        this.bgm.setIntensity(this.intensity);
      }
      this.suspended = false;
      if (this.ctx.state !== 'running') await this.ctx.resume();
      this.flushPendingBgm();
    } catch {
      // 오디오 실패는 게임 진행에 영향 주지 않는다
    }
  }

  /** 마스터 볼륨 0..1 (unlock 전에도 값은 기억) */
  setVolume(v: number): void {
    this.volume = clamp01(v);
    this.applyGain();
  }

  setMuted(m: boolean): void {
    this.muted = m;
    this.applyGain();
  }

  playSfx(name: SfxName): void {
    const { ctx, master, noiseBuf } = this;
    if (!ctx || !master || !noiseBuf || ctx.state !== 'running') return;
    try {
      playSfxAt(ctx, master, noiseBuf, name);
    } catch {
      // 무시
    }
  }

  /** AudioContext가 있고 실제로 재생 가능한 상태인지 */
  isRunning(): boolean {
    return this.ctx !== null && this.ctx.state === 'running';
  }

  /**
   * BGM 시작. 컨텍스트가 running이 아니면(unlock 실패·지연) 스케줄러를 돌리지 않고
   * 보류 표시만 남긴다. 이후 unlock()/resume()이 성공하면 그때 시작한다.
   */
  startBgm(): void {
    if (!this.bgm || !this.isRunning()) {
      this.bgmPending = true;
      return;
    }
    this.bgmPending = false;
    this.bgm.start();
    if (this.suspended) this.bgm.pause();
  }

  stopBgm(): void {
    this.bgmPending = false;
    this.bgm?.stop();
  }

  /** 0..1. 0.5 미만이면 하이햇 off, 1에 가까울수록 템포 128→140 (다음 마디부터) */
  setBgmIntensity(v: number): void {
    this.intensity = clamp01(v);
    this.bgm?.setIntensity(this.intensity);
  }

  /** 탭 숨김 시: BGM 스케줄러 정지 + 컨텍스트 suspend */
  suspend(): void {
    if (!this.ctx) return;
    this.suspended = true;
    this.bgm?.pause();
    this.ctx.suspend().catch(() => undefined);
  }

  /** 탭 복귀 시. 사용자 제스처가 아니어도 이미 unlock된 컨텍스트는 대개 재개된다 */
  resume(): void {
    const ctx = this.ctx;
    if (!ctx) return;
    this.suspended = false;
    ctx
      .resume()
      .then(() => {
        if (this.suspended) return;
        if (this.bgmPending) this.flushPendingBgm();
        else this.bgm?.resume();
      })
      .catch(() => undefined);
  }

  /** 보류된 BGM 시작 요청이 있고 이제 running이면 시작 */
  private flushPendingBgm(): void {
    if (this.bgmPending && !this.suspended && this.isRunning()) this.startBgm();
  }

  private targetGain(): number {
    return this.muted ? 0 : this.volume;
  }

  private applyGain(): void {
    if (!this.ctx || !this.master) return;
    // 클릭 노이즈 방지: 시정수 0.02s로 부드럽게 이동
    this.master.gain.setTargetAtTime(this.targetGain(), this.ctx.currentTime, 0.02);
  }
}
