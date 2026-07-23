/**
 * NEXUS Centralized API Client & Service Gateway
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("nexus_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("nexus_token");
    }
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}

export const ApiClient = {
  // Auth
  login: (credentials: any) => fetchApi("/api/auth/login", { method: "POST", body: JSON.stringify(credentials) }),
  getMe: () => fetchApi("/api/auth/me"),

  // Tasks
  getTasks: (investigationId?: string) => fetchApi(`/api/tasks${investigationId ? `?investigation_id=${investigationId}` : ''}`),
  createTask: (data: any) => fetchApi("/api/tasks", { method: "POST", body: JSON.stringify(data) }),
  startTask: (taskId: string) => fetchApi(`/api/tasks/${taskId}/start`, { method: "POST" }),
  completeTask: (taskId: string) => fetchApi(`/api/tasks/${taskId}/complete`, { method: "POST" }),

  // Assignments
  getAssignments: () => fetchApi("/api/assignment"),
  recommendAssignment: (data: any) => fetchApi("/api/assignment/recommend", { method: "POST", body: JSON.stringify(data) }),

  // Governance & Approvals
  getApprovals: (filters?: string) => fetchApi(`/api/approval/queue${filters || ''}`),
  submitApproval: (data: any) => fetchApi("/api/approval/submit", { method: "POST", body: JSON.stringify(data) }),
  actionApproval: (approvalId: string, action: string, comments?: string) =>
    fetchApi(`/api/approval/${approvalId}/action`, { method: "POST", body: JSON.stringify({ action, comments }) }),

  // Escalations
  getEscalations: () => fetchApi("/api/escalation/queue"),

  // Notifications
  getNotifications: () => fetchApi("/api/notification-hub/inbox"),

  // Executive Dashboard
  getExecutiveDashboard: () => fetchApi("/api/executive/dashboard"),

  // Audit Ledger
  getAuditHistory: (query?: string) => fetchApi(`/api/audit/history${query || ''}`),
  verifyAuditIntegrity: () => fetchApi("/api/audit/integrity/verify"),

  // Compliance
  getComplianceDashboard: () => fetchApi("/api/compliance/dashboard"),
  getComplianceViolations: () => fetchApi("/api/compliance/violations"),
};
