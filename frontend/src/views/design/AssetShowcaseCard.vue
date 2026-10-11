<template>
  <article
    v-if="visible"
    class="asset-card"
    :class="`asset-card--${statusClass}`"
    :aria-labelledby="`${asset.id}-title`"
  >
    <header class="asset-card__header">
      <div class="asset-card__heading">
        <h3 :id="`${asset.id}-title`">{{ asset.name }}</h3>
        <p>{{ asset.description }}</p>
      </div>
      <span class="asset-status" :class="`asset-status--${statusClass}`">{{ asset.status }}</span>
    </header>

    <div class="asset-card__preview">
      <slot />
    </div>

    <footer class="asset-card__meta">
      <span class="asset-card__meta-label">源码 / 资源</span>
      <code>{{ asset.source }}</code>
      <span v-if="asset.packageSource" class="asset-card__package">第三方来源：{{ asset.packageSource }}</span>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AssetCatalogEntry } from './assetCatalog'

const props = withDefaults(defineProps<{
  asset: AssetCatalogEntry
  visible?: boolean
}>(), {
  visible: true,
})

const statusClass = computed(() => ({
  '实际组件': 'active',
  '静态演示': 'demo',
  '合成样本': 'synthetic',
  '历史参考': 'historical',
  '未挂载': 'unmounted',
}[props.asset.status]))
</script>
