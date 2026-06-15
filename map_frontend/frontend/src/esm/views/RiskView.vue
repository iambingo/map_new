<template>
  <div class="mb-4">
    <h2 class="text-base font-semibold text-[#E8ECF4]">风险预警与退出机制</h2>
    <p class="mt-1 text-[11px] text-[#555E75]">围绕回撤、风格漂移、人员、流动性、杠杆、估值、信用与合规事件触发分层处置。</p>
  </div>
  <Panel>
    <div class="toolbar">
      <div class="filters">
        <select v-model="store.riskLevelFilter" class="select">
          <option v-for="item in riskLevels" :key="item">{{ item }}</option>
        </select>
      </div>
      <span class="status-tag red">高风险 {{ store.highRiskCount }} 项</span>
    </div>
    <div class="table-wrap">
      <table class="fin-table esm-table">
        <thead>
          <tr>
            <th>对象</th>
            <th>策略分类</th>
            <th>风险等级</th>
            <th>触发说明</th>
            <th>退出状态</th>
            <th>触发日期</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in store.filteredRiskEvents" :key="item.target">
            <td class="cursor-pointer text-[#3B9EFF] hover:underline" @click="goToStrategies(item.target)"><strong>{{ item.target }}</strong></td>
            <td class="cursor-pointer text-[#3B9EFF] hover:underline" @click="goToStrategies(item.strategyClass)">{{ item.strategyClass }}</td>
            <td><StatusTag :value="item.level" /></td>
            <td>{{ item.reason }}</td>
            <td><StatusTag :value="item.exitStatus" /></td>
            <td class="mono">{{ item.triggerDate }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </Panel>
  <div class="trigger-grid mt-3">
    <div v-for="(item, index) in riskTriggers" :key="item" class="terminal-card metric">
      <label>触发条件 {{ index + 1 }}</label>
      <strong>{{ item }}</strong>
      <span>自动生成观察、暂停、压降或退出建议</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import Panel from '@esm/components/Panel.vue';
import StatusTag from '@esm/components/StatusTag.vue';
import { useRiskStore } from '@esm/store/riskStore';
import { riskLevels } from '@esm/api/risk';

const route = useRoute();
const router = useRouter();
const store = useRiskStore();

function goToStrategies(search: string) {
  router.push({ path: '/esm/strategies', query: { search } });
}

const riskTriggers = ['最大回撤超过阈值', '风格漂移', '核心人员离职', '流动性恶化', '杠杆异常', '估值异常', '业绩持续低于基准', '发生信用事件', '发生合规或风控事件'];

onMounted(() => {
  store.load();
  if (route.query.level) store.riskLevelFilter = route.query.level as string;
});
</script>

