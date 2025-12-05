<script>
  import { createEventDispatcher } from 'svelte';
  import { walletStore } from '../stores/wallet.js';
  
  export let currentView;
  
  const dispatch = createEventDispatcher();
  
  $: wallet = $walletStore;
  
  function handleNavigation(view) {
    dispatch('navigate', { view });
  }
  
  function handleWalletClick() {
    if (wallet.connected) {
      dispatch('disconnectWallet');
    } else {
      dispatch('connectWallet');
    }
  }
  
  function truncateAddress(address) {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  }
</script>

<div class="navbar bg-base-100 shadow-lg">
  <div class="navbar-start">
    <div class="dropdown">
      <label tabindex="0" class="btn btn-ghost lg:hidden" aria-label="Menu">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16" />
        </svg>
      </label>
      <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
        <li><button on:click={() => handleNavigation('dashboard')}>Dashboard</button></li>
        <li><button on:click={() => handleNavigation('create')}>Create Proposal</button></li>
      </ul>
    </div>
    <button on:click={() => handleNavigation('dashboard')} class="btn btn-ghost normal-case text-xl">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      AI Investment Scout DAO
    </button>
  </div>
  
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li>
        <button 
          class:active={currentView === 'dashboard'}
          on:click={() => handleNavigation('dashboard')}
        >
          Dashboard
        </button>
      </li>
      <li>
        <button 
          class:active={currentView === 'create'}
          on:click={() => handleNavigation('create')}
        >
          Create Proposal
        </button>
      </li>
    </ul>
  </div>
  
  <div class="navbar-end">
    <button 
      class="btn btn-primary"
      on:click={handleWalletClick}
    >
      {#if wallet.connected}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
        {truncateAddress(wallet.address)}
      {:else}
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        Connect Wallet
      {/if}
    </button>
  </div>
</div>

<style>
  .active {
    background-color: hsl(var(--p) / var(--tw-bg-opacity));
    color: hsl(var(--pc));
  }
</style>

