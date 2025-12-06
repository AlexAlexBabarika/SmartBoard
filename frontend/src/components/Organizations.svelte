<script>
  import { createEventDispatcher, onMount } from "svelte";
  import { organizationAPI } from "../lib/api.js";

  const dispatch = createEventDispatcher();

  let organizations = [];
  let loading = true;
  let error = "";

  async function loadOrganizations() {
    error = "";
    loading = true;
    try {
      const data = await organizationAPI.list();
      organizations = Array.isArray(data) ? data : [];
    } catch (e) {
      error = e.message || "Failed to load organizations.";
      console.error("Organization load error:", e);
    } finally {
      loading = false;
    }
  }

  function handleCreateNew() {
    dispatch("createNew");
  }

  onMount(() => {
    loadOrganizations();
  });
</script>

<div class="space-y-6 animate-fade-in">
  <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <div>
      <h1 class="font-display text-4xl font-bold text-pe-text">Organizations</h1>
      <p class="text-pe-muted mt-2">Browse existing organizations and their membership size.</p>
    </div>

    <div class="flex items-center gap-3">
      <button class="btn-accent-pe flex items-center gap-2" on:click={handleCreateNew}>
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Create Organization
      </button>
      <button
        class="px-4 py-2 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors"
        on:click={loadOrganizations}
        aria-label="Refresh organizations"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v6h6M20 20v-6h-6" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 19a9 9 0 0114-7.48M19 5a9 9 0 01-14 7.48" />
        </svg>
      </button>
    </div>
  </div>

  {#if error}
    <div class="flex items-start gap-4 p-4 rounded-pe-lg bg-red-500/10 border border-red-500/20">
      <svg class="w-6 h-6 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div>
        <p class="text-red-400 font-medium">Failed to load organizations</p>
        <p class="text-sm text-pe-text-dim mt-1">{error}</p>
      </div>
    </div>
  {/if}

  {#if loading}
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each Array(6) as _}
        <div class="border border-pe-border rounded-pe-lg p-4 bg-pe-card animate-pulse" aria-hidden="true">
          <div class="w-16 h-16 rounded-full bg-pe-bg-secondary mb-4"></div>
          <div class="h-4 bg-pe-bg-secondary rounded w-3/4 mb-2"></div>
          <div class="h-3 bg-pe-bg-secondary rounded w-1/2"></div>
        </div>
      {/each}
    </div>
  {:else if organizations.length === 0}
    <div class="border border-dashed border-pe-border rounded-pe-lg p-8 text-center bg-pe-card">
      <div class="flex justify-center mb-3">
        <div class="w-12 h-12 rounded-full bg-pe-bg-secondary flex items-center justify-center text-pe-muted">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </div>
      </div>
      <p class="text-pe-text font-semibold">No organizations yet</p>
      <p class="text-pe-text-dim text-sm mt-1">Create the first organization to get started.</p>
      <button class="btn-accent-pe mt-4" on:click={handleCreateNew}>Create organization</button>
    </div>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each organizations as org}
        <article class="border border-pe-border rounded-pe-lg p-5 bg-pe-card space-y-3 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="w-14 h-14 rounded-full bg-pe-bg-secondary border border-pe-border overflow-hidden flex items-center justify-center">
              {#if org.logo}
                <img src={org.logo} alt={`${org.name} logo`} class="w-full h-full object-cover" />
              {:else}
                <span class="text-pe-text font-semibold text-lg">
                  {org.name ? org.name[0]?.toUpperCase() : "?"}
                </span>
              {/if}
            </div>
            <div class="flex-1">
              <p class="font-semibold text-pe-text">{org.name}</p>
              <p class="text-pe-text-dim text-sm flex items-center gap-2">
                <span class="px-2 py-1 rounded-pe text-xs bg-pe-accent/10 text-pe-accent capitalize">
                  {org.type || "Unknown"}
                </span>
                <span class="flex items-center gap-1 text-pe-muted">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5V4H2v16h5m10 0V10m0 10H7m10-10H7m0 10V10" />
                  </svg>
                  {org.membersCount ?? org.total_members ?? org.members ?? 0} members
                </span>
              </p>
            </div>
          </div>

          {#if org.description}
            <p class="text-sm text-pe-text-dim line-clamp-3">{org.description}</p>
          {/if}

          <div class="flex items-center justify-between text-xs text-pe-text-dim">
            <span>
              Created {org.createdAt ? new Date(org.createdAt).toLocaleDateString() : "recently"}
            </span>
            {#if org.status}
              <span class="px-2 py-1 rounded-pe bg-pe-bg-secondary border border-pe-border capitalize">
                {org.status}
              </span>
            {/if}
          </div>
        </article>
      {/each}
    </div>
  {/if}
</div>
