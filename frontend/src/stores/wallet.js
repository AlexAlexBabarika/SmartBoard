import { writable } from 'svelte/store';

function createWalletStore() {
  const { subscribe, set, update } = writable({
    connected: false,
    address: null,
    balance: 0
  });

  return {
    subscribe,
    connect: (address) => {
      set({
        connected: true,
        address: address,
        balance: 100 // Mock balance
      });
    },
    disconnect: () => {
      set({
        connected: false,
        address: null,
        balance: 0
      });
    }
  };
}

export const walletStore = createWalletStore();

