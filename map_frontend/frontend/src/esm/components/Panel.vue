<template>
  <section class="terminal-card panel">
    <header v-if="title" class="panel-head">
      <div class="panel-title">
        <span class="title-bar" />
        <span>{{ title }}</span>
      </div>
      <span v-if="tag" :class="['status-tag', tagTone]">{{ tag }}</span>
    </header>
    <div class="panel-body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title?: string;
  tag?: string;
  tagTone?: string;
}>(), {
  tagTone: 'blue',
});
</script>

