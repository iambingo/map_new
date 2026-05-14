import { expect, test, apiUrl } from "./fixtures";

let meetingId: number;

test.describe("投委会模块", () => {
  test("GET /page-context 无数据时返回空上下文", async ({ api }) => {
    const res = await api.get(apiUrl("/committee/page-context"));
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("meeting");
    expect(body).toHaveProperty("votes");
  });

  test("POST /meetings 创建会议", async ({ api }) => {
    const res = await api.post(apiUrl("/committee/meetings"), {
      data: {
        meeting_code: `E2E-${Date.now()}`,
        title: "E2E 测试会议",
        type: "mixed",
      },
    });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.id).toBeDefined();
    expect(body.status).toBe("draft");
    meetingId = body.id;
  });

  test("GET /meetings 列表包含已创建会议", async ({ api }) => {
    const res = await api.get(apiUrl("/committee/meetings"));
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(Array.isArray(body)).toBeTruthy();
  });

  test("POST /meetings/{id}/submit-vote 提交投票", async ({ api }) => {
    test.skip(!meetingId, "需要先创建会议");
    const res = await api.post(
      apiUrl(`/committee/meetings/${meetingId}/submit-vote`),
      {
        data: {
          committee_type: "mixed",
          vote_dimension: "monthly",
          section_a: { 红利: 4, 偏股混: 3 },
          section_b: { 红利: true },
          section_c: ["利率债"],
          core_view: "E2E 测试观点",
          risk_flag: false,
        },
      }
    );
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.meeting_id).toBe(meetingId);
  });

  test("POST /meetings/{id}/publish 发布决议", async ({ api }) => {
    test.skip(!meetingId, "需要先创建会议");
    const res = await api.post(
      apiUrl(`/committee/meetings/${meetingId}/publish`)
    );
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("meeting");
    expect(body).toHaveProperty("resolution");
  });

  test("POST /meetings/{id}/resolution 保存主任委员决议", async ({ api }) => {
    test.skip(!meetingId, "需要先创建会议");
    const res = await api.post(
      apiUrl(`/committee/meetings/${meetingId}/resolution`),
      {
        data: {
          bond_grade: "中",
          bond_duration: "3-5年",
          equity_grade: 3,
          equity_grade_label: "中性",
        },
      }
    );
    expect(res.status()).toBe(201);
  });

  test("GET /mixed/sessions 返回提交列表", async ({ api }) => {
    const res = await api.get(apiUrl("/committee/mixed/sessions"));
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("submissions");
  });

  test("GET /mixed/sessions/history 返回历史统计", async ({ api }) => {
    const res = await api.get(apiUrl("/committee/mixed/sessions/history"));
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toHaveProperty("sessions");
  });

  test("POST /mixed/remind 发送催办", async ({ api }) => {
    const res = await api.post(apiUrl("/committee/mixed/remind"), {
      data: { member_name: "测试委员" },
    });
    expect(res.ok()).toBeTruthy();
  });

  test("DELETE /meetings/{id} 软删除会议", async ({ api }) => {
    test.skip(!meetingId, "需要先创建会议");
    const res = await api.delete(
      apiUrl(`/committee/meetings/${meetingId}`)
    );
    expect(res.status()).toBe(204);
  });
});
