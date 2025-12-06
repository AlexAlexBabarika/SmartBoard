import { writable } from 'svelte/store';

// Storage key for persisting wallet state
const STORAGE_KEY = 'wallet_connection';

// Helper functions for localStorage
function loadFromStorage() {
  if (typeof window === 'undefined') {
    return { connected: false, address: null, balance: 0 };
  }
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Validate stored data structure
      if (parsed && typeof parsed === 'object' && 'connected' in parsed) {
        return parsed;
      }
    }
  } catch (e) {
    console.warn('Failed to load wallet state from localStorage:', e);
  }
  
  return { connected: false, address: null, balance: 0 };
}

function saveToStorage(state) {
  if (typeof window === 'undefined') {
    return;
  }
  
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.warn('Failed to save wallet state to localStorage:', e);
  }
}

function clearStorage() {
  if (typeof window === 'undefined') {
    return;
  }
  
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.warn('Failed to clear wallet state from localStorage:', e);
  }
}

function createWalletStore() {
  // Initialize from localStorage
  const initialState = loadFromStorage();
  
  const { subscribe, set, update } = writable(initialState);

  return {
    subscribe,
    connect: (address) => {
      const newState = {
        connected: true,
        address: address,
        balance: 100 // Mock balance
      };
      set(newState);
      saveToStorage(newState);
    },
    disconnect: () => {
      const newState = {
        connected: false,
        address: null,
        balance: 0
      };
      set(newState);
      clearStorage();
    }
  };
}

export const walletStore = createWalletStore();

