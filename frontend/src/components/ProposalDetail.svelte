<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { proposalAPI } from '../lib/api.js';
  import { walletStore } from '../stores/wallet.js';
  
  export let proposalId;
  
  const dispatch = createEventDispatcher();
  
  let proposal = null;
  let loading = true;
  let error = null;
  let voting = false;
  let finalizing = false;
  
  $: wallet = $walletStore;
  
  onMount(async () => {
    await loadProposal();
  });
  
  async function loadProposal() {
    try {
      loading = true;
      error = null;
      proposal = await proposalAPI.getProposal(proposalId);
    } catch (e) {
      error = 'Failed to load proposal details.';
      console.error('Error loading proposal:', e);
    } finally {
      loading = false;
    }
  }
  
  async function handleVote(vote) {
    if (!wallet.connected) {
      alert('Please connect your wallet to vote');
      return;
    }
    
    if (!confirm(`Are you sure you want to vote ${vote === 1 ? 'YES' : 'NO'}?`)) {
      return;
    }
    
    try {
      voting = true;
      await proposalAPI.vote(proposalId, wallet.address, vote);
      await loadProposal(); // Reload to see updated votes
      alert('Vote submitted successfully!');
    } catch (e) {
      alert('Failed to submit vote: ' + e.message);
      console.error('Error voting:', e);
    } finally {
      voting = false;
    }
  }
  
  async function handleFinalize() {
    if (!confirm('Are you sure you want to finalize this proposal? This will close voting.')) {
      return;
    }
    
    try {
      finalizing = true;
      await proposalAPI.finalize(proposalId);
      await loadProposal();
      alert('Proposal finalized successfully!');
    } catch (e) {
      alert('Failed to finalize proposal: ' + e.message);
      console.error('Error finalizing:', e);
    } finally {
      finalizing = false;
    }
  }
  
  function getIpfsUrl(cid) {
    return `https://w3s.link/ipfs/${cid}`;
  }
  
  function goBack() {
    dispatch('back');
  }
</script>

<div class="space-y-6">
  <!-- Back button -->
  <button class="btn btn-ghost" on:click={goBack}>
    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
    </svg>
    Back to Dashboard
  </button>
  
  {#if loading}
    <div class="flex justify-center items-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else if error}
    <div class="alert alert-error">
      <span>{error}</span>
    </div>
  {:else if proposal}
    <!-- Proposal header -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <h1 class="text-3xl font-bold">{proposal.title}</h1>
            <p class="text-sm text-gray-500 mt-2">
              Created: {new Date(proposal.created_at).toLocaleString()}
            </p>
          </div>
          <div class="badge badge-lg {proposal.status === 'active' ? 'badge-info' : proposal.status === 'approved' ? 'badge-success' : 'badge-error'}">
            {proposal.status.toUpperCase()}
          </div>
        </div>
        
        <!-- Metrics -->
        <div class="stats stats-horizontal shadow mt-4">
          <div class="stat">
            <div class="stat-title">Confidence Score</div>
            <div class="stat-value text-3xl {proposal.confidence >= 80 ? 'text-success' : proposal.confidence >= 60 ? 'text-warning' : 'text-error'}">
              {proposal.confidence}/100
            </div>
          </div>
          
          <div class="stat">
            <div class="stat-title">Yes Votes</div>
            <div class="stat-value text-3xl text-success">{proposal.yes_votes}</div>
          </div>
          
          <div class="stat">
            <div class="stat-title">No Votes</div>
            <div class="stat-value text-3xl text-error">{proposal.no_votes}</div>
          </div>
        </div>
        
        <!-- Summary -->
        <div class="mt-4">
          <h3 class="text-xl font-semibold mb-2">Summary</h3>
          <p class="text-gray-700">{proposal.summary}</p>
        </div>
      </div>
    </div>
    
    <!-- PDF Viewer -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Investment Memo (IPFS)
        </h2>
        
        <div class="bg-gray-100 p-4 rounded-lg">
          <p class="text-sm mb-2">
            <span class="font-semibold">IPFS CID:</span>
            <code class="ml-2 bg-gray-200 px-2 py-1 rounded">{proposal.ipfs_cid}</code>
          </p>
          
          <div class="flex gap-2">
            <a 
              href={getIpfsUrl(proposal.ipfs_cid)} 
              target="_blank" 
              rel="noopener noreferrer"
              class="btn btn-primary btn-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              View on IPFS
            </a>
            
            <a 
              href={getIpfsUrl(proposal.ipfs_cid)} 
              download
              class="btn btn-secondary btn-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download PDF
            </a>
          </div>
        </div>
        
        <!-- PDF Preview iframe -->
        <div class="mt-4 border-2 border-gray-300 rounded-lg overflow-hidden" style="height: 600px;">
          <iframe 
            src={getIpfsUrl(proposal.ipfs_cid)}
            title="Investment Memo PDF"
            class="w-full h-full"
            frameborder="0"
          ></iframe>
        </div>
      </div>
    </div>
    
    <!-- Voting Actions -->
    {#if proposal.status === 'active'}
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Cast Your Vote</h2>
          
          {#if !wallet.connected}
            <div class="alert alert-warning">
              <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>Please connect your wallet to vote</span>
            </div>
          {/if}
          
          <div class="flex gap-4 mt-4">
            <button 
              class="btn btn-success btn-lg flex-1"
              disabled={!wallet.connected || voting}
              on:click={() => handleVote(1)}
            >
              {#if voting}
                <span class="loading loading-spinner"></span>
              {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              {/if}
              Vote YES
            </button>
            
            <button 
              class="btn btn-error btn-lg flex-1"
              disabled={!wallet.connected || voting}
              on:click={() => handleVote(0)}
            >
              {#if voting}
                <span class="loading loading-spinner"></span>
              {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              {/if}
              Vote NO
            </button>
          </div>
          
          <div class="divider">OR</div>
          
          <button 
            class="btn btn-warning"
            disabled={finalizing}
            on:click={handleFinalize}
          >
            {#if finalizing}
              <span class="loading loading-spinner"></span>
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            {/if}
            Finalize Proposal
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>

