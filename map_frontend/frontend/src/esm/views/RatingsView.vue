<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">管理人评级体系</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">以 A/B/C/D 四类管理人评级联动额度、风险要求与合作策略。</p>
  </div>
  <div class="rating-grid">
    <div v-for="item in store.ratingLevels" :key="item.name" class="terminal-card rating-box">
      <h3>{{ item.name }}</h3>
      <p class="muted">{{ item.desc }}</p>
      <div class="rating-count">
        <label>管理人数量</label>
        <strong class="mono">{{ item.count }}</strong>
      </div>
      <p><strong>额度规则：</strong>{{ item.quota }}</p>
      <p><strong>风险要求：</strong>{{ item.risk }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useManagerStore } from '@esm/store/managerStore';

const store = useManagerStore();

onMounted(() => { store.load(); });
</script>

