<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">策略库 Strategy Inventory</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">按一级/二级分类沉淀收益来源、风险特征、容量、适配产品与状态。</p>
  </div>
  <Panel>
    <div class="toolbar">
      <div class="filters">
        <input v-model="store.searchQuery" class="input" placeholder="搜索策略、收益来源、产品类型" />
        <select v-model="store.categoryFilter" class="select">
          <option v-for="item in store.strategyClasses" :key="item">{{ item }}</option>
        </select>
        <select v-model="store.statusFilter" class="select">
          <option v-for="item in strategyStatuses" :key="item">{{ item }}</option>
        </select>
        <input v-model="store.createdMonthFilter" class="input compact month-input" type="month" />
      </div>
      <span class="status-tag blue">共 {{ store.filteredStrategies.length }} 条</span>
    </div>
    <div class="table-wrap">
      <table class="fin-table esm-table dense-fin-table strategy-fin-table">
        <thead>
          <tr>
            <th>策略名称</th>
            <th>一级分类</th>
            <th>二级分类</th>
            <th>收益来源</th>
            <th>风险特征</th>
            <th>波动率</th>
            <th>最大回撤</th>
            <th>流动性</th>
            <th>容量上限</th>
            <th>适配产品</th>
            <th>创建时间</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.filteredStrategies" :key="item.name" class="clickable-row" @click="router.push(`/esm/strategies/${item.id}`)">
            <td><strong>{{ item.name }}</strong></td>
            <td>{{ item.secondaryClass }}</td>
            <td>{{ item.source }}</td>
            <td>{{ item.risk }}</td>
            <td class="num-cell">{{ item.volatility }}</td>
            <td class="num-cell">{{ item.drawdown }}</td>
            <td class="mono">{{ item.liquidity }}</td>
            <td class="num-cell">{{ item.capacity }}</td>
            <td>{{ item.productFit }}</td>
            <td class="num-cell">{{ item.createdAt }}</td>
            <td><StatusTag :value="item.status" /></td>
          </tr>
          <tr v-if="store.filteredStrategies.length === 0">
            <td class="empty" colspan="12">暂无匹配策略</td>
          </tr>
        </tbody>
      </table>
    </div>
  </Panel>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Panel from '@esm/components/Panel.vue';
import StatusTag from '@esm/components/StatusTag.vue';
import { useStrategyStore } from '@esm/store/strategyStore';
import { strategyStatuses } from '@esm/api/strategy';

const route = useRoute();
const router = useRouter();
const store = useStrategyStore();

onMounted(() => {
  store.load();
  if (route.query.search) store.searchQuery = route.query.search as string;
  if (route.query.category) store.categoryFilter = route.query.category as string;
  if (route.query.status) store.statusFilter = route.query.status as string;
  if (route.query.createdMonth) store.createdMonthFilter = route.query.createdMonth as string;
});
</script>

<style scoped>
.clickable-row { cursor: pointer; }
.clickable-row:hover { background: rgba(59,158,255,0.06); }
</style>

