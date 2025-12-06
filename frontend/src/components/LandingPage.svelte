<script>
  import { createEventDispatcher, onMount } from "svelte";
  import RotatingEarth from "./RotatingEarth.svelte";

  const dispatch = createEventDispatcher();

  let windowWidth = 1920;
  let windowHeight = 1080;

  onMount(() => {
    windowWidth = window.innerWidth;
    windowHeight = window.innerHeight;
    
    const handleResize = () => {
      windowWidth = window.innerWidth;
      windowHeight = window.innerHeight;
    };
    
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  });

  function handleGetStarted() {
    dispatch("navigate", { view: "dashboard" });
  }
</script>

<div class="min-h-screen bg-pe-bg relative overflow-hidden">
  <!-- Full Screen Globe Background -->
  <div class="fixed inset-0 w-screen h-screen z-0 pointer-events-none overflow-hidden">
    <RotatingEarth 
      width={windowWidth} 
      height={windowHeight} 
      className="w-full h-full opacity-50" 
    />
  </div>

  <!-- Hero Section -->
  <section class="relative z-10 pt-24 pb-20 px-4 sm:px-6 lg:px-8">
    <!-- Background gradient overlay for better text readability -->
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
            class="flex items-center gap-3 p-4 rounded-pe-lg bg-pe-card/80 backdrop-blur-sm border border-pe-border"
          >
            <img
              src="/logo.svg"
              alt="SmartBoard Logo"
              class="w-14 h-14"
            />
            <span class="font-display font-semibold text-2xl text-pe-text"
              >SmartBoard</span
            >
          </div>
        </div>

        <!-- Main Headline -->
        <h1
          class="font-display font-bold text-5xl sm:text-6xl lg:text-7xl text-pe-text mb-6 leading-tight drop-shadow-lg"
        >
          AI-Powered Investment
          <span class="text-pe-accent">Scout DAO</span>
        </h1>

        <!-- Subheadline -->
        <p
          class="text-xl sm:text-2xl text-pe-muted max-w-3xl mx-auto mb-10 leading-relaxed drop-shadow-md"
        >
          Decentralized investment evaluation powered by artificial intelligence.
          Discover, analyze, and vote on the best investment opportunities.
        </p>

        <!-- CTA Buttons -->
        <div
          class="flex justify-center items-center mb-8"
        >
          <button
            class="btn-accent-pe text-lg px-8 py-4 min-w-[200px] shadow-xl"
            on:click={handleGetStarted}
          >
            Get Started
          </button>
        </div>
      </div>
    </div>
  </section>

  <!-- Features Section -->
  <section class="relative z-10 py-20 px-4 sm:px-6 lg:px-8 bg-pe-panel/30 backdrop-blur-sm">
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
        <div class="card-pe p-6 stagger-1 bg-pe-card/60">
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

        <div class="card-pe p-6 stagger-2 bg-pe-card/60">
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

        <div class="card-pe p-6 stagger-3 bg-pe-card/60">
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

        <div class="card-pe p-6 stagger-4 bg-pe-card/60">
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
