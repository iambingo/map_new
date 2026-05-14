import { expect, test, apiUrl } from "./fixtures";

test.describe("跨域指令模块", () => {
  // 注意：此模块使用 CurrentUserID（严格 JWT），开发环境无 Token 时会 401
  // 需要后端生成有效 Token 或在 CI 中配置

  test("POST /commands 需要认证", async ({ api }) => {
    const res = await api.post(apiUrl("/orchestrator/commands"), {
      data: {
        command_type: "rebalance",
        payload: { reason: "E2E test" },
      },
    });
    // 开发环境无 Token 时预期 401
    expect(res.status()).toBe(401);
  });

  test("GET /commands/{task_id} 需要认证", async ({ api }) => {
    const res = await api.get(apiUrl("/orchestrator/commands/999"));
    expect(res.status()).toBe(401);
  });
});
