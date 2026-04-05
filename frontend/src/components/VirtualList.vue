<template>
  <div class="virtual-list" :style="{ height: totalHeight + 'px' }">
    <div class="virtual-list-content" :style="contentStyle">
      <div
        v-for="item in visibleItems"
        :key="item[keyField]"
        class="virtual-list-item"
        :style="getItemStyle(item)"
      >
        <slot :item="item" :index="item[indexKey]"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  data: any[]
  itemHeight?: number
  height?: number
  keyField?: string
  indexKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  itemHeight: 60,
  height: 500,
  keyField: 'id',
  indexKey: 'index'
})

const scrollTop = ref(0)
const containerRef = ref<HTMLElement | null>(null)

// 计算可见区域
const visibleCount = computed(() => Math.ceil(props.height / props.itemHeight) + 2)
const startIndex = computed(() => Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - 1))
const endIndex = computed(() => Math.min(props.data.length, startIndex.value + visibleCount.value))

// 可见项
const visibleItems = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value).map((item, index) => ({
    ...item,
    [props.indexKey]: startIndex.value + index
  }))
})

// 内容高度
const totalHeight = computed(() => props.data.length * props.itemHeight)

// 内容样式
const contentStyle = computed(() => ({
  transform: `translateY(${startIndex.value * props.itemHeight}px)`
}))

// 项样式
function getItemStyle(item: any) {
  return {
    height: props.itemHeight + 'px',
    position: 'absolute' as const,
    top: '0',
    width: '100%'
  }
}

// 滚动处理
function handleScroll(event: Event) {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
}

// 暴露方法
defineExpose({
  scrollTo: (index: number) => {
    if (containerRef.value) {
      containerRef.value.scrollTop = index * props.itemHeight
    }
  },
  scrollToTop: () => {
    if (containerRef.value) {
      containerRef.value.scrollTop = 0
    }
  }
})
</script>

<style scoped>
.virtual-list {
  position: relative;
  overflow-y: auto;
  will-change: transform;
}

.virtual-list-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  will-change: transform;
}

.virtual-list-item {
  box-sizing: border-box;
  border-bottom: 1px solid #e0e0e0;
  background: white;
}
</style>
