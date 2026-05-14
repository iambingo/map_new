import { APIRequestContext, expect, test as base } from "@playwright/test";

const API_PREFIX = "/api/v1";

type ApiFixture = {
  api: APIRequestContext;
};

export const test = base.extend<ApiFixture>({
  api: async ({ request }, use) => {
    await use(request);
  },
});

export { expect };

export function apiUrl(path: string) {
  return `${API_PREFIX}${path}`;
}
