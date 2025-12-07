<script>
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  function handleBack() {
    dispatch("back");
  }

  function handleNavigate(view) {
    dispatch("navigate", { view });
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

  <div class="bg-pe-panel border border-pe-border rounded-pe-lg p-8">
    <h1 class="font-display font-semibold text-2xl text-pe-text mb-6">
      Create Organization
    </h1>

    <p class="text-pe-muted mb-6">
      Organization creation feature coming soon.
    </p>
  </div>
</div>

