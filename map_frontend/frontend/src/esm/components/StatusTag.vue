<template>
  <span :class="['status-tag', tone]">{{ value }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{ value: string }>();

const tone = computed(() => {
  const v = props.value;
  if (['已准入', '已通过', '正常', 'A', '低', '核心合作', '否', '在投'].includes(v)) return 'green';
  if (['观察池', '进行中', '待上会', '材料复核', 'B', '中', '观察', '待审批'].includes(v)) return 'blue';
  if (['研究中', '补充材料', '暂停', '暂停新增', 'C', '中高', '压降规模', '战术使用'].includes(v)) return 'orange';
  if (['退出', '驳回', 'D', '高', '淘汰', '是', '已退出'].includes(v)) return 'red';
  return 'gray';
});
</script>

