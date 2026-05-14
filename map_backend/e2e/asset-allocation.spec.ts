import { expect, test, apiUrl } from "./fixtures";

let draftId: number;

test.describe("资配业务模块", () => {
  test("GET /asset-classes 返回资产类别", async ({ api }) => {
    const res = await api.get(apiUrl("/asset-allocation/asset-classes"));
    expect(res.ok()).toBeTruthy();
  });

  test("GET /drafts 返回草稿列表", async ({ api }) => {
    const res = await api.get(apiUrl("/asset-allocation/drafts"));
    expect(res.ok()).toBeTruthy();
  });

  test("POST /drafts/calculate 计算并保存草稿", async ({ api }) => {
    const res = await api.post(apiUrl("/asset-allocation/drafts/calculate"), {
      data: {
        risk_level: 3,
        total_amount: 1000000,
        notes: "E2E 测试草稿",
      },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    if (body.data?.id) {
      draftId = body.data.id;
    }
  });

  test("GET /drafts/{id} 获取草稿详情", async ({ api }) => {
    test.skip(!draftId, "需要先创建草稿");
    const res = await api.get(apiUrl(`/asset-allocation/drafts/${draftId}`));
    expect(res.ok()).toBeTruthy();
  });

  test("POST /drafts/{id}/submit 提交草稿", async ({ api }) => {
    test.skip(!draftId, "需要先创建草稿");
    const res = await api.post(
      apiUrl(`/asset-allocation/drafts/${draftId}/submit`)
    );
    expect(res.ok()).toBeTruthy();
  });

  test("POST /drafts/{id}/approve 需要 JWT 认证", async ({ api }) => {
    test.skip(!draftId, "需要先创建草稿");
    const res = await api.post(
      apiUrl(`/asset-allocation/drafts/${draftId}/approve`)
    );
    // approve 使用 CurrentUserID，无 Token 预期 401
    expect(res.status()).toBe(401);
  });

  test("POST /drafts/{id}/reject 需要 JWT 认证", async ({ api }) => {
    test.skip(!draftId, "需要先创建草稿");
    const res = await api.post(
      apiUrl(`/asset-allocation/drafts/${draftId}/reject`),
      { data: { reason: "E2E 测试拒绝" } }
    );
    expect(res.status()).toBe(401);
  });
});
