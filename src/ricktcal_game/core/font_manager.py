import pygame


class FontManager:
    """게임 전체의 폰트를 관리하는 클래스"""

    def __init__(self):
        self.fonts = {}
        self.default_font_sizes = {"small": 24, "normal": 36, "large": 48, "title": 70}

        # 한글 폰트 후보 목록 TODO : 커스텀 폰트 추가
        self.korean_font_candidates = [
            "malgun gothic",
            "malgungothic",
            "gulim",
            "gungsuh",
            "batang",
            "applegothic",
            "nanumgothic",
            "nanumgothicbold",
        ]

        self.font_paths = {"korean": self.find_korean_font()}

        self.initialize_fonts()

    def find_korean_font(self):
        """시스템에서 한글 폰트 찾기"""
        for font_name in self.korean_font_candidates:
            font_path = pygame.font.match_font(font_name)
            if font_path:
                print(f"한글 폰트 발견: {font_name} ({font_path})")
                return font_path

        print("경고: 한글 폰트를 찾을 수 없습니다. 대체 폰트를 사용합니다.")
        # 폰트 적용 실패 시 기본 폰트 적용
        return pygame.font.get_default_font()

    def initialize_fonts(self):
        """폰트 캐시 초기화"""
        try:
            # 기본 폰트 (영문용)
            for size_name, size in self.default_font_sizes.items():
                key = f"default_{size_name}"
                self.fonts[key] = pygame.font.Font(None, size)

            # 한글 폰트
            if "korean" in self.font_paths and self.font_paths["korean"]:
                korean_path = self.font_paths["korean"]
                for size_name, size in self.default_font_sizes.items():
                    key = f"korean_{size_name}"
                    self.fonts[key] = pygame.font.Font(korean_path, size)

                    compat_key = f"nanum_{size_name}"
                    self.fonts[compat_key] = pygame.font.Font(korean_path, size)

                print(f"한글 폰트 로드 완료: {korean_path}")
            else:
                print("경고: 한글 폰트 파일을 찾을 수 없습니다.")

        except Exception as e:
            print(f"폰트 초기화 오류: {e}")

    def normalize_font_type(self, font_type):
        """폰트 타입 이름 정규화"""
        if font_type in ["nanum", "korean", "hangul", "nanumgothic"]:
            return "korean"
        return font_type

    def get_font(self, font_type="default", size_type="normal"):
        """특정 유형과 크기의 폰트 반환"""
        font_type = self.normalize_font_type(font_type)
        key = f"{font_type}_{size_type}"

        if key in self.fonts:
            return self.fonts[key]

        if font_type in ["korean"]:
            korean_key = f"korean_{size_type}"
            if korean_key in self.fonts:
                return self.fonts[korean_key]

        # 폴백 처리
        fallback_key = f"default_{size_type}"
        if fallback_key in self.fonts:
            print(f"경고: {key} 폰트를 찾을 수 없어 {fallback_key}로 대체합니다.")
            return self.fonts[fallback_key]

        print(f"경고: {fallback_key} 폰트도 찾을 수 없어 새 폰트를 생성합니다.")
        return pygame.font.Font(None, self.default_font_sizes.get(size_type, 36))

    def render_text(
        self,
        text,
        font_type="default",
        size_type="normal",
        color=(255, 255, 255),
        antialias=True,
    ):
        """텍스트 렌더링 헬퍼 메서드"""
        font_type = self.normalize_font_type(font_type)
        font = self.get_font(font_type, size_type)
        return font.render(text, antialias, color)
