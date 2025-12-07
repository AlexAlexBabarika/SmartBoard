<script>
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  function handleCreateNew() {
    dispatch("createNew");
  }
</script>

<div class="max-w-6xl mx-auto">
  <div class="flex items-center justify-between mb-6">
    <h1 class="font-display font-semibold text-2xl text-pe-text">
      Organizations
    </h1>
    <button
      on:click={handleCreateNew}
      class="px-4 py-2 rounded-pe bg-pe-accent text-white hover:bg-pe-accent-hover transition-colors focus-ring"
    >
      Create New
    </button>
  </div>

  <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-8">
    <p class="text-pe-muted">
      Organizations feature coming soon.
    </p>
  </div>
</div>

