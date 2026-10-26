// 에셋 매니페스트 로드와 이미지 캐시 (실패해도 플레이스홀더로 계속 동작)
import { FALLBACK_SPRITES, SPRITE_KEYS } from './layout';

export interface SpriteInfo {
  src: string;
  w: number;
  h: number;
  anchorX: number;
  anchorY: number;
}

export interface Manifest {
  version: number;
  background: { src: string; w: number; h: number };
  sprites: Record<string, SpriteInfo>;
  gauge: {
    fillRect: { x: number; y: number; w: number; h: number };
    fillColor: string;
    trackColor: string;
  };
}

export interface SpriteBank {
  manifest: Manifest | null;
  images: Map<string, HTMLImageElement>;
  background: HTMLImageElement | null;
  /** 매니페스트 자체를 못 불러왔는지 */
  manifestFailed: boolean;
  /** 개별 이미지 로드 실패 키 */
  missing: string[];
}

const BASE = './assets/';

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`image load failed: ${src}`));
    img.src = src;
  });
}

/** 매니페스트와 모든 이미지를 불러온다. 진행률은 (완료, 전체)로 보고. reject하지 않는다 */
export async function loadSprites(onProgress?: (done: number, total: number) => void): Promise<SpriteBank> {
  const bank: SpriteBank = {
    manifest: null,
    images: new Map(),
    background: null,
    manifestFailed: false,
    missing: [],
  };

  try {
    const res = await fetch(`${BASE}manifest.json`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`manifest ${res.status}`);
    bank.manifest = (await res.json()) as Manifest;
  } catch {
    bank.manifestFailed = true;
    bank.missing = [...SPRITE_KEYS];
    onProgress?.(1, 1);
    return bank;
  }

  const manifest = bank.manifest;
  const keys = SPRITE_KEYS.filter((k) => manifest.sprites?.[k]);
  for (const k of SPRITE_KEYS) if (!manifest.sprites?.[k]) bank.missing.push(k);
  const total = keys.length + 1;
  let done = 0;
  const tick = () => onProgress?.(++done, total);
  onProgress?.(0, total);

  const jobs: Promise<void>[] = keys.map((k) =>
    loadImage(BASE + manifest.sprites[k].src)
      .then((img) => {
        bank.images.set(k, img);
      })
      .catch(() => {
        bank.missing.push(k);
      })
      .finally(tick),
  );
  jobs.push(
    (manifest.background
      ? loadImage(BASE + manifest.background.src).then((img) => {
          bank.background = img;
        })
      : Promise.reject(new Error('no background'))
    )
      .catch(() => {
        bank.missing.push('background');
      })
      .finally(tick),
  );
  await Promise.all(jobs);
  return bank;
}

/** 키의 원본 픽셀 크기와 기준점 (매니페스트 우선, 없으면 대체값) */
export function spriteSize(bank: SpriteBank, key: string): SpriteInfo {
  const m = bank.manifest?.sprites?.[key];
  if (m && m.w > 0 && m.h > 0) return m;
  const f = FALLBACK_SPRITES[key] ?? { w: 100, h: 100 };
  return { src: '', w: f.w, h: f.h, anchorX: 0.5, anchorY: 1 };
}
