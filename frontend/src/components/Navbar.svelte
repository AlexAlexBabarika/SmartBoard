<script>
  import { createEventDispatcher } from "svelte";
  import { walletStore } from "../stores/wallet.js";

  export let currentView;

  const dispatch = createEventDispatcher();

  $: wallet = $walletStore;

  let mobileMenuOpen = false;
  let showAddressPrompt = false;
  let addressInput = "";

  function handleNavigation(view) {
    dispatch("navigate", { view });
    mobileMenuOpen = false;
  }

  function handleWalletClick() {
    if (wallet.connected) {
      dispatch("disconnectWallet");
    } else {
      // Show prompt for wallet address
      showAddressPrompt = true;
      addressInput = "";
    }
  }

  function handleAddressSubmit() {
    if (addressInput.trim()) {
      dispatch("connectWallet", { address: addressInput.trim() });
      showAddressPrompt = false;
      addressInput = "";
    }
  }

  function handleAddressCancel() {
    showAddressPrompt = false;
    addressInput = "";
  }

  function truncateAddress(address) {
    if (!address) return "";
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  }

  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }
</script>

<!-- Glass Navigation Bar -->
<nav class="fixed top-0 left-0 right-0 z-50 nav-glass">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <!-- Logo (Left) -->
      <div class="flex-shrink-0">
        <button
          on:click={() => handleNavigation("dashboard")}
          class="flex items-center gap-2 focus-ring rounded-pe"
          aria-label="Go to dashboard"
        >
          <!-- Plant/Leaf Icon in Accent Green -->
          <svg
            class="w-7 h-7 text-pe-accent"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path
              d="M12 2C8.5 2 4 4.5 4 9.5C4 14 8 18 12 22C16 18 20 14 20 9.5C20 4.5 15.5 2 12 2ZM12 18.5C9 15.5 6 12.5 6 9.5C6 5.91 9.13 4 12 4C14.87 4 18 5.91 18 9.5C18 12.5 15 15.5 12 18.5Z"
            />
            <path
              d="M12 6C10.5 6 8.5 7 8.5 9.5C8.5 11.5 10 13 12 14.5C14 13 15.5 11.5 15.5 9.5C15.5 7 13.5 6 12 6Z"
            />
          </svg>
          <span class="font-display font-semibold text-lg text-pe-text">SmartBoard
          </span>
        </button>
      </div>

      <!-- Center Navigation Links (Desktop) -->
      <div class="hidden md:flex items-center gap-1">
        <button
          class="nav-link"
          class:active={currentView === "dashboard"}
          on:click={() => handleNavigation("dashboard")}
        >
          Dashboard
        </button>
        <button
          class="nav-link"
          class:active={currentView === "create"}
          on:click={() => handleNavigation("create")}
        >
          Create Proposal
        </button>
        <button
          class="nav-link"
          class:active={currentView === "organizations"}
          on:click={() => handleNavigation("organizations")}
        >
          Organizations
        </button>
        <button
          class="nav-link"
          class:active={currentView === "createOrganization"}
          on:click={() => handleNavigation("createOrganization")}
        >
          Create Organization
        </button>
        <button
          class="nav-link"
          class:active={currentView === "qa"}
          on:click={() => handleNavigation("qa")}
        >
          Q&A
        </button>
      </div>

      <!-- Right Side: User Icons + Wallet -->
      <div class="flex items-center gap-3">
        <!-- User/Wallet Button -->
        <button
          class="flex items-center gap-2 px-3 py-2 rounded-pe transition-all duration-200 focus-ring
                 {wallet.connected
            ? 'bg-pe-accent/10 border border-pe-accent/30 hover:bg-pe-accent/20'
            : 'hover:bg-white/5'}"
          on:click={handleWalletClick}
          aria-label={wallet.connected ? "Disconnect wallet" : "Link wallet"}
        >
          {#if wallet.connected}
            <svg
              class="w-5 h-5 text-pe-accent"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
              />
            </svg>
            <span class="text-sm font-medium text-pe-accent hidden sm:inline">
              {truncateAddress(wallet.address)}
            </span>
          {:else}
            <span class="text-sm font-medium text-pe-muted">Link wallet</span>
          {/if}
        </button>

        <!-- Mobile Menu Button -->
        <button
          class="md:hidden p-2 rounded-pe hover:bg-white/5 transition-colors focus-ring"
          on:click={toggleMobileMenu}
          aria-label="Toggle menu"
          aria-expanded={mobileMenuOpen}
        >
          <svg
            class="w-5 h-5 text-pe-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            {#if mobileMenuOpen}
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            {:else}
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"
              />
            {/if}
          </svg>
        </button>
      </div>
    </div>
  </div>

  <!-- Mobile Menu Dropdown -->
  {#if mobileMenuOpen}
    <div class="md:hidden border-t border-pe-border animate-slide-up">
      <div class="px-4 py-4 space-y-2">
        <button
          class="mobile-nav-link"
          class:active={currentView === "dashboard"}
          on:click={() => handleNavigation("dashboard")}
        >
          Dashboard
        </button>
        <button
          class="mobile-nav-link"
          class:active={currentView === "create"}
          on:click={() => handleNavigation("create")}
        >
          Create Proposal
        </button>
        <button
          class="mobile-nav-link"
          class:active={currentView === "organizations"}
          on:click={() => handleNavigation("organizations")}
        >
          Organizations
        </button>
        <button
          class="mobile-nav-link"
          class:active={currentView === "createOrganization"}
          on:click={() => handleNavigation("createOrganization")}
        >
          Create Organization
        </button>
        <button
          class="mobile-nav-link"
          class:active={currentView === "qa"}
          on:click={() => handleNavigation("qa")}
        >
          Q&A
        </button>
      </div>
    </div>
  {/if}

  <!-- Address Prompt Modal -->
  {#if showAddressPrompt}
    <div
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      on:click|self={handleAddressCancel}
      on:keydown={(e) => e.key === "Escape" && handleAddressCancel()}
      tabindex="-1"
    >
      <div
        class="bg-pe-panel border border-pe-border rounded-pe-lg p-6 max-w-md w-full shadow-xl"
        role="document"
        on:click|stopPropagation
        on:keydown={(e) => e.stopPropagation()}
      >
        <h3
          id="modal-title"
          class="font-display font-semibold text-lg text-pe-text mb-4"
        >
          Enter your NEO wallet address
        </h3>
        <input
          type="text"
          class="search-input-pe w-full mb-4"
          placeholder="N..."
          bind:value={addressInput}
          on:keydown={(e) => {
            if (e.key === "Enter") handleAddressSubmit();
            if (e.key === "Escape") handleAddressCancel();
          }}
        />
        <div class="flex gap-3 justify-end">
          <button
            class="px-4 py-2 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors"
            on:click={handleAddressCancel}
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            on:click={handleAddressSubmit}
            disabled={!addressInput.trim()}
          >
            Connect
          </button>
        </div>
      </div>
    </div>
  {/if}
</nav>

<style>
  .nav-link {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--pe-muted);
    border-radius: 8px;
    transition: all 0.18s ease;
  }

  .nav-link:hover {
    color: var(--pe-text);
    background: rgba(255, 255, 255, 0.05);
  }

  .nav-link.active {
    color: var(--pe-text);
    background: rgba(255, 255, 255, 0.08);
  }

  .mobile-nav-link {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--pe-muted);
    border-radius: 8px;
    transition: all 0.18s ease;
  }

  .mobile-nav-link:hover {
    color: var(--pe-text);
    background: rgba(255, 255, 255, 0.05);
  }

  .mobile-nav-link.active {
    color: var(--pe-accent);
    background: rgba(25, 195, 122, 0.1);
  }
</style>
