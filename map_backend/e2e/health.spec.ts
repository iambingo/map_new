import { expect, test } from "./fixtures";

test.describe("健康检查", () => {
  test("GET /health 返回 ok", async ({ api }) => {
    const res = await api.get("/health");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body).toHaveProperty("version");
    expect(body.env).toBe("development");
  });

  test("GET / 返回服务信息", async ({ api }) => {
    const res = await api.get("/");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("service");
    expect(body.api_base).toBe("/api/v1");
  });
});
