import { create } from 'zustand';

interface ProjectDetails {
  id: string;
  name: string;
  domain: string;
  created_at: string;
  user_id: string;
}

interface ProjectState {
  selectedProject: ProjectDetails | null;
  setProject: (project: ProjectDetails) => void;
  clearProject: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  selectedProject: null,
  setProject: (project) => set({ selectedProject: project }),
  clearProject: () => set({ selectedProject: null }),
}));
