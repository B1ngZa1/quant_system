<template>
  <div class="tags-view">
    <div class="tags-wrapper">
      <el-tag
        v-for="tag in tagsViewList"
        :key="tag.path"
        :closable="tag.path !== '/dashboard'"
        :effect="isActive(tag.path) ? 'dark' : 'plain'"
        :type="isActive(tag.path) ? 'primary' : 'info'"
        class="tag-item"
        @click="handleClick(tag)"
        @close="handleClose(tag)"
        @contextmenu.prevent="handleContextMenu($event, tag)"
      >
        {{ tag.title }}
      </el-tag>
    </div>
    
    <!-- 右键菜单 -->
    <ul v-show="visible" :style="{ left: left + 'px', top: top + 'px' }" class="contextmenu">
      <li @click="refreshSelected">刷新页面</li>
      <li @click="closeSelected">关闭当前</li>
      <li @click="closeOthers">关闭其他</li>
      <li @click="closeAll">关闭所有</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store/modules/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const tagsViewList = computed(() => appStore.tagsViewList)
const visible = ref(false)
const top = ref(0)
const left = ref(0)
type TagViewItem = { name: string | symbol; path: string; title: string }
const selectedTag = ref<TagViewItem | null>(null)

const isActive = (path: string) => {
  return path === route.path
}

const addTag = () => {
  const { name, path, meta } = route
  if (name && meta?.title) {
    const routeName = typeof name === 'symbol' ? name.toString() : name
    appStore.addTagView({ name: routeName, path, meta: { title: meta.title as string } })
  }
}

const handleClick = (tag: { path: string }) => {
  router.push(tag.path)
}

const handleClose = (tag: { path: string }) => {
  appStore.removeTagView(tag.path)
  if (isActive(tag.path)) {
    const lastTag = tagsViewList.value[tagsViewList.value.length - 1]
    if (lastTag) {
      router.push(lastTag.path)
    } else {
      router.push('/dashboard')
    }
  }
}

const handleContextMenu = (e: MouseEvent, tag: TagViewItem) => {
  left.value = e.clientX
  top.value = e.clientY
  visible.value = true
  selectedTag.value = tag
}

const closeMenu = () => {
  visible.value = false
}

const refreshSelected = () => {
  if (selectedTag.value) {
    router.push(selectedTag.value.path)
  }
  closeMenu()
}

const closeSelected = () => {
  if (selectedTag.value) {
    handleClose(selectedTag.value)
  }
  closeMenu()
}

const closeOthers = () => {
  if (selectedTag.value) {
    appStore.closeOtherTags(selectedTag.value.path)
    router.push(selectedTag.value.path)
  }
  closeMenu()
}

const closeAll = () => {
  appStore.closeAllTags()
  router.push('/dashboard')
  closeMenu()
}

watch(() => route.path, addTag, { immediate: true })
watch(visible, (value) => {
  if (value) {
    document.body.addEventListener('click', closeMenu)
  } else {
    document.body.removeEventListener('click', closeMenu)
  }
})

onMounted(() => {
  addTag()
})

onBeforeUnmount(() => {
  document.body.removeEventListener('click', closeMenu)
})
</script>

<style lang="scss" scoped>
.tags-view {
  height: 40px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 4px 10px;
  
  .tags-wrapper {
    display: flex;
    gap: 8px;
    
    .tag-item {
      cursor: pointer;
      
      &:hover {
        opacity: 0.8;
      }
    }
  }
  
  .contextmenu {
    position: absolute;
    z-index: 3000;
    list-style: none;
    background: var(--el-bg-color);
    border-radius: 4px;
    box-shadow: var(--el-box-shadow-light);
    padding: 5px 0;
    margin: 0;
    border: 1px solid var(--el-border-color-light);
    
    li {
      padding: 8px 16px;
      cursor: pointer;
      font-size: 13px;
      
      &:hover {
        background: var(--el-fill-color-light);
      }
    }
  }
}
</style>
