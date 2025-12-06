<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  function goBack() {
    dispatch('back');
  }
</script>

<div class="space-y-6 animate-fade-in">
  <!-- Header -->
  <div class="flex justify-between items-center">
    <div>
      <h1 class="font-display text-4xl font-bold text-pe-text">Q&A</h1>
      <p class="text-pe-muted mt-2">Frequently asked questions and how it works</p>
    </div>
    
    <button class="flex items-center gap-2 px-4 py-2 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors focus-ring" on:click={goBack}>
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      Back
    </button>
  </div>
  
  <!-- How it works -->
  <div class="card-pe p-6">
    <h2 class="font-display font-semibold text-lg text-pe-text mb-4">How It Works</h2>
    <div class="space-y-4">
      {#each [
        { num: 1, title: 'SpoonOS Agent', desc: 'The AI agent analyzes startup data and generates a comprehensive investment memo' },
        { num: 2, title: 'PDF Generation', desc: 'The memo is rendered as a professional PDF with SWOT analysis, risk assessment, and recommendations' },
        { num: 3, title: 'IPFS Upload', desc: 'The PDF is uploaded to IPFS for permanent, decentralized storage' },
        { num: 4, title: 'Blockchain Submission', desc: 'The proposal is submitted to the NEO smart contract and stored in the backend database' },
        { num: 5, title: 'DAO Voting', desc: 'DAO members review the memo and vote on whether to invest' }
      ] as step}
        <div class="flex items-start gap-4">
          <div class="w-7 h-7 rounded-full bg-pe-accent/20 flex items-center justify-center flex-shrink-0">
            <span class="text-sm font-semibold text-pe-accent">{step.num}</span>
          </div>
          <div>
            <h3 class="font-medium text-pe-text">{step.title}</h3>
            <p class="text-sm text-pe-muted mt-0.5">{step.desc}</p>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fade-in {
    animation: fade-in 0.3s ease-out;
  }
</style>

