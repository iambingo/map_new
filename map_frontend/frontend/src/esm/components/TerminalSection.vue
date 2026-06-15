<template>
  <section class="border border-[var(--am-border)] bg-[var(--am-bg-panel)]">
    <header class="flex h-9 items-center justify-between border-b border-[var(--am-border-sub)] px-3">
      <div class="am-title-l2">
        <span class="am-title-bar"></span>
        <span>{{ title }}</span>
      </div>
      <slot name="actions"></slot>
    </header>
    <div class="p-3">
      <slot></slot>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
}>();
</script>

