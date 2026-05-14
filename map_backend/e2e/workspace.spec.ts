import { expect, test, apiUrl } from "./fixtures";

test.describe("智能门户 BFF", () => {
  test("GET /portal-snapshot 返回门户快照", async ({ api }) => {
    const res = await api.get(apiUrl("/workspace/portal-snapshot"));
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("snapshot_at");
    expect(body).toHaveProperty("is_stale");
  });
});
