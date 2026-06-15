# MAP Frontend-Backend API Interface Specification

> Document version: v1.0 | Date: 2026-05-07
> Frontend stack: Vue 3 + TypeScript + Axios
> Base URL: configured via `VITE_API_BASE_URL` env variable (defaults to `/api`)
> Auth: JWT Bearer token in `Authorization` header

---

## Overview

| # | Method | Path | Description | Caller |
|---|--------|------|-------------|--------|
| 1 | GET | `/v1/workspace/portal-snapshot` | Portal snapshot with TAA guidance | demoStore |
| 2 | GET | `/v1/committee/page-context` | Committee meeting context + votes | demoStore |
| 3 | GET | `/v1/committee/meetings` | List committee meetings | CommitteeView |
| 4 | POST | `/v1/committee/meetings` | Create a new meeting | CommitteeView |
| 5 | DELETE | `/v1/committee/meetings/{id}` | Delete a meeting | CommitteeView |
| 6 | POST | `/v1/committee/meetings/{meetingId}/submit-vote` | Submit vote (self or proxy) | CommitteeView / demoStore |
| 7 | GET | `/v1/committee/mixed/sessions` | Load mixed committee submissions | CommitteeView |
| 8 | GET | `/v1/committee/mixed/sessions/history` | Load historical vote sessions | CommitteeView |
| 9 | POST | `/v1/committee/mixed/remind` | Send reminder to a member | CommitteeView |

---

## 1. GET `/v1/workspace/portal-snapshot`

Portal homepage snapshot. Contains TAA guidance (committee resolution results), positions, deviation analysis, and rebalance urgency.

### Request

**Query Params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Yes | User role enum: `ADMIN`, `COMMITTEE_MEMBER`, `PM`, `ANALYST`, `COMMITTEE_SECRETARY`, `COMMITTEE_CHAIR`, `FICC_SECRETARY`, `FICC_MEMBER`, `FICC_CHAIR` |

### Response 200

```typescript
interface PortalSnapshot {
  snapshot_at: string;                    // ISO datetime, snapshot generation time
  is_stale: boolean;                      // whether snapshot data is outdated
  stale_reason: string | null;            // reason if stale
  taa_guidance: {
    source_resolution: {
      resolution_id?: number;
      meeting_id?: number;
      published_at?: string | null;
    } | null;
    choice_results: Record<string, {      // key: "equity_view" | "bond_view" | "commodity_view" | "cash_view"
      winner: string;                     // "overweight" | "neutral" | "underweight"
      vote_counts: Record<string, number>; // e.g. { "overweight": 3, "neutral": 2, "underweight": 1 }
    }>;
    numeric_results: Record<string, Record<string, unknown>>;
    published_at: string | null;
  };
  positions: Record<string, unknown> | null;
  deviation_analysis: Record<string, unknown>;
  rebalance_urgency: {
    level: string;                        // e.g. "high", "medium", "low"
    reason: string;
  };
  navigation_tiles: Array<Record<string, unknown>>;
}
```

### Notes
- Role mapping from frontend Chinese role names to English enum values is handled client-side in `demoStore.ts:ROLE_QUERY`.
- Frontend maps `choice_results` into a decision table for the committee resolution display.
- Winner values: `overweight` -> optimistic, `neutral` -> neutral, `underweight` -> cautious.

---

## 2. GET `/v1/committee/page-context`

Committee page read-only context. Returns meeting metadata, resolution summary, and submitted vote rows. Called in parallel with portal-snapshot via `Promise.allSettled`.

### Request

No query params required.

### Response 200

```typescript
interface CommitteePageContextDTO {
  meeting: {
    id: number;
    meeting_code: string;
    title: string;
    type: string;                         // e.g. "mixed", "ficc"
    status: string;                       // e.g. "open", "closed"
    scheduled_at: string | null;
    created_by: number;
    created_at: string;
    updated_at: string;
  } | null;
  resolution: {
    id: number;
    meeting_id: number;
    aggregated_taa: Record<string, unknown>;  // same structure as portal-snapshot choice_results
    ai_minutes: string | null;
    published_at: string | null;
    published_by: number | null;
    created_at: string;
  } | null;
  votes: Array<{
    user_id: number;
    submitted_at: string | null;
  }>;
}
```

### Notes
- If `resolution.aggregated_taa` contains `choice_results`, frontend uses it as fallback when portal-snapshot has no data.
- `votes` array is used to show vote submission progress (how many members have voted).

---

## 3. GET `/v1/committee/meetings`

List all committee meetings. Used in the meeting management panel.

### Request

No query params required.

### Response 200

```typescript
// Returns array of meeting objects
type MeetingListResponse = Array<{
  id: number;
  meeting_code: string;
  title: string;
  type: string;                           // "mixed" | "ficc"
  status: string;                         // "draft" | "open" | "voting" | "closed"
  scheduled_at: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}>;
```

### Notes
- Frontend falls back to mock data (`MOCK_MEETINGS`) when global mock mode is on or API fails.

---

## 4. POST `/v1/committee/meetings`

Create a new committee meeting. Called by the secretary when initiating a new meeting session.

### Request Body

```typescript
{
  meeting_code: string;                   // auto-generated format: "IC-YYYYMMDD-XXXX"
  title: string;                          // meeting title
  type: string;                           // "mixed" | "ficc"
  scheduled_at?: string;                  // ISO datetime, optional
}
```

### Response 201

```typescript
{
  id: number;
  meeting_code: string;
  title: string;
  type: string;
  status: string;
  scheduled_at: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}
```

### Notes
- Frontend generates `meeting_code` client-side via `buildUniqueMeetingCode()`.
- After successful creation, frontend re-fetches the meeting list (`loadMeetings`).
- Has retry logic: up to 3 attempts on failure.

---

## 5. DELETE `/v1/committee/meetings/{id}`

Delete a committee meeting by ID.

### Request

**Path Params:**

| Param | Type | Description |
|-------|------|-------------|
| `id` | number | Meeting ID |

### Response 204

Empty response on success.

### Notes
- Only called when not in mock mode (`skipCommitteeHttp()` is false).
- On failure, shows alert to user and does NOT remove from local list.

---

## 6. POST `/v1/committee/meetings/{meetingId}/submit-vote`

Submit a committee member's vote. Supports both self-submission and proxy submission (secretary filling in for a member).

### Request

**Path Params:**

| Param | Type | Description |
|-------|------|-------------|
| `meetingId` | number | Meeting ID |

**Body:**

```typescript
{
  // Standard vote payload
  votes: Record<string, string>;          // asset name -> vote level
                                          // e.g. { "利率(10Y)": "中性偏乐观", "红利": "乐观" }
  core_view: string;                      // overall market view text
  risk_flag: boolean;                     // whether member flagged risk

  // Proxy submission fields (only when secretary fills in for a member)
  target_member_id?: string;              // the member ID being filled in for
  is_proxy?: boolean;                     // true when this is a proxy submission
  proxy_submitter_role?: string;          // the secretary's role identifier
}
```

### Response 200

```typescript
{
  success: boolean;
  vote_id?: number;
}
```

### Notes
- `votes` keys must match `细分策略` field from the unified vote config (`UNIFIED_VOTE_CONFIG`).
- Vote levels: `"谨慎"` | `"中性偏谨慎"` | `"中性"` | `"中性偏乐观"` | `"乐观"`.
- Proxy mode: when `target_member_id` is provided, `is_proxy` is automatically set to `true`.
- Frontend also maintains local state (`memberSubmissions`) for immediate UI update.

---

## 7. GET `/v1/committee/mixed/sessions`

Load all submission data for the mixed committee. Returns each member's questionnaire responses.

### Request

No query params required.

### Response 200

```typescript
{
  submissions: Array<{
    submitter_id: number;
    submitted_at: string;
    questionnaire_json: {
      // Member's votes for each asset
      [assetName: string]: string;        // asset -> vote level
    };
    // May include additional fields from the questionnaire
    core_view?: string;
    risk_flag?: boolean;
  }>;
}
```

### Notes
- Frontend maps `submitter_id` to member IDs (e.g., `m${submitter_id}`) for local state.
- Falls back to `MOCK_SUBMISSIONS_RAW` on failure.

---

## 8. GET `/v1/committee/mixed/sessions/history`

Load historical vote session data for trend comparison.

### Request

**Query Params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | No | Max sessions to return (default: 10) |

### Response 200

```typescript
{
  sessions: Array<{
    session_code: string;                 // e.g. "IC2026Q2"
    submitted_count: number;              // number of members who voted
    scores: Record<string, {              // key: asset name
      avg: number;                        // weighted average score (1-5)
      max: number;                        // highest score
      min: number;                        // lowest score
      count: number;                      // total votes
    }>;
  }>;
}
```

### Notes
- Used for the "historical votes" comparison feature in the decision tab.
- `session_code` is reformatted client-side for display (e.g., inserting space before "Q").

---

## 9. POST `/v1/committee/mixed/remind`

Send a reminder notification to a committee member who hasn't submitted their vote.

### Request Body

```typescript
{
  member_name: string;                    // display name of the member
  member_id?: number;                     // optional member ID
}
```

### Response 200

```typescript
{
  success: boolean;
}
```

### Notes
- Called by the secretary via the "remind" button next to each unsubmitted member.
- Frontend shows success/failure alert immediately after response.

---

## Error Response Format

All endpoints return errors in this structure:

```typescript
{
  detail: string;                         // human-readable error message
}
```

Common HTTP status codes:
- `401 Unauthorized` - Invalid or expired JWT token
- `404 Not Found` - Resource (meeting, session) not found
- `422 Unprocessable Entity` - Request body validation error
- `500 Internal Server Error` - Server-side error

---

## Authentication

All requests include `Authorization: Bearer <JWT>` header.

JWT payload structure (expected):
```json
{
  "sub": "<user_id>",
  "exp": "<unix_timestamp>"
}
```

Development token is hardcoded in `frontend/src/api/request.ts` with `sub=1`.
Backend should support `POST /auth/token` or similar endpoint for token issuance in production.

---

## Mock Mode

Frontend has a global mock mode toggle (`MAP_GLOBAL_MOCK` in localStorage).
When active, all API calls are skipped and mock data is returned from `demoStore.ts`.

Environment variable `VITE_COMMITTEE_OFFLINE_MOCK=true` enables committee-specific offline mock mode.

The `useApi()` helper in `demoStore.ts` provides automatic fallback:
- If global mock is on -> returns mock data immediately
- If API call fails -> logs warning and returns mock data as fallback

---

## Data Flow Diagram

```
Frontend (Vue 3)                    Backend (BFF/API Gateway)
────────────────                    ────────────────────────

  MapPortal.vue ──── GET /v1/workspace/portal-snapshot?role=PM
                     ◄─────────────── PortalSnapshot

  CommitteeView.vue ─┬─ GET /v1/workspace/portal-snapshot?role=...
                     │  GET /v1/committee/page-context
                     │  ◄─────────────── (parallel, allSettled)
                     │
                     ├─ GET /v1/committee/meetings
                     │  ◄─────────────── Meeting[]
                     │
                     ├─ POST /v1/committee/meetings
                     │  ◄─────────────── Meeting
                     │
                     ├─ DELETE /v1/committee/meetings/{id}
                     │  ◄─────────────── 204
                     │
                     ├─ POST /v1/committee/meetings/{id}/submit-vote
                     │  ◄─────────────── { success }
                     │
                     ├─ GET /v1/committee/mixed/sessions
                     │  ◄─────────────── { submissions }
                     │
                     ├─ GET /v1/committee/mixed/sessions/history?limit=10
                     │  ◄─────────────── { sessions }
                     │
                     └─ POST /v1/committee/mixed/remind
                        ◄─────────────── { success }
```

---

*Document generated from frontend codebase analysis. All request/response types derived from TypeScript interfaces in `demoStore.ts`, `CommitteeView.vue`, and `request.ts`.*
