/** 特性开关白名单 — 控制模块按需上线 */

const RAW = import.meta.env.VITE_ENABLED_MODULES as string | undefined;

const _whitelist: string[] | null =
  RAW === 'all' || !RAW ? null : RAW.split(',').map((s) => s.trim()).filter(Boolean);

/**
 * 判断模块是否启用
 * @param moduleKey 模块标识，如 'committee'、'ficc'、'model-center'
 */
export function isModuleEnabled(moduleKey: string): boolean {
  if (_whitelist === null) return true; // 'all' 或未配置
  return _whitelist.includes(moduleKey);
}

/** 获取当前所有启用的模块 key（用于 fallback 导航） */
export function getEnabledModuleKeys(): string[] | null {
  return _whitelist;
}
