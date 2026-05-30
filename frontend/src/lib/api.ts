const API = process.env.NEXT_PUBLIC_API_URL || "";

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return data;
}

// ── 小说 ──
export const api = {
  novels: {
    list: () => request("/api/v1/novels"),
    create: (data: { title: string; genre_id: string; writing_style?: string; target_word_count?: number }) =>
      request("/api/v1/novels", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => request(`/api/v1/novels/${id}`),
    update: (id: string, data: Record<string, any>) =>
      request(`/api/v1/novels/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    delete: (id: string) => request(`/api/v1/novels/${id}`, { method: "DELETE" }),
  },

  genre: {
    list: () => request("/api/v1/genre/list"),
    detail: (id: string) => request(`/api/v1/genre/${id}`),
  },

  world: {
    list: (novelId: string) => request(`/api/v1/novels/${novelId}/world`),
    create: (novelId: string, data: Record<string, any>) =>
      request(`/api/v1/novels/${novelId}/world`, { method: "POST", body: JSON.stringify(data) }),
  },

  characters: {
    list: (novelId: string) => request(`/api/v1/novels/${novelId}/characters`),
    create: (novelId: string, data: Record<string, any>) =>
      request(`/api/v1/novels/${novelId}/characters`, { method: "POST", body: JSON.stringify(data) }),
    update: (novelId: string, charId: string, data: Record<string, any>) =>
      request(`/api/v1/novels/${novelId}/characters/${charId}`, { method: "PATCH", body: JSON.stringify(data) }),
    delete: (novelId: string, charId: string) =>
      request(`/api/v1/novels/${novelId}/characters/${charId}`, { method: "DELETE" }),
    autoGenerate: (novelId: string) =>
      request(`/api/v1/novels/${novelId}/characters/auto`, { method: "POST" }),
  },

  chapters: {
    list: (novelId: string) => request(`/api/v1/novels/${novelId}/chapters`),
    get: (novelId: string, chId: string) => request(`/api/v1/novels/${novelId}/chapters/${chId}`),
    generate: (novelId: string, chapterNumber: number, focus: string = "") => {
      const params = focus ? `?focus=${encodeURIComponent(focus)}` : "";
      return fetch(`${API}/api/v1/novels/${novelId}/chapters/${chapterNumber}/generate${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
    },
    revise: (novelId: string, chId: string, data: Record<string, any>) =>
      request(`/api/v1/novels/${novelId}/chapters/${chId}/revise`, { method: "POST", body: JSON.stringify(data) }),
    versions: (novelId: string, chId: string) =>
      request(`/api/v1/novels/${novelId}/chapters/${chId}/versions`),
  },

  foreshadows: {
    list: (novelId: string) => request(`/api/v1/novels/${novelId}/foreshadows`),
    detect: (novelId: string, chId: string) =>
      request(`/api/v1/novels/${novelId}/chapters/${chId}/detect-foreshadows`, { method: "POST" }),
  },

  analysis: {
    get: (novelId: string, chId: string) => request(`/api/v1/novels/${novelId}/analysis/${chId}`),
  },

  export: {
    download: async (novelId: string, format: string = "md") => {
      const res = await fetch(`${API}/api/v1/novels/${novelId}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format }),
      });
      if (!res.ok) {
        const err = await res.text().catch(() => `HTTP ${res.status}`);
        throw new Error(err);
      }
      return res.text();
    },
  },
};
