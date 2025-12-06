<script>
  import Dashboard from "./components/Dashboard.svelte";
  import ProposalDetail from "./components/ProposalDetail.svelte";
  import CreateProposal from "./components/CreateProposal.svelte";
  import QA from "./components/QA.svelte";
  import Navbar from "./components/Navbar.svelte";
  import { walletStore } from "./stores/wallet.js";

  let currentView = "dashboard"; // 'dashboard', 'detail', 'create', 'qa'
  let selectedProposalId = null;

  function navigateTo(view, proposalId = null) {
    currentView = view;
    selectedProposalId = proposalId;
  }

  // Wallet connection
  function connectWallet(event) {
    const address = event.detail?.address || null;
    if (address) {
      walletStore.connect(address);
    }
  }

  function disconnectWallet() {
    walletStore.disconnect();
  }
</script>

<div class="min-h-screen bg-pe-bg">
  <Navbar
    {currentView}
    on:navigate={(e) => navigateTo(e.detail.view)}
    on:connectWallet={connectWallet}
    on:disconnectWallet={disconnectWallet}
  />

  <main>
    {#if currentView === "dashboard"}
      <Dashboard on:selectProposal={(e) => navigateTo("detail", e.detail.id)} />
    {:else if currentView === "detail"}
      <div class="container mx-auto px-4 py-8 pt-24">
        <ProposalDetail
          proposalId={selectedProposalId}
          on:back={() => navigateTo("dashboard")}
        />
      </div>
    {:else if currentView === "create"}
      <div class="container mx-auto px-4 py-8 pt-24">
        <CreateProposal on:back={() => navigateTo("dashboard")} />
      </div>
    {:else if currentView === "qa"}
      <div class="container mx-auto px-4 py-8 pt-24">
        <QA on:back={() => navigateTo("dashboard")} />
      </div>
    {/if}
  </main>

  <footer class="border-t border-pe-border mt-8 py-4 px-6">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col md:flex-row justify-between items-center gap-3">
        <div class="text-center md:text-left">
          <p class="font-display font-semibold text-base text-pe-text">
            AI Investment Scout DAO
          </p>
          <p class="text-pe-muted text-xs mt-0.5">
            Decentralized investment evaluation powered by AI
          </p>
        </div>
        <div class="flex items-center gap-4">
          <a
            href="https://github.com"
            class="text-pe-muted hover:text-pe-accent transition-colors text-xs"
            >GitHub</a
          >
          <a
            href="https://neo.org"
            class="text-pe-muted hover:text-pe-accent transition-colors text-xs"
            >NEO</a
          >
          <a
            href="https://spoon.so"
            class="text-pe-muted hover:text-pe-accent transition-colors text-xs"
            >SpoonOS</a
          >
        </div>
      </div>
      <p class="text-center text-pe-text-dim text-xs mt-3">
        Built for Hackat Hackathon 2025
      </p>
    </div>
  </footer>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }
</style>
