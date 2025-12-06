<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { proposalAPI } from "../lib/api.js";
  import { walletStore } from "../stores/wallet.js";
  import FloatingNetwork from "./FloatingNetwork.svelte";

  export let proposalId;

  const dispatch = createEventDispatcher();

  let windowWidth = 1920;
  let windowHeight = 1080;

  onMount(async () => {
    windowWidth = window.innerWidth;
    windowHeight = window.innerHeight;

    const handleResize = () => {
      windowWidth = window.innerWidth;
      windowHeight = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);

    await loadProposal();

    return () => window.removeEventListener("resize", handleResize);
  });

  let proposal = null;
  let loading = true;
  let error = null;
  let voting = false;
  let finalizing = false;
  let pdfLoading = true;

  $: wallet = $walletStore;

  async function loadProposal() {
    try {
      loading = true;
      pdfLoading = true;
      error = null;
      currentGateway = "dweb";
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
      await loadProposal();
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

  let currentGateway = "dweb";

  function getIpfsUrl(cid, gateway = null) {
    if (cid.startsWith("http://") || cid.startsWith("https://")) {
      return cid;
    }
    const cleanCid = cid
      .replace(/^https?:\/\/[^/]+\/ipfs\//, "")
      .replace(/^ipfs:\/\//, "");

    const gateways = {
      ipfs: `https://ipfs.io/ipfs/${cleanCid}`,
      dweb: `https://dweb.link/ipfs/${cleanCid}`,
      cloudflare: `https://cloudflare-ipfs.com/ipfs/${cleanCid}`,
      gateway: `https://gateway.pinata.cloud/ipfs/${cleanCid}`,
      storacha: `https://storacha.link/ipfs/${cleanCid}`,
    };

    const gatewayName = gateway || currentGateway;
    return gateways[gatewayName] || gateways["ipfs"];
  }

  async function handleDownload(cid) {
    const gateways = ["ipfs", "dweb", "gateway", "cloudflare", "storacha"];

    for (const gateway of gateways) {
      try {
        const url = getIpfsUrl(cid, gateway);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(url, {
          method: "GET",
          mode: "cors",
          cache: "default",
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const blob = await response.blob();

        if (blob.size < 100) {
          throw new Error("Response too small");
        }

        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = `proposal-${proposalId || "memo"}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);

        return;
      } catch (error) {
        continue;
      }
    }

    const fallbackUrl = getIpfsUrl(cid, "ipfs");
    if (
      confirm("Direct download failed. Click OK to open the PDF in a new tab.")
    ) {
      window.open(fallbackUrl, "_blank", "noopener,noreferrer");
    }
  }

  function goBack() {
    dispatch("back");
  }

  function getStatusColor(status) {
    switch (status) {
      case "active":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "approved":
        return "bg-pe-accent/20 text-pe-accent border-pe-accent/30";
      case "rejected":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-pe-muted/20 text-pe-muted border-pe-muted/30";
    }
  }
</script>

<div class="relative min-h-screen">
  <!-- Floating Network Background -->
  <div
    class="fixed inset-0 w-screen h-screen z-0 pointer-events-none overflow-hidden opacity-40"
  >
    {#if loading || !proposal}
      <FloatingNetwork
        width={windowWidth}
        height={windowHeight}
        yesVotes={8}
        noVotes={3}
        className="w-full h-full"
      />
    {:else}
      <FloatingNetwork
        width={windowWidth}
        height={windowHeight}
        yesVotes={Math.max(proposal.yes_votes || 0, 5)}
        noVotes={Math.max(proposal.no_votes || 0, 2)}
        className="w-full h-full"
      />
    {/if}
  </div>

  <!-- Content -->
  <div class="relative z-10 space-y-6 animate-fade-in">
    <!-- Back button -->
    <button
      class="flex items-center gap-2 px-4 py-2 rounded-pe text-pe-muted hover:text-pe-text hover:bg-pe-card transition-colors focus-ring"
      on:click={goBack}
    >
      <svg
        class="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M15 19l-7-7 7-7"
        />
      </svg>
      Back to Dashboard
    </button>

    {#if loading}
      <div class="flex flex-col justify-center items-center py-20">
        <div
          class="w-12 h-12 border-3 border-pe-accent/30 border-t-pe-accent rounded-full animate-spin"
        ></div>
        <p class="text-pe-muted mt-4">Loading proposal...</p>
      </div>
    {:else if error}
      <div
        class="flex items-start gap-4 p-4 rounded-pe-lg bg-red-500/10 border border-red-500/20"
      >
        <svg
          class="w-6 h-6 text-red-500 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span class="text-red-400">{error}</span>
      </div>
    {:else if proposal}
      <!-- Proposal header -->
      <div class="card-pe p-6 bg-pe-card/20 backdrop-blur-md">
        <div
          class="flex flex-col md:flex-row justify-between items-start gap-4"
        >
          <div class="flex-1">
            <h1 class="font-display text-3xl font-bold text-pe-text">
              {proposal.title}
            </h1>
            <p class="text-sm text-pe-muted mt-2">
              Created: {new Date(proposal.created_at).toLocaleString()}
            </p>
          </div>
          <span
            class="px-4 py-2 rounded-pe border text-sm font-medium uppercase tracking-wide {getStatusColor(
              proposal.status,
            )}"
          >
            {proposal.status}
          </span>
        </div>

        <!-- Metrics -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
          <div class="p-4 rounded-pe bg-pe-panel border border-pe-border">
            <p class="text-xs text-pe-muted uppercase tracking-wide">
              Confidence Score
            </p>
            <p
              class="text-2xl font-display font-bold mt-1
            {proposal.confidence >= 80
                ? 'text-pe-accent'
                : proposal.confidence >= 60
                  ? 'text-yellow-400'
                  : 'text-red-400'}"
            >
              {proposal.confidence}/100
            </p>
          </div>

          <div class="p-4 rounded-pe bg-pe-panel border border-pe-border">
            <p class="text-xs text-pe-muted uppercase tracking-wide">
              Yes Votes
            </p>
            <p class="text-2xl font-display font-bold mt-1 text-pe-accent">
              {proposal.yes_votes}
            </p>
          </div>

          <div class="p-4 rounded-pe bg-pe-panel border border-pe-border">
            <p class="text-xs text-pe-muted uppercase tracking-wide">
              No Votes
            </p>
            <p class="text-2xl font-display font-bold mt-1 text-red-400">
              {proposal.no_votes}
            </p>
          </div>
        </div>

        <!-- Summary -->
        <div class="mt-6">
          <h3 class="font-display font-semibold text-pe-text mb-2">Summary</h3>
          <p class="text-pe-muted leading-relaxed">{proposal.summary}</p>
        </div>
      </div>

      <!-- PDF Viewer -->
      <div class="card-pe p-6 bg-pe-card/20 backdrop-blur-md">
        <h2
          class="flex items-center gap-2 font-display font-semibold text-lg text-pe-text"
        >
          <svg
            class="h-5 w-5 text-pe-accent"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Investment Memo (IPFS)
        </h2>

        <div class="mt-4 p-4 rounded-pe bg-pe-panel border border-pe-border">
          <p class="text-sm">
            <span class="text-pe-muted">IPFS CID:</span>
            <code
              class="ml-2 px-2 py-1 rounded bg-pe-bg text-pe-text font-mono text-xs"
              >{proposal.ipfs_cid}</code
            >
          </p>

          <div class="flex gap-3 mt-4">
            <button
              type="button"
              on:click={() => handleDownload(proposal.ipfs_cid)}
              class="btn-accent-pe flex items-center gap-2"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download PDF
            </button>
          </div>
        </div>

        <!-- Demo Mode Notice -->
        {#if proposal.ipfs_cid.startsWith("bafysim")}
          <div
            class="flex items-start gap-4 p-4 mt-4 rounded-pe-lg bg-blue-500/10 border border-blue-500/20"
          >
            <svg
              class="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div class="text-sm">
              <p class="text-blue-300">
                <strong>Demo Mode:</strong> This is a simulated IPFS CID. The PDF
                won't load because it wasn't actually uploaded.
              </p>
              <p class="text-blue-400/70 mt-1">
                To enable real IPFS uploads, install the Storacha CLI and set <code
                  class="bg-blue-500/20 px-1 rounded">DEMO_MODE=false</code
                >.
              </p>
            </div>
          </div>
        {/if}

        <!-- PDF Preview iframe -->
        <div
          class="mt-4 border border-pe-border rounded-pe-lg overflow-hidden bg-pe-panel relative"
          style="height: 600px;"
        >
          {#if pdfLoading}
            <div
              class="absolute inset-0 flex flex-col items-center justify-center bg-pe-panel"
            >
              <div
                class="w-12 h-12 border-3 border-pe-accent/30 border-t-pe-accent rounded-full animate-spin"
              ></div>
              <p class="text-pe-muted mt-4">Loading PDF...</p>
            </div>
          {/if}
          <iframe
            src={getIpfsUrl(proposal.ipfs_cid, currentGateway)}
            title="Investment Memo PDF"
            class="w-full h-full bg-white"
            on:load={() => (pdfLoading = false)}
            on:error={() => (pdfLoading = false)}
          ></iframe>
        </div>
      </div>

      <!-- Voting Actions -->
      {#if proposal.status === "active"}
        <div class="card-pe p-6 bg-pe-card/20 backdrop-blur-md">
          <h2 class="font-display font-semibold text-lg text-pe-text">
            Cast Your Vote
          </h2>

          {#if !wallet.connected}
            <div
              class="flex items-start gap-4 p-4 mt-4 rounded-pe-lg bg-yellow-500/10 border border-yellow-500/20"
            >
              <svg
                class="w-6 h-6 text-yellow-400 flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span class="text-yellow-300"
                >Please connect your wallet to vote</span
              >
            </div>
          {/if}

          <div class="flex gap-4 mt-6">
            <button
              class="flex-1 py-4 rounded-pe-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2
              bg-pe-accent/20 text-pe-accent border border-pe-accent/30 hover:bg-pe-accent hover:text-white
              disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!wallet.connected || voting}
              on:click={() => handleVote(1)}
            >
              {#if voting}
                <div
                  class="w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin"
                ></div>
              {:else}
                <svg
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              {/if}
              Vote YES
            </button>

            <button
              class="flex-1 py-4 rounded-pe-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2
              bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500 hover:text-white
              disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!wallet.connected || voting}
              on:click={() => handleVote(0)}
            >
              {#if voting}
                <div
                  class="w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin"
                ></div>
              {:else}
                <svg
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              {/if}
              Vote NO
            </button>
          </div>

          <div class="relative flex items-center py-6">
            <div class="flex-grow border-t border-pe-border"></div>
            <span class="flex-shrink mx-4 text-pe-muted text-sm">OR</span>
            <div class="flex-grow border-t border-pe-border"></div>
          </div>

          <button
            class="w-full py-3 rounded-pe-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2
            bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500 hover:text-white
            disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={finalizing}
            on:click={handleFinalize}
          >
            {#if finalizing}
              <div
                class="w-5 h-5 border-2 border-current/30 border-t-current rounded-full animate-spin"
              ></div>
            {:else}
              <svg
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            {/if}
            Finalize Proposal
          </button>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  }
</style>
