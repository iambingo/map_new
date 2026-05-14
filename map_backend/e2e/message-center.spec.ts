import http from "node:http";
import { expect, test, apiUrl } from "./fixtures";

test.describe("消息中心模块", () => {
  test("GET /events/stream SSE 连接", async () => {
    const url = new URL(apiUrl("/messages/events/stream"), "http://localhost:8001");
    const { statusCode, headers } = await new Promise<{
      statusCode: number;
      headers: Record<string, string | string[] | undefined>;
    }>((resolve, reject) => {
      const req = http.get(url, (res) => {
        resolve({ statusCode: res.statusCode!, headers: res.headers });
        req.destroy();
      });
      req.on("error", reject);
      setTimeout(() => {
        req.destroy();
        reject(new Error("SSE connection timeout"));
      }, 5000);
    });
    expect(statusCode).toBe(200);
    expect(headers["content-type"]).toContain("text/event-stream");
  });

  test("POST /webhooks/signal 接收外部信号（无需认证）", async ({ api }) => {
    const res = await api.post(apiUrl("/messages/webhooks/signal"), {
      data: {
        source: "e2e-test",
        event_type: "test-signal",
        payload: { message: "E2E 测试信号" },
      },
    });
    expect(res.status()).toBe(202);
    const body = await res.json();
    expect(body.accepted).toBe(true);
  });
});
