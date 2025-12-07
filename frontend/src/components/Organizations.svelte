<script>
  import { createEventDispatcher, onMount } from "svelte";
  import { walletStore } from "../stores/wallet.js";
  import { organizationAPI } from "../lib/api.js";

  const dispatch = createEventDispatcher();

  $: wallet = $walletStore;

  let organizations = [];
  let loading = true;
  let error = null;

  async function loadOrganizations() {
    if (!wallet.connected || !wallet.address) {
      organizations = [];
      loading = false;
      return;
    }

    loading = true;
    error = null;
    try {
      organizations = await organizationAPI.getOrganizations(wallet.address);
    } catch (err) {
      console.error("Failed to load organizations:", err);
      error = "Failed to load organizations. Please try again.";
      organizations = [];
    } finally {
      loading = false;
    }
  }

  // Load organizations when wallet is connected
  $: if (wallet.connected && wallet.address) {
    loadOrganizations();
  } else {
    organizations = [];
    loading = false;
  }

  function handleCreateNew() {
    dispatch("createNew");
  }

  function truncateAddress(address) {
    if (!address) return "";
    return `${address.slice(0, 8)}...${address.slice(-6)}`;
  }

  function truncateCID(cid) {
    if (!cid) return "";
    if (cid.length <= 20) return cid;
    return `${cid.slice(0, 10)}...${cid.slice(-8)}`;
  }
</script>

<div class="max-w-6xl mx-auto">
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="font-display font-semibold text-2xl text-pe-text">
        Organizations
      </h1>
      <p class="text-sm text-pe-muted mt-1">
        Organizations you belong to
      </p>
    </div>
    <button
      on:click={handleCreateNew}
      class="px-4 py-2 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors focus-ring flex items-center gap-2"
    >
      <svg
        class="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 4v16m8-8H4"
        />
      </svg>
      Create New
    </button>
  </div>

  {#if !wallet.connected}
    <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-8 text-center">
      <svg
        class="w-16 h-16 text-pe-muted mx-auto mb-4"
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
      <p class="text-pe-text font-medium mb-2">Connect your wallet</p>
      <p class="text-pe-muted text-sm">
        Please connect your wallet to view your organizations
      </p>
    </div>
  {:else if loading}
    <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-8 text-center">
      <div class="flex items-center justify-center gap-3">
        <svg
          class="animate-spin w-5 h-5 text-pe-accent"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <p class="text-pe-muted">Loading organizations...</p>
      </div>
    </div>
  {:else if error}
    <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-8">
      <div class="flex items-center gap-3 text-pe-accent mb-2">
        <svg
          class="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
        </svg>
        <p class="font-medium">{error}</p>
      </div>
      <button
        on:click={loadOrganizations}
        class="mt-4 px-4 py-2 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors focus-ring text-sm"
      >
        Retry
      </button>
    </div>
  {:else if organizations.length === 0}
    <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-12 text-center">
      <svg
        class="w-20 h-20 text-pe-muted mx-auto mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.645-5.963-1.76A8.967 8.967 0 016 18.72m3 0a5.971 5.971 0 014.93-5.57m0 0a5.995 5.995 0 015.682 4.282M9 18.72v-3.75m0 0v-3.75m0 3.75h3.75m-3.75 0H9"
        />
      </svg>
      <p class="text-pe-text font-medium mb-2">No organizations yet</p>
      <p class="text-pe-muted text-sm mb-6">
        You don't belong to any organizations. Create one to get started!
      </p>
      <button
        on:click={handleCreateNew}
        class="px-6 py-3 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors focus-ring inline-flex items-center gap-2"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
        Create Your First Organization
      </button>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each organizations as org (org.id)}
        <div
          class="bg-pe-panel border border-pe-border rounded-pe-lg p-6 hover:border-pe-accent/30 transition-all hover:shadow-lg group"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1 min-w-0">
              <h3 class="font-display font-semibold text-lg text-pe-text mb-1 truncate">
                {org.name}
              </h3>
              {#if org.sector}
                <span
                  class="inline-block px-2 py-1 text-xs font-medium rounded-pe bg-pe-accent/10 text-pe-accent"
                >
                  {org.sector}
                </span>
              {/if}
            </div>
            {#if org.creator_wallet === wallet.address}
              <span
                class="px-2 py-1 text-xs font-medium rounded-pe bg-pe-accent/20 text-pe-accent"
                title="You are the creator"
              >
                Creator
              </span>
            {/if}
          </div>

          <div class="space-y-3 mt-4">
            <div class="flex items-center gap-2 text-sm text-pe-muted">
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.645-5.963-1.76A8.967 8.967 0 016 18.72m3 0a5.971 5.971 0 014.93-5.57m0 0a5.995 5.995 0 015.682 4.282M9 18.72v-3.75m0 0v-3.75m0 3.75h3.75m-3.75 0H9"
                />
              </svg>
              <span>{org.member_count || org.team_members?.length || 0} {org.member_count === 1 ? "member" : "members"}</span>
            </div>

            {#if org.ipfs_cid}
              <div class="flex items-center gap-2 text-sm">
                <svg
                  class="w-4 h-4 text-pe-muted"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"
                  />
                </svg>
                <span class="text-pe-muted font-mono text-xs" title={org.ipfs_cid}>
                  IPFS: {truncateCID(org.ipfs_cid)}
                </span>
              </div>
            {/if}

            <div class="pt-3 border-t border-pe-border">
              <div class="text-xs text-pe-muted">
                <p class="mb-1">
                  <span class="font-medium">Creator:</span> {truncateAddress(org.creator_wallet)}
                </p>
                {#if org.created_at}
                  <p>
                    Created: {new Date(org.created_at).toLocaleDateString()}
                  </p>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

