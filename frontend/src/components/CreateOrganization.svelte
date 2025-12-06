<script>
  import { createEventDispatcher } from "svelte";
  import { organizationAPI } from "../lib/api.js";

  const dispatch = createEventDispatcher();

  let name = "";
  let type = "Public";
  let membersCount = "";
  let logoPreview = "";
  let logoData = "";
  let submitting = false;
  let error = "";
  let success = "";

  function goBack() {
    dispatch("back");
  }

  function clearLogo() {
    logoPreview = "";
    logoData = "";
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      clearLogo();
      return;
    }

    logoPreview = URL.createObjectURL(file);

    const reader = new FileReader();
    reader.onload = (e) => {
      logoData = e.target?.result || "";
    };
    reader.readAsDataURL(file);
  }

  async function handleSubmit() {
    error = "";
    success = "";

    const trimmedName = name.trim();
    const count = Number(membersCount);

    if (!trimmedName) {
      error = "Organization name is required.";
      return;
    }

    if (!Number.isFinite(count) || count <= 0) {
      error = "Members count must be a positive number.";
      return;
    }

    if (!type) {
      error = "Type is required.";
      return;
    }

    const payload = {
      name: trimmedName,
      logo: logoData,
      type,
      membersCount: count,
    };

    try {
      submitting = true;
      await organizationAPI.create(payload);
      success = "Organization created successfully.";
      dispatch("navigate", { view: "organizations" });
    } catch (e) {
      error = e.message || "Failed to create organization.";
      console.error("Organization creation failed:", e);
    } finally {
      submitting = false;
    }
  }
</script>

<div class="space-y-6 animate-fade-in">
  <div class="flex justify-between items-center">
    <div>
      <h1 class="font-display text-4xl font-bold text-pe-text">Create Organization</h1>
      <p class="text-pe-muted mt-2">Register a new organization with logo and membership size.</p>
    </div>

    <button
      class="flex items-center gap-2 px-4 py-2 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors focus-ring"
      on:click={goBack}
    >
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      Back
    </button>
  </div>

  {#if error}
    <div class="flex items-start gap-4 p-4 rounded-pe-lg bg-red-500/10 border border-red-500/20">
      <svg class="w-6 h-6 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span class="text-red-400">{error}</span>
    </div>
  {/if}

  {#if success}
    <div class="flex items-start gap-4 p-4 rounded-pe-lg bg-pe-accent/10 border border-pe-accent/20">
      <svg class="w-6 h-6 text-pe-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
      <span class="text-pe-text">{success}</span>
    </div>
  {/if}

  <div class="card-pe p-6">
    <form class="space-y-6" on:submit|preventDefault={handleSubmit}>
      <div class="grid grid-cols-1 gap-6">
        <div class="space-y-6">
          <div>
            <label class="flex items-center justify-between mb-2" for="name">
              <span class="text-sm font-medium text-pe-text">Organization Name</span>
              <span class="text-xs text-red-400">*</span>
            </label>
            <input
              id="name"
              class="search-input-pe"
              placeholder="Acme Ventures"
              bind:value={name}
              required
              type="text"
            />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="flex items-center justify-between mb-2" for="type">
                <span class="text-sm font-medium text-pe-text">Type</span>
                <span class="text-xs text-red-400">*</span>
              </label>
              <select id="type" class="search-input-pe" bind:value={type} required>
                <option value="Public">Public</option>
                <option value="Private">Private</option>
              </select>
            </div>

            <div>
              <label class="flex items-center justify-between mb-2" for="membersCount">
                <span class="text-sm font-medium text-pe-text">Members Count</span>
                <span class="text-xs text-red-400">*</span>
              </label>
              <input
                id="membersCount"
                class="search-input-pe"
                type="number"
                min="1"
                placeholder="50"
                bind:value={membersCount}
                required
              />
              <p class="text-xs text-pe-text-dim mt-1">Total active members.</p>
            </div>
          </div>

          <div>
            <label class="flex items-center justify-between mb-2" for="logo">
              <span class="text-sm font-medium text-pe-text">Logo Upload</span>
              <span class="text-xs text-pe-muted">PNG/JPG, max a few MB</span>
            </label>
            <div class="flex items-center gap-3">
              <input
                id="logo"
                type="file"
                accept="image/*"
                class="file-input file-input-bordered w-full max-w-xs"
                on:change={handleFileChange}
              />
              {#if logoPreview}
                <button type="button" class="text-pe-muted hover:text-pe-text" on:click={clearLogo}>
                  Clear
                </button>
              {/if}
            </div>
            <p class="text-xs text-pe-text-dim mt-1">Preview updates instantly after selecting a file.</p>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-4 pt-4 border-t border-pe-border">
        <button
          type="button"
          class="px-5 py-2.5 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card-hover transition-colors"
          on:click={goBack}
        >
          Cancel
        </button>

        <button type="submit" class="btn-accent-pe flex items-center gap-2" disabled={submitting}>
          {#if submitting}
            <div class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            Saving...
          {:else}
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Create Organization
          {/if}
        </button>
      </div>
    </form>
  </div>
</div>
