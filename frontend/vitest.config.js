import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig } from 'vite'
import { configDefaults, defineProject } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default mergeConfig(
  {
    plugins: [vue()],
  },
  defineProject({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/*'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      setupFiles: ['./tests/setup.js'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        include: ['src/**/*.{vue,js,ts}'],
      },
    },
  }),
)
