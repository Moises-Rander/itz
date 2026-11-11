import { create } from 'zustand'

// Estado global de UI (menu mobile).
export const useUiStore = create((set) => ({
  mobileMenuAberto: false,
  abrirMobileMenu: () => set({ mobileMenuAberto: true }),
  fecharMobileMenu: () => set({ mobileMenuAberto: false }),
  toggleMobileMenu: () =>
    set((s) => ({ mobileMenuAberto: !s.mobileMenuAberto })),
}))
