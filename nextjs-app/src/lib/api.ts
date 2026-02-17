import { ChatMessage } from "@/types/chat";
import { Email } from "@/types/email";
import { Projekt } from "@/types/projekt";
import { User } from "@/types/user";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://192.168.0.66:8000/api";

function getHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

// Auth
export async function apiLogin(username: string, password: string) {
  return request<{ access_token: string; refresh_token: string; token_type: string }>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ username, password }) }
  );
}

export async function apiGetMe() {
  return request<User>("/auth/me");
}

export async function apiRefreshToken(refreshToken: string) {
  return request<{ access_token: string; refresh_token: string; token_type: string }>(
    "/auth/refresh",
    { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) }
  );
}

// Chat
export async function apiSendMessage(message: string, projektId?: number) {
  const data = await request<Record<string, unknown>>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, ...(projektId ? { projekt_id: projektId } : {}) }),
  });
  return parseChatMessage(data, "agent");
}

export async function apiGetChatHistory(projektId?: number): Promise<ChatMessage[]> {
  const path = projektId ? `/chat/history/${projektId}` : "/chat/history";
  const data = await request<{ history: Record<string, unknown>[] }>(path);
  return (data.history || []).map((m) => parseChatMessage(m));
}

export async function apiConfirmAction(actionId: string) {
  return request<void>(`/chat/actions/${actionId}/confirm`, { method: "POST" });
}

export async function apiRejectAction(actionId: string) {
  return request<void>(`/chat/actions/${actionId}/reject`, { method: "POST" });
}

// Projects
export async function apiGetProjekti(params?: { faza?: string }) {
  const query = params?.faza ? `?faza=${encodeURIComponent(params.faza)}` : "";
  const data = await request<{ projekti: Record<string, unknown>[] }>(`/projekti${query}`);
  return (data.projekti || []).map(parseProjekt);
}

export async function apiGetProjekt(id: number) {
  const data = await request<Record<string, unknown>>(`/projekti/${id}`);
  return parseProjekt(data);
}

// Emails
export async function apiGetEmaili(params?: { kategorija?: string; rfqPodkategorija?: string }) {
  const parts: string[] = [];
  if (params?.kategorija) parts.push(`kategorija=${encodeURIComponent(params.kategorija)}`);
  if (params?.rfqPodkategorija) parts.push(`rfq_podkategorija=${encodeURIComponent(params.rfqPodkategorija)}`);
  const query = parts.length > 0 ? `?${parts.join("&")}` : "";
  const data = await request<{ emaili: Record<string, unknown>[] }>(`/emaili${query}`);
  return (data.emaili || []).map(parseEmail);
}

export async function apiGetEmailAnalysis(emailId: number) {
  return request<Record<string, unknown>>(`/emaili/${emailId}/analysis`);
}

export async function apiTriggerAnalysis(emailId: number) {
  return request<Record<string, unknown>>(`/emaili/${emailId}/analyze`, { method: "POST" });
}

// Parsers
function parseChatMessage(data: Record<string, unknown>, defaultRole?: string): ChatMessage {
  return {
    role: (data.role as ChatMessage["role"]) || (defaultRole as ChatMessage["role"]) || "agent",
    content: (data.content as string) || (data.response as string) || "",
    timestamp: (data.timestamp as string) || new Date().toISOString(),
    projektId: data.projekt_id as number | undefined,
    needsConfirmation: (data.needs_confirmation as boolean) || false,
    actions: data.actions as ChatMessage["actions"],
    suggestedCommands: data.suggested_commands as string[] | undefined,
  };
}

function parseProjekt(data: Record<string, unknown>): Projekt {
  return {
    id: data.id as number,
    stevilkaProjekta: (data.stevilka_projekta as string) || "",
    naziv: (data.naziv as string) || "",
    strankaId: data.stranka_id as number | undefined,
    faza: (data.faza as string) || "",
    status: (data.status as string) || "",
    datumRfq: (data.datum_rfq as string) || "",
    datumZakljucka: data.datum_zakljucka as string | undefined,
    opombe: data.opombe as string | undefined,
  };
}

function parseEmail(data: Record<string, unknown>): Email {
  return {
    id: data.id as number,
    zadeva: data.zadeva as string | undefined,
    posiljatelj: data.posiljatelj as string | undefined,
    prejemniki: data.prejemniki as string | undefined,
    kategorija: data.kategorija as string | undefined,
    rfqPodkategorija: data.rfq_podkategorija as string | undefined,
    status: data.status as string | undefined,
    datum: data.datum as string | undefined,
    analizaStatus: data.analiza_status as string | undefined,
    analizaRezultat: data.analiza_rezultat as Record<string, unknown> | undefined,
    priloge: data.priloge as Email["priloge"],
    izvleceniPodatki: data.izvleceni_podatki as Record<string, unknown> | undefined,
  };
}
