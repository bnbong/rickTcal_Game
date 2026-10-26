// Vite 빌드·Vitest 설정 (정적 상대 경로 빌드)
import { defineConfig } from 'vitest/config';

export default defineConfig({
  base: './',
  build: {
    outDir: 'dist',
    // public/assets(게임 에셋)와 번들 산출물이 섞이지 않게 분리
    assetsDir: 'static',
    target: 'es2020',
  },
  test: {
    include: ['test/**/*.test.ts'],
    environment: 'node',
  },
});
