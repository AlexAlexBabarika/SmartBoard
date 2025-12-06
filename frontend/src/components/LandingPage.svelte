<script>
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  function handleGetStarted() {
    dispatch("navigate", { view: "dashboard" });
  }
</script>

<div class="min-h-screen bg-pe-bg">
  <!-- Hero Section -->
  <section class="relative overflow-hidden pt-24 pb-20 px-4 sm:px-6 lg:px-8">
    <!-- Background gradient effects -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        class="absolute -top-40 -right-40 w-80 h-80 bg-pe-accent/10 rounded-full blur-3xl"
      ></div>
      <div
        class="absolute -bottom-40 -left-40 w-80 h-80 bg-pe-accent/10 rounded-full blur-3xl"
      ></div>
    </div>

    <div class="relative max-w-7xl mx-auto">
      <div class="text-center animate-fade-in">
        <!-- Logo/Brand -->
        <div class="flex justify-center mb-8">
          <div
            class="flex items-center gap-3 p-4 rounded-pe-lg bg-pe-card border border-pe-border"
          >
            <svg
              class="w-10 h-10 text-pe-accent"
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
            <span class="font-display font-semibold text-2xl text-pe-text"
              >SmartBoard</span
            >
          </div>
        </div>

        <!-- Main Headline -->
        <h1
          class="font-display font-bold text-5xl sm:text-6xl lg:text-7xl text-pe-text mb-6 leading-tight"
        >
          AI-Powered Investment
          <span class="text-pe-accent">Scout DAO</span>
        </h1>

        <!-- Subheadline -->
        <p
          class="text-xl sm:text-2xl text-pe-muted max-w-3xl mx-auto mb-10 leading-relaxed"
        >
          Decentralized investment evaluation powered by artificial intelligence.
          Discover, analyze, and vote on the best investment opportunities.
        </p>

        <!-- CTA Buttons -->
        <div
          class="flex justify-center items-center mb-16"
        >
          <button
            class="btn-accent-pe text-lg px-8 py-4 min-w-[200px]"
            on:click={handleGetStarted}
          >
            Get Started
          </button>
        </div>
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section class="py-20 px-4 sm:px-6 lg:px-8 bg-pe-panel/50">
    <div class="max-w-7xl mx-auto">
      <div class="text-center mb-16">
        <h2
          class="font-display font-bold text-4xl sm:text-5xl text-pe-text mb-4"
        >
          How It Works
        </h2>
        <p class="text-lg text-pe-muted max-w-2xl mx-auto">
          A streamlined process for evaluating and voting on investment
          opportunities
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="card-pe p-6 stagger-1">
          <div class="flex items-center gap-4 mb-4">
            <div
              class="w-10 h-10 rounded-pe bg-pe-accent/10 flex items-center justify-center flex-shrink-0"
            >
              <span class="text-pe-accent font-bold text-lg">1</span>
            </div>
            <h3 class="font-display font-semibold text-xl text-pe-text">
              Create Proposal
            </h3>
          </div>
          <p class="text-pe-muted text-sm leading-relaxed">
            Submit investment opportunities with detailed information for
            community review
          </p>
        </div>

        <div class="card-pe p-6 stagger-2">
          <div class="flex items-center gap-4 mb-4">
            <div
              class="w-10 h-10 rounded-pe bg-pe-accent/10 flex items-center justify-center flex-shrink-0"
            >
              <span class="text-pe-accent font-bold text-lg">2</span>
            </div>
            <h3 class="font-display font-semibold text-xl text-pe-text">
              AI Analysis
            </h3>
          </div>
          <p class="text-pe-muted text-sm leading-relaxed">
            Our AI system analyzes the proposal, providing risk assessment and
            market insights
          </p>
        </div>

        <div class="card-pe p-6 stagger-3">
          <div class="flex items-center gap-4 mb-4">
            <div
              class="w-10 h-10 rounded-pe bg-pe-accent/10 flex items-center justify-center flex-shrink-0"
            >
              <span class="text-pe-accent font-bold text-lg">3</span>
            </div>
            <h3 class="font-display font-semibold text-xl text-pe-text">
              Community Review
            </h3>
          </div>
          <p class="text-pe-muted text-sm leading-relaxed">
            DAO members review proposals, ask questions, and discuss
            opportunities
          </p>
        </div>

        <div class="card-pe p-6 stagger-4">
          <div class="flex items-center gap-4 mb-4">
            <div
              class="w-10 h-10 rounded-pe bg-pe-accent/10 flex items-center justify-center flex-shrink-0"
            >
              <span class="text-pe-accent font-bold text-lg">4</span>
            </div>
            <h3 class="font-display font-semibold text-xl text-pe-text">
              Vote & Execute
            </h3>
          </div>
          <p class="text-pe-muted text-sm leading-relaxed">
            Cast your vote on proposals. Approved investments are executed
            transparently
          </p>
        </div>
      </div>
    </div>
  </section>
</div>
