/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COMMITTEE_OFFLINE_MOCK: string
  readonly VITE_ENABLED_MODULES: string
  readonly VITE_API_BASE_URL?: string
  readonly VITE_DEV_BEARER_TOKEN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}
