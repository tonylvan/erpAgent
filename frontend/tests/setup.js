import { config } from '@vue/test-utils'

// 全局配置
config.global.mocks = {
  $t: (key) => key,
}

// 全局组件
config.global.components = {}
