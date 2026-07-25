import { create } from "zustand";

interface SystemStatusState {
  lastCheckedAt: Date | null;
  markChecked: () => void;
}

/**
 * Tracks the last time a health/readiness poll resolved successfully,
 * so any component (header, status cards, future notification toasts)
 * can display "last checked Xs ago" without re-deriving it from the
 * query cache directly.
 */
export const useSystemStatusStore = create<SystemStatusState>((set) => ({
  lastCheckedAt: null,
  markChecked: () => set({ lastCheckedAt: new Date() }),
}));
