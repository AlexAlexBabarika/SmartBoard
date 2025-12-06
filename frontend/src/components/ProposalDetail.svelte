<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { proposalAPI } from "../lib/api.js";
  import { walletStore } from "../stores/wallet.js";

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
      // Reset gateway when loading new proposal
      currentGateway = 'dweb';
      proposal = await proposalAPI.getProposal(proposalId);
    } catch (e) {
      error = "Failed to load proposal details.";
      console.error("Error loading proposal:", e);
    } finally {
      loading = false;
    }
  }

  async function handleVote(vote) {
    if (!wallet.connected) {
      alert("Please connect your wallet to vote");
      return;
    }

    if (
      !confirm(`Are you sure you want to vote ${vote === 1 ? "YES" : "NO"}?`)
    ) {
      return;
    }

    try {
      voting = true;
      await proposalAPI.vote(proposalId, wallet.address, vote);
      await loadProposal(); // Reload to see updated votes
      alert("Vote submitted successfully!");
    } catch (e) {
      alert("Failed to submit vote: " + e.message);
      console.error("Error voting:", e);
    } finally {
      voting = false;
    }
  }

  async function handleFinalize() {
    if (
      !confirm(
        "Are you sure you want to finalize this proposal? This will close voting.",
      )
    ) {
      return;
    }

    try {
      finalizing = true;
      await proposalAPI.finalize(proposalId);
      await loadProposal();
      alert("Proposal finalized successfully!");
    } catch (e) {
      alert("Failed to finalize proposal: " + e.message);
      console.error("Error finalizing:", e);
    } finally {
      finalizing = false;
    }
  }

  let currentGateway = 'dweb'; // Use dweb.link for viewing PDFs

  function getIpfsUrl(cid, gateway = null) {
    // Support multiple IPFS gateway options for reliability
    // If CID is already a full URL, return it as-is
    if (cid.startsWith('http://') || cid.startsWith('https://')) {
      return cid;
    }
    // Remove any path/gateway prefix if present
    const cleanCid = cid.replace(/^https?:\/\/[^/]+\/ipfs\//, '').replace(/^ipfs:\/\//, '');
    
    // Use different gateways - ordered by reliability
    const gateways = {
      'ipfs': `https://ipfs.io/ipfs/${cleanCid}`,           // Most reliable public gateway
      'dweb': `https://dweb.link/ipfs/${cleanCid}`,        // Protocol Labs gateway
      'cloudflare': `https://cloudflare-ipfs.com/ipfs/${cleanCid}`,  // Cloudflare (sometimes has issues)
      'gateway': `https://gateway.pinata.cloud/ipfs/${cleanCid}`,   // Pinata gateway
      'storacha': `https://storacha.link/ipfs/${cleanCid}` // Original gateway
    };
    
    const gatewayName = gateway || currentGateway;
    return gateways[gatewayName] || gateways['ipfs'];
  }
  
  async function handleDownload(cid) {
    // Try multiple gateways if one fails - ordered by reliability
    const gateways = ['ipfs', 'dweb', 'gateway', 'cloudflare', 'storacha'];
    
    for (const gateway of gateways) {
      try {
        const url = getIpfsUrl(cid, gateway);
        console.log(`Attempting download from ${gateway} gateway: ${url}`);
        
        // For downloads, we need to fetch as blob
        // If CORS is an issue, fall back to direct link
        // Create timeout abort controller for older browsers
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch(url, {
          method: 'GET',
          mode: 'cors',
          cache: 'default',
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const blob = await response.blob();
        
        // Check if we got an error page instead of PDF
        if (blob.size < 100) {
          throw new Error('Response too small, might be an error page');
        }
        
        // Verify it's a PDF
        if (blob.type && !blob.type.includes('pdf') && !blob.type.includes('octet-stream')) {
          console.warn(`Unexpected content type: ${blob.type}`);
        }
        
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `proposal-${proposalId || 'memo'}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
        
        console.log(`Successfully downloaded from ${gateway} gateway`);
        return; // Success, exit function
      } catch (error) {
        console.warn(`Download failed from ${gateway} gateway:`, error);
        // Continue to next gateway
        if (error.name === 'AbortError') {
          console.warn(`Download timeout from ${gateway} gateway`);
        }
        continue;
      }
    }
    
    // If all gateways failed, offer direct link as fallback
    const fallbackUrl = getIpfsUrl(cid, 'ipfs');
    const userConfirmed = confirm(
      `Direct download failed from all gateways.\n\n` +
      `This might be due to:\n` +
      `- CORS restrictions\n` +
      `- The file not being available yet\n` +
      `- Network connectivity issues\n\n` +
      `Click OK to open the PDF in a new tab where you can download it manually.`
    );
    
    if (userConfirmed) {
      window.open(fallbackUrl, '_blank', 'noopener,noreferrer');
    }
  }

  function goBack() {
    dispatch("back");
  }
</script>

<div class="space-y-6">
  <!-- Back button -->
  <button class="btn btn-ghost" on:click={goBack}>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 mr-2"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M15 19l-7-7 7-7"
      />
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
          <div
            class="badge badge-lg {proposal.status === 'active'
              ? 'badge-info'
              : proposal.status === 'approved'
                ? 'badge-success'
                : 'badge-error'}"
          >
            {proposal.status.toUpperCase()}
          </div>
        </div>

        <!-- Metrics -->
        <div class="stats stats-horizontal shadow mt-4">
          <div class="stat">
            <div class="stat-title">Confidence Score</div>
            <div
              class="stat-value text-3xl {proposal.confidence >= 80
                ? 'text-success'
                : proposal.confidence >= 60
                  ? 'text-warning'
                  : 'text-error'}"
            >
              {proposal.confidence}/100
            </div>
          </div>

          <div class="stat">
            <div class="stat-title">Yes Votes</div>
            <div class="stat-value text-3xl text-success">
              {proposal.yes_votes}
            </div>
          </div>

          <div class="stat">
            <div class="stat-title">No Votes</div>
            <div class="stat-value text-3xl text-error">
              {proposal.no_votes}
            </div>
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Investment Memo (IPFS)
        </h2>

        <div class="bg-gray-100 p-4 rounded-lg">
          <p class="text-sm mb-2">
            <span class="font-semibold">IPFS CID:</span>
            <code class="ml-2 bg-gray-200 px-2 py-1 rounded"
              >{proposal.ipfs_cid}</code
            >
          </p>

          <div class="flex gap-2">
            <button
              type="button"
              on:click={() => handleDownload(proposal.ipfs_cid)}
              class="btn btn-secondary btn-sm"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download PDF
            </button>
          </div>
        </div>

        <!-- Demo Mode Notice -->
        {#if proposal.ipfs_cid.startsWith("bafysim")}
          <div class="alert alert-info mt-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              class="stroke-current shrink-0 w-6 h-6"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              ></path>
            </svg>
            <div class="text-sm">
              <p>
                <strong>Demo Mode:</strong> This is a simulated IPFS CID. The PDF
                won't load because it wasn't actually uploaded.
              </p>
              <p class="mt-1">
                To enable real IPFS uploads, install the Storacha CLI, run
                <code>storacha login</code>, select a space with
                <code>storacha space use &lt;space&gt;</code>, and set
                <code>DEMO_MODE=false</code>.
              </p>
            </div>
          </div>
        {/if}

        <!-- PDF Preview iframe -->
        <div
          class="mt-4 border-2 border-gray-300 rounded-lg overflow-hidden bg-gray-50 relative"
          style="height: 600px;"
        >
          <iframe
            src={getIpfsUrl(proposal.ipfs_cid, currentGateway)}
            title="Investment Memo PDF"
            class="w-full h-full"
            frameborder="0"
          ></iframe>
        </div>
      </div>
    </div>

    <!-- Voting Actions -->
    {#if proposal.status === "active"}
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Cast Your Vote</h2>

          {#if !wallet.connected}
            <div class="alert alert-warning">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="stroke-current shrink-0 h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
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
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-6 w-6 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
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
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-6 w-6 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
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
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            {/if}
            Finalize Proposal
          </button>
        </div>
      </div>
    {/if}
  {/if}
</div>
