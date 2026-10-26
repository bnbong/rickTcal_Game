// 1280×720 논리 좌표계의 캐릭터·소품·HUD 위치 상수 (사양서 §6)
export const LOGICAL_W = 1280;
export const LOGICAL_H = 720;

/** 캐릭터: 발(바닥 중앙) 위치와 그 캐릭터 포즈 중 최대 높이의 표시 높이 */
export interface CharacterSlot {
  footX: number;
  footY: number;
  height: number;
}

export const LAYOUT = {
  deskLong: { x: 560, y: 470, w: 760 },
  joanne: { footX: 720, footY: 520, height: 320 } as CharacterSlot,
  erpin: { footX: 1045, footY: 520, height: 330 } as CharacterSlot,
  sherum: { footX: 250, footY: 790, height: 520 } as CharacterSlot,
  deskSmall: { x: -40, y: 600, w: 520 },
  /**
   * 작은 책상 윗면(크림색 띠) 아래쪽 경계 y. desk_small 원본 76/258행 → 600 + 76×(520/569) ≈ 669.
   * 셰럼은 이 값 + sherumClipPad 아래를 잘라 그려 책상 다리 사이로 머리카락이 비치지 않게 한다.
   */
  deskSmallTopBottomY: 669,
  sherumClipPad: 30,
  /** 작은 책상 위 소품: 바닥 중앙 기준. 윗면 띠(y≈612~669, 오른쪽 끝 x≈453) 안쪽, 셰럼 손 오른쪽 */
  papers: { cx: 374, footY: 666, w: 90 },
  ink: { cx: 432, footY: 656, w: 40 },
  /** 긴 책상 위 죠안 앞 빵 접시 (남은 개수만큼 앞에서부터 사용) */
  breadPlates: [
    { cx: 665, footY: 492, w: 92 },
    { cx: 760, footY: 492, w: 92 },
  ],
  /** 느낌표 말풍선: 셰럼 머리 위 기준 오프셋 */
  warnBubble: { dx: 120, dy: 10, r: 40 },
  hud: {
    margin: 20,
    breadIcon: { x: 20, y: 16, size: 56 },
    gauge: { cx: 640, y: 18, w: 480 },
    label: { right: 1200, y: 14, w: 220 },
    pause: { x: 1216, y: 16, size: 48 },
  },
} as const;

/** 캐릭터별 포즈 키 (같은 캐릭터는 공통 축척을 써서 포즈 전환 시 크기가 튀지 않게) */
export const CHARACTER_POSES = {
  erpin: ['erpin_idle', 'erpin_dance', 'erpin_eat', 'erpin_caught'],
  joanne: ['joanne_idle', 'joanne_shocked', 'joanne_dance', 'joanne_bread'],
  sherum: ['sherum_safe', 'sherum_turning', 'sherum_watching'],
} as const;

/**
 * 포즈별 '몸 중심' x 기준점(원본 폭 대비 비율). 매니페스트 anchorX(0.5)는 bbox 중앙이라
 * 날개·머리카락이 한쪽으로 뻗은 포즈에서 몸이 좌우로 튄다. 피부색 픽셀(얼굴·손) 중앙값과
 * 가슴 보석 위치를 눈으로 대조해 정한 값으로, 이 점이 slot.footX에 오도록 그린다.
 * flipX는 이 기준점을 축으로 뒤집으므로 거울상 보정이 자동으로 따라온다.
 */
export const POSE_ANCHOR_X: Readonly<Record<string, number>> = {
  erpin_idle: 0.36,
  erpin_dance: 0.35,
  erpin_eat: 0.41,
  erpin_caught: 0.41,
  joanne_idle: 0.48,
  joanne_shocked: 0.53,
  joanne_dance: 0.53,
  joanne_bread: 0.44,
};

/** 매니페스트가 없을 때 플레이스홀더 크기 (원본 픽셀 가정값과 색) */
export const FALLBACK_SPRITES: Record<string, { w: number; h: number; color: string }> = {
  erpin_idle: { w: 420, h: 480, color: '#f3c94d' },
  erpin_dance: { w: 500, h: 520, color: '#f3c94d' },
  erpin_eat: { w: 420, h: 480, color: '#f3c94d' },
  erpin_caught: { w: 420, h: 480, color: '#f3c94d' },
  joanne_idle: { w: 420, h: 500, color: '#5bb36a' },
  joanne_shocked: { w: 420, h: 500, color: '#5bb36a' },
  joanne_dance: { w: 520, h: 520, color: '#5bb36a' },
  joanne_bread: { w: 460, h: 500, color: '#5bb36a' },
  sherum_safe: { w: 560, h: 720, color: '#3d4a7a' },
  sherum_turning: { w: 560, h: 720, color: '#3d4a7a' },
  sherum_watching: { w: 560, h: 720, color: '#3d4a7a' },
  desk_long: { w: 1400, h: 330, color: '#8a5a3c' },
  desk_small: { w: 900, h: 220, color: '#8a5a3c' },
  bread_plate: { w: 200, h: 120, color: '#e8b56a' },
  papers: { w: 260, h: 140, color: '#f4ecd6' },
  ink: { w: 90, h: 120, color: '#22304f' },
  ui_gauge_frame: { w: 900, h: 125, color: '#fbf4dc' },
  ui_bread_icon: { w: 200, h: 200, color: '#e8b56a' },
  ui_dance_icon: { w: 330, h: 330, color: '#7cc8f2' },
  ui_pause_icon: { w: 160, h: 170, color: '#7cc8f2' },
  ui_label: { w: 300, h: 100, color: '#fbf4dc' },
};

export const SPRITE_KEYS = Object.keys(FALLBACK_SPRITES);
