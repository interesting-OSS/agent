import { create } from "zustand";
import { api } from "@/lib/api";

export interface Novel {
  id: string;
  title: string;
  genre_id: string | null;
  status: string;
  writing_style: string;
  word_count: number;
  target_word_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface Genre {
  id: string;
  name: string;
  category: string;
}

interface NovelStore {
  novels: Novel[];
  genres: Genre[];
  loading: boolean;
  fetchNovels: () => Promise<void>;
  fetchGenres: () => Promise<void>;
  createNovel: (data: { title: string; genre_id: string; writing_style?: string; target_word_count?: number }) => Promise<Novel>;
  deleteNovel: (id: string) => Promise<void>;
}

export const useNovelStore = create<NovelStore>((set) => ({
  novels: [],
  genres: [],
  loading: false,

  fetchNovels: async () => {
    set({ loading: true });
    try {
      const novels = await api.novels.list();
      set({ novels, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchGenres: async () => {
    try {
      const genres = await api.genre.list();
      set({ genres });
    } catch {
      console.error("加载小说类型失败，请确认后端服务已启动");
    }
  },

  createNovel: async (data) => {
    const novel = await api.novels.create(data);
    set((s) => ({ novels: [novel, ...s.novels] }));
    return novel;
  },

  deleteNovel: async (id) => {
    await api.novels.delete(id);
    set((s) => ({ novels: s.novels.filter((n) => n.id !== id) }));
  },
}));
