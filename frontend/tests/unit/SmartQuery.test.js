/**
 * SmartQuery 组件单元测试
 * 覆盖：组件渲染、用户交互、API 调用、错误处理
 * 总计 13 个测试用例
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SmartQuery from '../src/views/SmartQuery.vue'
import { nextTick } from 'vue'

// Mock Element Plus 组件
vi.mock('element-plus', () => ({
  ElButton: {
    name: 'ElButton',
    template: '<button class="el-button"><slot /></button>',
    props: ['type', 'size', 'loading', 'disabled', 'plain']
  },
  ElInput: {
    name: 'ElInput',
    template: '<input class="el-input" /><slot name="append" />',
    props: ['modelValue', 'placeholder', 'disabled']
  },
  ElTag: {
    name: 'ElTag',
    template: '<span class="el-tag"><slot /></span>',
    props: ['type', 'effect']
  },
  ElCard: {
    name: 'ElCard',
    template: '<div class="el-card"><div class="header"><slot name="header" /></div><div class="body"><slot /></div></div>',
    props: ['shadow']
  },
  ElIcon: {
    name: 'ElIcon',
    template: '<i class="el-icon"><slot /></i>',
    props: []
  }
}))

// Mock API 调用
const mockPostQuery = vi.fn()
const mockGetSuggested = vi.fn()

describe('SmartQuery Component', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ==================== 组件渲染测试 (4 个) ====================

  describe('Component Rendering', () => {
    it('should render successfully', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      expect(wrapper.exists()).toBe(true)
    })

    it('should display welcome message when no messages', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      expect(wrapper.text()).toContain('你好！我是 GSD 智能问数助手')
    })

    it('should display quick questions', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      const quickQuestions = wrapper.findAll('.question-tag')
      expect(quickQuestions.length).toBeGreaterThan(0)
    })

    it('should have input field', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      const input = wrapper.find('.el-input')
      expect(input.exists()).toBe(true)
    })
  })

  // ==================== 用户交互测试 (5 个) ====================

  describe('User Interaction', () => {
    beforeEach(() => {
      mockPostQuery.mockResolvedValue({
        success: true,
        answer: '这是测试回答',
        data_type: 'text'
      })
    })

    it('should send message on button click', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      // 输入消息
      const input = wrapper.find('input')
      await input.setValue('销售趋势')
      
      // 点击发送按钮
      const sendButton = wrapper.find('button[type="primary"]')
      await sendButton.trigger('click')
      
      await flushPromises()
      expect(mockPostQuery).toHaveBeenCalled()
    })

    it('should send message on Enter key', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('测试消息')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      expect(mockPostQuery).toHaveBeenCalled()
    })

    it('should disable input while loading', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      // 模拟加载状态
      wrapper.vm.isLoading = true
      await nextTick()
      
      const input = wrapper.find('input')
      expect(input.attributes('disabled')).toBeDefined()
    })

    it('should add user message to list', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('测试问题')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      expect(wrapper.vm.messages.length).toBeGreaterThan(0)
    })

    it('should show loading indicator during API call', async () => {
      mockPostQuery.mockImplementation(() => {
        return new Promise(resolve => setTimeout(() => {
          resolve({ success: true, answer: '回答', data_type: 'text' })
        }, 100))
      })

      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('测试')
      await input.trigger('keyup.enter')
      
      await nextTick()
      expect(wrapper.vm.isLoading).toBe(true)
    })
  })

  // ==================== API 调用测试 (2 个) ====================

  describe('API Calls', () => {
    it('should call API with correct parameters', async () => {
      mockPostQuery.mockResolvedValue({
        success: true,
        answer: '测试结果',
        data_type: 'text'
      })

      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('销售数据')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      expect(mockPostQuery).toHaveBeenCalledWith('销售数据')
    })

    it('should handle API error gracefully', async () => {
      mockPostQuery.mockRejectedValue(new Error('API Error'))

      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('测试')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      // 应该不崩溃
      expect(wrapper.exists()).toBe(true)
    })
  })

  // ==================== 数据展示测试 (2 个) ====================

  describe('Data Display', () => {
    it('should display assistant response', async () => {
      mockPostQuery.mockResolvedValue({
        success: true,
        answer: '这是 AI 回答',
        data_type: 'text'
      })

      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('测试')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      expect(wrapper.text()).toContain('这是 AI 回答')
    })

    it('should display feedback buttons for assistant messages', async () => {
      mockPostQuery.mockResolvedValue({
        success: true,
        answer: '回答',
        data_type: 'text'
      })

      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('测试')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      const feedbackButtons = wrapper.findAll('.feedback-buttons button')
      expect(feedbackButtons.length).toBeGreaterThan(0)
    })
  })

  // ==================== 边界条件测试 (1 个) ====================

  describe('Edge Cases', () => {
    it('should handle empty message', async () => {
      wrapper = mount(SmartQuery, {
        global: {
          mocks: {
            $api: {
              postQuery: mockPostQuery,
              getSuggestedQuestions: mockGetSuggested
            }
          }
        }
      })

      await flushPromises()
      
      const input = wrapper.find('input')
      await input.setValue('')
      await input.trigger('keyup.enter')
      
      await flushPromises()
      // 空消息不应该发送
      expect(mockPostQuery).not.toHaveBeenCalled()
    })
  })
})
