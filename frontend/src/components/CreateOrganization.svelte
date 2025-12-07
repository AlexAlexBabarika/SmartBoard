<script>
  import { createEventDispatcher } from "svelte";
  import { walletStore } from "../stores/wallet.js";
  import { organizationAPI } from "../lib/api.js";

  const dispatch = createEventDispatcher();

  $: wallet = $walletStore;

  let organizationName = "";
  let sector = "";
  let teamMembers = [];
  let newMemberWallet = "";
  let submitting = false;
  let nameInputElement;
  let walletInputElement;

  function handleBack() {
    dispatch("back");
  }

  function handleNavigate(view) {
    dispatch("navigate", { view });
  }

  function addTeamMember() {
    const wallet = newMemberWallet.trim();
    if (!wallet) return;
    
    // Basic validation for NEO wallet address (starts with N)
    if (!wallet.startsWith("N")) {
      alert("Invalid NEO wallet address. Must start with 'N'");
      return;
    }
    
    // Check for duplicates
    if (teamMembers.includes(wallet)) {
      alert("This wallet address is already added");
      return;
    }
    
    teamMembers = [...teamMembers, wallet];
    newMemberWallet = "";
    
    // Focus back on input
    setTimeout(() => {
      if (walletInputElement) {
        walletInputElement.focus();
      }
    }, 100);
  }

  function removeTeamMember(wallet) {
    teamMembers = teamMembers.filter((w) => w !== wallet);
  }

  function truncateAddress(address) {
    if (!address) return "";
    return `${address.slice(0, 8)}...${address.slice(-6)}`;
  }

  async function handleSubmit() {
    if (!organizationName.trim()) {
      alert("Please enter an organization name");
      return;
    }

    if (teamMembers.length === 0) {
      alert("Please add at least one team member");
      return;
    }

    if (!wallet.connected || !wallet.address) {
      alert("Please connect your wallet to create an organization");
      return;
    }

    submitting = true;
    try {
      const result = await organizationAPI.createOrganization(
        organizationName.trim(),
        sector.trim() || null,
        teamMembers,
        wallet.address
      );
      
      console.log("Organization created:", result);
      alert(`Organization "${result.name}" created successfully! IPFS CID: ${result.ipfs_cid}`);
      handleNavigate("organizations");
    } catch (error) {
      console.error("Error creating organization:", error);
      alert(`Failed to create organization: ${error.message || "Please try again."}`);
    } finally {
      submitting = false;
    }
  }

  function handleKeydown(event, action) {
    if (event.key === "Enter") {
      event.preventDefault();
      if (action === "add") {
        addTeamMember();
      } else if (action === "submit") {
        handleSubmit();
      }
    }
  }
</script>

<div class="max-w-4xl mx-auto">
  <div class="mb-6">
    <button
      on:click={handleBack}
      class="text-pe-muted hover:text-pe-text transition-colors flex items-center gap-2"
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
          d="M15 19l-7-7 7-7"
        />
      </svg>
      Back to Dashboard
    </button>
  </div>

  <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-8 shadow-lg">
    <h1 class="font-display font-semibold text-2xl text-pe-text mb-2">
      Create Organization
    </h1>
    <p class="text-pe-muted mb-8">
      Set up a new organization and add team members by their wallet addresses. 
      Organization data will be saved to Storacha/IPFS.
    </p>

    {#if !wallet.connected}
      <div class="bg-pe-card border border-pe-border rounded-pe-lg p-4 mb-6">
        <div class="flex items-center gap-3">
          <svg
            class="w-5 h-5 text-pe-accent"
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
          <p class="text-sm text-pe-text">
            Please connect your wallet to create an organization.
          </p>
        </div>
      </div>
    {/if}

    <form on:submit|preventDefault={handleSubmit} class="space-y-6">
      <!-- Organization Name -->
      <div>
        <label
          for="org-name"
          class="block text-sm font-medium text-pe-text mb-2"
        >
          Organization Name <span class="text-pe-accent">*</span>
        </label>
        <input
          id="org-name"
          type="text"
          bind:this={nameInputElement}
          bind:value={organizationName}
          class="search-input-pe w-full"
          placeholder="Enter organization name"
          required
          autofocus
        />
      </div>

      <!-- Sector -->
      <div>
        <label
          for="org-sector"
          class="block text-sm font-medium text-pe-text mb-2"
        >
          Sector <span class="text-pe-muted text-xs">(optional)</span>
        </label>
        <input
          id="org-sector"
          type="text"
          bind:value={sector}
          class="search-input-pe w-full"
          placeholder="e.g., Technology, Energy, Healthcare"
        />
      </div>

      <!-- Team Members Section -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <label class="block text-sm font-medium text-pe-text">
            Team Members <span class="text-pe-accent">*</span>
          </label>
          <span class="text-sm text-pe-muted">
            {teamMembers.length} {teamMembers.length === 1 ? "member" : "members"}
          </span>
        </div>

        <!-- Add Team Member Input -->
        <div class="flex gap-2 mb-4">
          <input
            type="text"
            bind:this={walletInputElement}
            bind:value={newMemberWallet}
            class="search-input-pe flex-1"
            placeholder="N... (Enter NEO wallet address)"
            on:keydown={(e) => handleKeydown(e, "add")}
          />
          <button
            type="button"
            on:click={addTeamMember}
            disabled={!newMemberWallet.trim()}
            class="px-4 py-2 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-ring flex items-center gap-2"
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
            Add
          </button>
        </div>

        <!-- Team Members List -->
        {#if teamMembers.length > 0}
          <div class="space-y-2">
            {#each teamMembers as wallet (wallet)}
              <div
                class="flex items-center justify-between bg-pe-card border border-pe-border rounded-pe p-3 group hover:border-pe-accent/30 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-pe-accent/10 flex items-center justify-center">
                    <svg
                      class="w-5 h-5 text-pe-accent"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-mono text-pe-text">
                      {truncateAddress(wallet)}
                    </p>
                    <p class="text-xs text-pe-muted font-mono">{wallet}</p>
                  </div>
                </div>
                <button
                  type="button"
                  on:click={() => removeTeamMember(wallet)}
                  class="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-pe hover:bg-pe-card text-pe-muted hover:text-pe-accent focus-ring"
                  aria-label="Remove team member"
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            {/each}
          </div>
        {:else}
          <div
            class="border-2 border-dashed border-pe-border rounded-pe p-8 text-center"
          >
            <svg
              class="w-12 h-12 text-pe-muted mx-auto mb-3"
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
            <p class="text-pe-muted text-sm">
              No team members added yet. Add wallet addresses above.
            </p>
          </div>
        {/if}
      </div>

      <!-- Submit Button -->
      <div class="flex gap-3 pt-4 border-t border-pe-border">
        <button
          type="button"
          on:click={handleBack}
          class="px-6 py-3 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors focus-ring"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting || !organizationName.trim() || teamMembers.length === 0 || !wallet.connected}
          class="px-6 py-3 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-ring flex items-center gap-2 ml-auto"
        >
          {#if submitting}
            <svg
              class="animate-spin w-5 h-5"
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
            Creating...
          {:else}
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
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
            Create Organization
          {/if}
        </button>
      </div>
    </form>
  </div>
</div>

