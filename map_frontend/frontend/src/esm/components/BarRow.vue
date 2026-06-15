<template>
  <div class="bar-row cursor-pointer" @click="$emit('click')">
    <span class="bar-label">{{ label }}</span>
    <div class="progress" role="presentation">
      <span
        class="progress-fill"
        :style="{
          display: 'block',
          width: `${pct}%`,
          height: '100%',
          borderRadius: 'inherit',
          background: 'linear-gradient(90deg, var(--am-brand), var(--am-accent-cyan))',
        }"
      />
    </div>
    <strong class="bar-value">{{ value }}</strong>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: number;
  pct: number;
}>();

defineEmits<{
  click: [];
}>();
</script>

