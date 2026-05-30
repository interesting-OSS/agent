import { create } from "zustand";
import { api } from "@/lib/api";

export interface Chapter {
  id: string;
  chapter_number: number;
  title: string;
  content: string | null;
  word_count: number;
  status: string;
}

interface WriteStore {
  chapters: Chapter[];
  currentChapter: Chapter | null;
  sseStatus: "idle" | "preflight" | "writing" | "review" | "done";
  sseMessage: string;
  streamedText: string;
  qualityReport: {
    verdict: string;
    guardian_passed: boolean | null;
    inspector_verdict: string | null;
    violations: number;
  } | null;

  fetchChapters: (novelId: string) => Promise<void>;
  selectChapter: (ch: Chapter) => void;
  updateCurrentContent: (content: string) => void;
  generateChapter: (novelId: string, chapterNumber: number, focus?: string) => Promise<void>;
  resetGeneration: () => void;
}

export const useWriteStore = create<WriteStore>((set, get) => ({
  chapters: [],
  currentChapter: null,
  sseStatus: "idle",
  sseMessage: "",
  streamedText: "",
  qualityReport: null,

  fetchChapters: async (novelId) => {
    try {
      const chapters = await api.chapters.list(novelId);
      set({ chapters });
    } catch {}
  },

  selectChapter: (ch) => {
    set({ currentChapter: ch, qualityReport: null, streamedText: "", sseStatus: "idle" });
  },

  updateCurrentContent: (content: string) => {
    const ch = get().currentChapter;
    if (ch) {
      set({ currentChapter: { ...ch, content } });
    }
  },

  generateChapter: async (novelId, chapterNumber, focus = "") => {
    set({ sseStatus: "preflight", sseMessage: "PreFlight 检查中...", streamedText: "", qualityReport: null });

    try {
      const response = await api.chapters.generate(novelId, chapterNumber, focus);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Response body is empty");
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6);
          if (jsonStr === "[DONE]") continue;

          try {
            const event = JSON.parse(jsonStr);
            switch (event.phase) {
              case "preflight":
                set({ sseStatus: "preflight", sseMessage: event.message || "PreFlight..." });
                break;
              case "preflight_done":
                set({ sseMessage: "PreFlight 完成，开始生成正文..." });
                break;
              case "writing":
                set({ sseStatus: "writing" });
                if (event.token) {
                  set((s) => ({ streamedText: s.streamedText + event.token }));
                }
                break;
              case "writing_done":
                set({ sseMessage: `正文完成 (${event.word_count} 字)，质量检查中...` });
                break;
              case "review":
                set({ sseStatus: "review", sseMessage: event.message || "质量检查中..." });
                break;
              case "done":
                set({
                  sseStatus: "done",
                  qualityReport: {
                    verdict: event.verdict || "pass",
                    guardian_passed: event.guardian_passed,
                    inspector_verdict: event.inspector_verdict,
                    violations: 0,
                  },
                });
                // 刷新章节列表并更新 currentChapter
                await get().fetchChapters(novelId);
                const updated = get().chapters;
                const refreshed = updated.find((c: any) => c.chapter_number === chapterNumber);
                if (refreshed) {
                  set({ currentChapter: refreshed });
                }
                break;
            }
          } catch {}
        }
      }
    } catch (e: any) {
      set({ sseStatus: "idle", sseMessage: `生成失败: ${e.message}` });
    }
  },

  resetGeneration: () => {
    set({ sseStatus: "idle", sseMessage: "", streamedText: "", qualityReport: null });
  },
}));
