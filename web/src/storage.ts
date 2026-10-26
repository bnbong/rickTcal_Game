// localStorage 최고점·볼륨 저장 (차단·비공개 모드에서도 게임이 계속되도록 try/catch)
const KEY_BEST = 'smdc.best';
const KEY_VOLUME = 'smdc.volume';
const KEY_MUTED = 'smdc.muted';

let failed = false;

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    failed = true;
    return null;
  }
}

function write(key: string, value: string): boolean {
  try {
    window.localStorage.setItem(key, value);
    // 일부 브라우저는 쓰기를 조용히 버리므로 다시 읽어 확인
    if (window.localStorage.getItem(key) !== value) throw new Error('not persisted');
    return true;
  } catch {
    failed = true;
    return false;
  }
}

/** 한 번이라도 읽기/쓰기에 실패했는지 (결과 화면 안내용) */
export function storageFailed(): boolean {
  return failed;
}

export function loadBest(): number {
  const n = Number(read(KEY_BEST));
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
}

export function saveBest(score: number): boolean {
  return write(KEY_BEST, String(Math.floor(score)));
}

export function loadVolume(): number {
  const raw = read(KEY_VOLUME);
  const n = raw === null ? NaN : Number(raw);
  return Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : 0.7;
}

export function saveVolume(v: number): void {
  write(KEY_VOLUME, String(v));
}

export function loadMuted(): boolean {
  return read(KEY_MUTED) === '1';
}

export function saveMuted(m: boolean): void {
  write(KEY_MUTED, m ? '1' : '0');
}
