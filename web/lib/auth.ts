"use client";

// Client-side auth helpers. The actual gate is the HttpOnly `auth_ok` cookie set
// by /api/login and checked in middleware; the display name is non-sensitive UI
// state kept in localStorage (FR-001).

const DISPLAY_NAME_KEY = "display_name";

export function getDisplayName(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(DISPLAY_NAME_KEY);
}

export function setDisplayName(name: string): void {
  window.localStorage.setItem(DISPLAY_NAME_KEY, name);
}

export async function login(password: string, displayName: string): Promise<void> {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error === "invalid" ? "Incorrect password." : "Login failed.");
  }
  setDisplayName(displayName);
}

export async function logout(): Promise<void> {
  await fetch("/api/logout", { method: "POST" });
  window.localStorage.removeItem(DISPLAY_NAME_KEY);
}
