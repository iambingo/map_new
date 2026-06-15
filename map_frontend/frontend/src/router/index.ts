import { createRouter, createWebHashHistory } from 'vue-router';

export const ESM_ROUTE_NAMES = {
  dashboard: 'esm-dashboard',
  strategies: 'esm-strategies',
  strategyDetail: 'esm-strategy-detail',
  managers: 'esm-managers',
  spvPool: 'esm-spv-pool',
  workflow: 'esm-workflow',
  committee: 'esm-committee',
  kpi: 'esm-kpi',
  risk: 'esm-risk',
  ratings: 'esm-ratings',
} as const;

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'map-root', component: { template: '<span />' } },
    {
      path: '/esm',
      redirect: '/esm/dashboard',
      children: [
        { path: 'dashboard', name: ESM_ROUTE_NAMES.dashboard, component: () => import('@esm/views/DashboardView.vue') },
        { path: 'strategies', name: ESM_ROUTE_NAMES.strategies, component: () => import('@esm/views/StrategiesView.vue') },
        { path: 'strategies/:id', name: ESM_ROUTE_NAMES.strategyDetail, component: () => import('@esm/views/StrategyDetailView.vue') },
        { path: 'managers', name: ESM_ROUTE_NAMES.managers, component: () => import('@esm/views/ManagersView.vue') },
        { path: 'spv-pool', name: ESM_ROUTE_NAMES.spvPool, component: () => import('@esm/views/SpvPoolView.vue') },
        { path: 'workflow', name: ESM_ROUTE_NAMES.workflow, component: () => import('@esm/views/WorkflowView.vue') },
        { path: 'committee', name: ESM_ROUTE_NAMES.committee, component: () => import('@esm/views/CommitteeView.vue') },
        { path: 'kpi', name: ESM_ROUTE_NAMES.kpi, component: () => import('@esm/views/KpiView.vue') },
        { path: 'risk', name: ESM_ROUTE_NAMES.risk, component: () => import('@esm/views/RiskView.vue') },
        { path: 'ratings', name: ESM_ROUTE_NAMES.ratings, component: () => import('@esm/views/RatingsView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});

export default router;
