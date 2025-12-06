<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { proposalAPI } from '../lib/api.js';
  
  const dispatch = createEventDispatcher();
  
  let proposals = [];
  let loading = true;
  let error = null;
  let filter = 'all'; // 'all', 'active', 'approved', 'rejected'
  
  onMount(async () => {
    await loadProposals();
  });
  
  async function loadProposals() {
    // Safety timeout: ensure loading never stays true forever (reduced to 8 seconds)
    const safetyTimeout = setTimeout(() => {
      if (loading) {
        console.warn('Loading timeout - forcing loading state to false');
        loading = false;
        if (!error) {
          error = 'Backend is not responding. Please check:\n\n1. Is the backend running?\n   uvicorn backend.app.main:app --reload\n\n2. Check backend logs for errors\n\n3. Try refreshing the page';
        }
      }
    }, 8000); // 8 second safety timeout
    
    try {
      loading = true;
      error = null;
      
      // Try to load proposals directly
      const fetchedProposals = await proposalAPI.getProposals();
      
      // Clear safety timeout on success
      clearTimeout(safetyTimeout);
      
      // Ensure we have an array
      if (Array.isArray(fetchedProposals)) {
        proposals = fetchedProposals;
        console.log(`✅ Loaded ${proposals.length} proposals from backend`);
      } else if (fetchedProposals) {
        // If it's not an array but exists, wrap it
        proposals = [fetchedProposals];
        console.warn('⚠️ Backend returned non-array, wrapped it');
      } else {
        proposals = [];
        console.warn('⚠️ Backend returned null/undefined, using empty array');
      }
    } catch (e) {
      console.error('Error loading proposals:', e);
      
      // Clear safety timeout on error
      clearTimeout(safetyTimeout);
      
      // Set error message based on error type
      if (e.message) {
        if (e.message.includes('Cannot connect') || e.message.includes('connection failed') || e.message.includes('fetch')) {
          error = 'Cannot connect to backend.\n\nMake sure the backend is running:\n\n  cd backend\n  uvicorn app.main:app --reload\n\nThe backend should be available at: http://localhost:8000';
        } else if (e.message.includes('timed out') || e.message.includes('timeout')) {
          error = 'Backend request timed out.\n\nThe backend may be:\n• Not running\n• Slow to respond\n• Hanging on a request\n\nCheck the backend terminal for errors.';
        } else if (e.message.includes('Backend returned error')) {
          error = `Backend error: ${e.message}\n\nCheck the backend logs for details.`;
        } else {
          error = `Failed to load proposals:\n\n${e.message}`;
        }
      } else {
        error = 'Failed to load proposals. Check browser console (F12) for details.';
      }
      
      // Ensure proposals is an empty array on error
      proposals = [];
    } finally {
      // Always reset loading state
      clearTimeout(safetyTimeout);
      loading = false;
    }
  }
  
  function selectProposal(id) {
    dispatch('selectProposal', { id });
  }
  
  function getStatusColor(status) {
    switch (status) {
      case 'active': return 'badge-info';
      case 'approved': return 'badge-success';
      case 'rejected': return 'badge-error';
      default: return 'badge-ghost';
    }
  }
  
  function getConfidenceColor(confidence) {
    if (confidence >= 80) return 'text-success';
    if (confidence >= 60) return 'text-warning';
    return 'text-error';
  }
  
  $: filteredProposals = filter === 'all' 
    ? proposals 
    : proposals.filter(p => p.status === filter);
  
  // Debug: Log when proposals change
  $: {
    if (proposals.length > 0) {
      console.log(`📊 Proposals updated: ${proposals.length} total, ${filteredProposals.length} after filter (${filter})`);
    }
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex justify-between items-center">
    <div>
      <h1 class="text-4xl font-bold">Investment Proposals</h1>
      <p class="text-gray-600 mt-2">AI-generated investment memos submitted to the DAO</p>
    </div>
    
    <button 
      class="btn btn-primary btn-lg"
      on:click={loadProposals}
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Refresh
    </button>
  </div>
  
  <!-- Filter tabs -->
  <div class="tabs tabs-boxed">
    <button 
      class="tab"
      class:tab-active={filter === 'all'}
      on:click={() => filter = 'all'}
    >
      All
    </button>
    <button 
      class="tab"
      class:tab-active={filter === 'active'}
      on:click={() => filter = 'active'}
    >
      Active
    </button>
    <button 
      class="tab"
      class:tab-active={filter === 'approved'}
      on:click={() => filter = 'approved'}
    >
      Approved
    </button>
    <button 
      class="tab"
      class:tab-active={filter === 'rejected'}
      on:click={() => filter = 'rejected'}
    >
      Rejected
    </button>
  </div>
  
  <!-- Loading state -->
  {#if loading}
    <div class="flex flex-col justify-center items-center py-20">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="text-gray-500 mt-4">Loading proposals...</p>
      <p class="text-sm text-gray-400 mt-2">If this takes too long, check that the backend is running</p>
    </div>
  {:else if error}
    <!-- Error state -->
    <div class="alert alert-error">
      <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div class="flex-1">
        <div class="whitespace-pre-line">{error}</div>
        <div class="mt-2">
          <button class="btn btn-sm btn-outline" on:click={loadProposals}>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Retry
          </button>
        </div>
      </div>
    </div>
  {:else if filteredProposals.length === 0}
    <!-- Empty state -->
    <div class="text-center py-20">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24 mx-auto text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="text-xl font-semibold mt-4">No proposals found</h3>
      <p class="text-gray-600 mt-2">
        {filter === 'all' ? 'Run the SpoonOS agent to create your first proposal' : `No ${filter} proposals`}
      </p>
    </div>
  {:else}
    <!-- Proposals grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each filteredProposals as proposal}
        <div 
          class="card bg-base-100 shadow-xl card-hover cursor-pointer"
          on:click={() => selectProposal(proposal.id)}
          on:keydown={(e) => e.key === 'Enter' && selectProposal(proposal.id)}
          role="button"
          tabindex="0"
        >
          <div class="card-body">
            <div class="flex justify-between items-start">
              <h2 class="card-title text-lg">{proposal.title}</h2>
              <div class="badge {getStatusColor(proposal.status)}">
                {proposal.status}
              </div>
            </div>
            
            <p class="text-sm text-gray-600 line-clamp-3">{proposal.summary}</p>
            
            <div class="divider my-2"></div>
            
            <div class="flex justify-between items-center text-sm">
              <div>
                <span class="font-semibold">Confidence:</span>
                <span class="ml-2 font-bold {getConfidenceColor(proposal.confidence)}">
                  {proposal.confidence}/100
                </span>
              </div>
              
              <div class="flex gap-2">
                <div class="badge badge-success gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  {proposal.yes_votes}
                </div>
                <div class="badge badge-error gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {proposal.no_votes}
                </div>
              </div>
            </div>
            
            <div class="card-actions justify-end mt-2">
              <button class="btn btn-sm btn-primary">
                View Details
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>

