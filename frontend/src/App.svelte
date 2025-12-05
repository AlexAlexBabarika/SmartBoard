<script>
  import Dashboard from './components/Dashboard.svelte';
  import ProposalDetail from './components/ProposalDetail.svelte';
  import CreateProposal from './components/CreateProposal.svelte';
  import Navbar from './components/Navbar.svelte';
  import { walletStore } from './stores/wallet.js';
  
  let currentView = 'dashboard'; // 'dashboard', 'detail', 'create'
  let selectedProposalId = null;
  
  function navigateTo(view, proposalId = null) {
    currentView = view;
    selectedProposalId = proposalId;
  }
  
  // Mock wallet connection
  function connectWallet() {
    const mockAddress = 'N' + Math.random().toString(36).substring(2, 15);
    walletStore.connect(mockAddress);
  }
  
  function disconnectWallet() {
    walletStore.disconnect();
  }
</script>

<div class="min-h-screen bg-base-200">
  <Navbar 
    {currentView}
    on:navigate={(e) => navigateTo(e.detail.view)}
    on:connectWallet={connectWallet}
    on:disconnectWallet={disconnectWallet}
  />
  
  <main class="container mx-auto px-4 py-8">
    {#if currentView === 'dashboard'}
      <Dashboard on:selectProposal={(e) => navigateTo('detail', e.detail.id)} />
    {:else if currentView === 'detail'}
      <ProposalDetail 
        proposalId={selectedProposalId} 
        on:back={() => navigateTo('dashboard')} 
      />
    {:else if currentView === 'create'}
      <CreateProposal on:back={() => navigateTo('dashboard')} />
    {/if}
  </main>
  
  <footer class="footer footer-center p-10 bg-base-300 text-base-content mt-16">
    <div>
      <p class="font-semibold text-lg">AI Investment Scout DAO</p>
      <p>Decentralized investment proposal evaluation powered by AI and blockchain</p>
      <p class="text-sm opacity-70">Built for Hackat Hackathon 2025</p>
    </div>
    <div>
      <div class="grid grid-flow-col gap-4">
        <a href="https://github.com" class="link link-hover">GitHub</a>
        <a href="https://neo.org" class="link link-hover">NEO</a>
        <a href="https://spoon.so" class="link link-hover">SpoonOS</a>
      </div>
    </div>
  </footer>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }
</style>

