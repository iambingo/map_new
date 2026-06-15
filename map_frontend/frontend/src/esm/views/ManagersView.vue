<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">管理人库 Manager Database</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">统一记录管理人机构信息、核心能力、尽调结论、合作状态与风险事件。</p>
  </div>
  <Panel>
    <div class="toolbar">
      <div class="filters">
        <input v-model="store.searchQuery" class="input" placeholder="搜索管理人、机构类型、策略" />
        <select v-model="store.ratingFilter" class="select">
          <option v-for="item in managerRatings" :key="item">{{ item }}</option>
        </select>
      </div>
      <span class="status-tag blue">当前显示 {{ store.filteredManagers.length }} 家</span>
    </div>
    <div class="table-wrap">
      <table class="fin-table esm-table dense-fin-table manager-fin-table">
        <thead>
          <tr>
            <th>管理人名称</th>
            <th>机构类型</th>
            <th>核心策略</th>
            <th>管理规模</th>
            <th>合作状态</th>
            <th>评级</th>
            <th>核心人员稳定性</th>
            <th>风控能力</th>
            <th>历史业绩</th>
            <th>策略容量</th>
            <th>最近尽调</th>
            <th>风险事件</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.filteredManagers" :key="item.name">
            <td><strong>{{ item.name }}</strong></td>
            <td>{{ item.orgType }}</td>
            <td class="cursor-pointer text-[#3B9EFF] hover:underline" @click="goToStrategy(item.coreStrategy)">{{ item.coreStrategy }}</td>
            <td class="num-cell">{{ item.aum }}</td>
            <td><StatusTag :value="item.cooperation" /></td>
            <td><StatusTag :value="item.rating" /></td>
            <td><StatusTag :value="item.peopleStability" /></td>
            <td>{{ item.riskControl }}</td>
            <td>{{ item.performance }}</td>
            <td class="num-cell">{{ item.capacity }}</td>
            <td class="mono">{{ item.lastDueDiligence }}</td>
            <td><StatusTag :value="item.hasRiskEvent" /></td>
          </tr>
          <tr v-if="store.filteredManagers.length === 0">
            <td class="empty" colspan="12">暂无匹配管理人</td>
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
import { useManagerStore } from '@esm/store/managerStore';
import { managerRatings } from '@esm/api/manager';

const route = useRoute();
const router = useRouter();
const store = useManagerStore();

function goToStrategy(coreStrategy: string) {
  router.push({ path: '/esm/strategies', query: { search: coreStrategy } });
}

onMounted(() => {
  store.load();
  if (route.query.search) store.searchQuery = route.query.search as string;
});
</script>

