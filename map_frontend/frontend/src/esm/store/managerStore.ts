import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { Manager } from '@esm/types/domain';
import { fetchManagers, managerRatings } from '@esm/api/manager';

export const useManagerStore = defineStore('manager', () => {
  const managers = ref<Manager[]>([]);
  const searchQuery = ref('');
  const ratingFilter = ref('全部');

  const filteredManagers = computed(() =>
    managers.value.filter(item =>
      (ratingFilter.value === '全部' || item.rating === ratingFilter.value)
      && Object.values(item).join('').toLowerCase().includes(searchQuery.value.toLowerCase()),
    ),
  );

  const ratingLevels = computed(() => [
    { name: 'A类：核心合作', desc: '长期业绩稳健、风控强、信息披露透明，可作为核心配置与重点额度承接方。', count: String(managers.value.filter(m => m.rating === 'A').length), quota: '可配置核心额度，允许滚动扩容', risk: '季度复核，重大事项 T+1 上报' },
    { name: 'B类：观察池', desc: '策略有价值但仍需验证容量、稳定性或团队持续性。', count: String(managers.value.filter(m => m.rating === 'B').length), quota: '小额度试投或观察额度', risk: '月度跟踪，触发指标加密复核' },
    { name: 'C类：战术使用', desc: '适合阶段性机会或特定市场环境，容量与回撤约束较强。', count: String(managers.value.filter(m => m.rating === 'C').length), quota: '项目制额度，不做长期承诺', risk: '周度监测，严格止损与到期复盘' },
    { name: 'D类：淘汰', desc: '存在重大风险事件、持续低于基准或配合度不足。', count: String(managers.value.filter(m => m.rating === 'D').length), quota: '不新增，存量退出或封存', risk: '退出报告归档，限制重新准入' },
  ]);

  async function load() {
    managers.value = await fetchManagers();
  }

  return { managers, searchQuery, ratingFilter, filteredManagers, ratingLevels, managerRatings, load };
});

