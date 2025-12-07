<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { proposalAPI } from "../lib/api.js";
  import {
    filtersStore,
    favoritesStore,
    activeFilters,
    availableTags,
    sampleProducts,
  } from "../stores/filters.js";
  import FloatingNetwork from "./FloatingNetwork.svelte";

  const dispatch = createEventDispatcher();

  let proposals = [];
  let loading = true;
  let error = null;
  let sidebarOpen = true;
  let searchTimeout;
  let mainContentElement;
  let contentWidth = 1200;
  let contentHeight = 800;
  let searchSources = ["producthunt"];
  let proposalLimit = 5;
  let additionalFields = "";
  let searching = false;
  let searchStatus = "";
  let searchError = null;
  let searchJobId = null;
  let statusPolling = false;
  let searchStartedAt = null;
  let lastSelectedSources = [];
  const MAX_POLL_ATTEMPTS = 60; // ~3 minutes at 3s interval
  const POLL_DELAY_MS = 3000;
  const STATUS_POLL_DELAY_MS = 3000;

  // Subscribe to stores
  $: filters = $filtersStore;
  $: favorites = $favoritesStore;
  $: activeFiltersList = $activeFilters;

  // Filter proposals based on filters
  $: products = (() => {
    let filtered = [...proposals];

    // Apply search filter
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          (p.title || "").toLowerCase().includes(query) ||
          (p.subtitle || p.summary || "").toLowerCase().includes(query),
      );
    }

    // Apply category filter
    if (filters.category !== "all") {
      filtered = filtered.filter((p) => {
        // Check if proposal has category field, or use metadata
        const proposalCategory =
          p.category || p.metadata?.category || p.metadata?.sector || "";
        return proposalCategory === filters.category;
      });
    }

    // Apply status filter
    if (filters.status && filters.status !== "all") {
      filtered = filtered.filter((p) => {
        const status = p.status || "active";
        return status === filters.status;
      });
    }

    // Apply confidence range filter
    filtered = filtered.filter((p) => {
      const confidence =
        p.confidence !== undefined && p.confidence !== null ? p.confidence : 0;
      return (
        confidence >= filters.confidenceMin &&
        confidence <= filters.confidenceMax
      );
    });

    // Apply size filter (if any sizes selected)
    if (filters.sizes.length > 0) {
      filtered = filtered.filter((p) => {
        const proposalSize = p.size || p.metadata?.size || "";
        return filters.sizes.includes(proposalSize);
      });
    }

    // Apply tag filter (if any tags selected, product must have at least one matching tag)
    if (filters.tags.length > 0) {
      filtered = filtered.filter((p) => {
        const proposalTags = p.tags || p.metadata?.tags || [];
        return (
          Array.isArray(proposalTags) &&
          proposalTags.some((tag) => filters.tags.includes(tag))
        );
      });
    }

    // Apply sorting
    switch (filters.sortBy) {
      case "confidence-asc":
        filtered.sort((a, b) => (a.confidence || 0) - (b.confidence || 0));
        break;
      case "confidence-desc":
        filtered.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));
        break;
      case "name":
        filtered.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
        break;
      case "status":
        filtered.sort((a, b) => {
          const statusA = (a.status || "active").toLowerCase();
          const statusB = (b.status || "active").toLowerCase();
          const statusOrder = { active: 1, approved: 2, rejected: 3 };
          return (statusOrder[statusA] || 99) - (statusOrder[statusB] || 99);
        });
        break;
      default:
        // Keep original order
        break;
    }

    // Add favorite status from favorites store
    return filtered.map((p) => ({
      ...p,
      favorite: favorites.has(p.id),
      // Ensure required fields exist for display
      image: getProposalImage(p),
      subtitle: p.subtitle || p.summary || "",
      confidence: p.confidence || 0,
      status: p.status || "active",
      yes_votes: p.yes_votes || 0,
      no_votes: p.no_votes || 0,
    }));
  })();

  // Calculate confidence histogram from actual proposals
  $: confidenceHistogram = (() => {
    // Create bins for confidence ranges (0-10, 10-20, ..., 90-100)
    const bins = Array.from({ length: 10 }, (_, i) => ({
      min: i * 10,
      max: (i + 1) * 10,
      count: 0
    }));

    // Count proposals in each bin
    proposals.forEach((proposal) => {
      const confidence = proposal.confidence !== undefined && proposal.confidence !== null 
        ? proposal.confidence 
        : 0;
      
      // Find the appropriate bin
      const binIndex = Math.min(
        Math.floor(confidence / 10),
        9 // Cap at last bin (90-100)
      );
      
      if (binIndex >= 0 && binIndex < bins.length) {
        bins[binIndex].count++;
      }
    });

    return bins;
  })();

  // Get max histogram count for scaling bars
  $: maxHistogramCount = confidenceHistogram.length > 0 
    ? Math.max(...confidenceHistogram.map((h) => h.count), 1) 
    : 1;

  // Helper function to generate beautiful SVG gradient placeholder
  function getGradientPlaceholder(proposal) {
    const seed = proposal.id || Math.random() * 1000;
    const colors = [
      ["#667eea", "#764ba2"], // Purple gradient
      ["#f093fb", "#f5576c"], // Pink gradient
      ["#4facfe", "#00f2fe"], // Blue gradient
      ["#43e97b", "#38f9d7"], // Green gradient
      ["#fa709a", "#fee140"], // Pink-yellow gradient
      ["#30cfd0", "#330867"], // Teal-purple gradient
      ["#a8edea", "#fed6e3"], // Mint-pink gradient
      ["#ff9a9e", "#fecfef"], // Rose gradient
      ["#ffecd2", "#fcb69f"], // Peach gradient
      ["#ff8a80", "#ea4c89"], // Coral gradient
    ];
    const colorIndex = Math.floor(seed) % colors.length;
    const [color1, color2] = colors[colorIndex];
    
    // Create a beautiful SVG gradient placeholder
    const svg = `<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad-${seed}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:${color1};stop-opacity:1" />
          <stop offset="100%" style="stop-color:${color2};stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="400" height="400" fill="url(#grad-${seed})" />
      <circle cx="200" cy="150" r="40" fill="white" opacity="0.3" />
      <circle cx="250" cy="200" r="30" fill="white" opacity="0.2" />
      <circle cx="150" cy="250" r="35" fill="white" opacity="0.25" />
    </svg>`;
    
    // Use URI encoding for better compatibility
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  }

  // Helper function to generate beautiful placeholder image based on proposal ID
  function getProposalImage(proposal) {
    if (proposal.image) return proposal.image;

    // Generate a unique seed based on proposal ID for consistent images
    const seed = proposal.id || Math.random() * 1000;
    
    // Use Picsum Photos for beautiful random images with consistent seeding
    // This provides high-quality, beautiful placeholder images
    return `https://picsum.photos/seed/${seed}/400/400`;
  }

  // Handle image load errors by falling back to gradient placeholder
  function handleImageError(event, proposal) {
    if (event.target.src && !event.target.src.includes('data:image/svg+xml')) {
      event.target.src = getGradientPlaceholder(proposal);
    }
  }

  function getStatusBadgeClasses(status) {
    switch ((status || "active").toLowerCase()) {
      case "approved":
        return "bg-pe-accent/15 text-pe-accent border-pe-accent/30";
      case "rejected":
        return "bg-red-500/15 text-red-400 border-red-500/30";
      default:
        return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    }
  }

  // Calculate category counts dynamically from proposals
  $: categoryCounts = (() => {
    const counts = {
      all: proposals.length,
      "AI & ML": 0,
      Healthcare: 0,
      CleanTech: 0,
      Web3: 0,
      FinTech: 0,
    };

    proposals.forEach((p) => {
      const category =
        p.category || p.metadata?.category || p.metadata?.sector || "";
      if (category && counts.hasOwnProperty(category)) {
        counts[category]++;
      }
    });

    return counts;
  })();

  // Available categories with dynamic counts
  $: availableCategories = [
    { name: "All Proposals", count: categoryCounts.all, key: "all" },
    { name: "AI & ML", count: categoryCounts["AI & ML"], key: "AI & ML" },
    {
      name: "Healthcare",
      count: categoryCounts["Healthcare"],
      key: "Healthcare",
    },
    { name: "CleanTech", count: categoryCounts["CleanTech"], key: "CleanTech" },
    { name: "Web3", count: categoryCounts["Web3"], key: "Web3" },
    { name: "FinTech", count: categoryCounts["FinTech"], key: "FinTech" },
  ];

  onMount(async () => {
    await loadProposals();

    // Update content dimensions for floating network
    const updateDimensions = () => {
      if (mainContentElement) {
        contentWidth = mainContentElement.clientWidth;
        contentHeight = mainContentElement.clientHeight;
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);

    return () => window.removeEventListener("resize", updateDimensions);
  });

  async function loadProposals({ useSampleFallback = true } = {}) {
    const safetyTimeout = setTimeout(() => {
      if (loading && useSampleFallback && !searching) {
        loading = false;
        error = "Backend unavailable. Please check if the server is running.";
        // Don't use sample data on timeout - show empty state instead
        proposals = [];
      }
    }, 5000);

    try {
      loading = true;
      error = null;

      // Try to load from API
      if (typeof proposalAPI !== "undefined" && proposalAPI.getProposals) {
        const fetchedProposals = await proposalAPI.getProposals();
        clearTimeout(safetyTimeout);

        if (Array.isArray(fetchedProposals)) {
          const filtered = applySearchFilters(fetchedProposals, searching);
          proposals = filtered;
        } else {
          // Invalid response format
          proposals = [];
          error = "Invalid response from server";
        }
      } else {
        // API not available
        proposals = [];
        error = "API not available";
      }
    } catch (e) {
      clearTimeout(safetyTimeout);
      // On error, show empty state instead of sample data
      proposals = [];
      error = `Failed to load proposals: ${e.message || "Unknown error"}`;
      console.error("Error loading proposals:", e);
    } finally {
      clearTimeout(safetyTimeout);
      loading = false;
    }
  }

  async function initiateSearch() {
    searchError = null;
    searchStatus = "";
    searchJobId = null;
    searchStartedAt = new Date();
    proposals = []; // Clear existing proposals immediately so UI shows empty state

    const selectedSources = Array.isArray(searchSources)
      ? searchSources.filter(Boolean)
      : [];

    if (selectedSources.length === 0) {
      searchError = "Select at least one data source.";
      return;
    }

    const limit = Math.max(1, Math.min(50, Number(proposalLimit) || 1));
    lastSelectedSources = [...selectedSources];

    searching = true;
    loading = true;
    proposals = [];

    try {
      const payload = {
        sources: selectedSources,
        limit_per_source: limit,
        auto_process: true,
      };

      if (additionalFields.trim()) {
        payload.additional_fields = additionalFields.trim();
      }

      const response = await proposalAPI.discoverStartups(payload);
      searchJobId = response?.job_id || null;
      searchStatus =
        response?.message ||
        "Search started. New proposals will appear once ready.";

      // Poll backend job status (non-blocking) if job id is provided
      if (searchJobId) {
        pollJobStatus(searchJobId);
      }

      const found = await waitForProposals();
      if (!found) {
        searchStatus =
          "Search started. Waiting for new proposals... (none received yet)";
      }
    } catch (e) {
      searchError = e?.message || "Failed to start discovery.";
      loading = false;
    } finally {
      searching = false;
    }
  }

  async function waitForProposals() {
    for (let attempt = 1; attempt <= MAX_POLL_ATTEMPTS; attempt++) {
      const fetched = await proposalAPI.getProposals().catch(() => null);
      const filtered = applySearchFilters(fetched, true);
      if (Array.isArray(filtered) && filtered.length > 0) {
        proposals = filtered;
        loading = false;
        return true;
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_DELAY_MS));
    }
    loading = false;
    return false;
  }

  async function pollJobStatus(jobId) {
    if (!jobId || statusPolling) return;
    statusPolling = true;
    try {
      for (let attempt = 1; attempt <= MAX_POLL_ATTEMPTS; attempt++) {
        const status = await proposalAPI.getDiscoveryStatus(jobId).catch(() => null);
        if (status?.message) {
          searchStatus = status.message;
        }
        if (status?.status === "completed") {
          searchStatus = status.message || "Discovery completed";
          break;
        }
        if (status?.status === "failed") {
          searchStatus = status.message || "Discovery failed";
          searchError = status.error || searchError;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, STATUS_POLL_DELAY_MS));
      }
    } finally {
      statusPolling = false;
    }
  }

  function applySearchFilters(fetched, respectSearchWindow = false) {
    if (!Array.isArray(fetched)) return [];
    // If not currently searching, just return fetched
    if (!searching && !respectSearchWindow) return fetched;

    return fetched.filter((p) => {
      const source = p?.metadata?.source || p?.source;
      if (lastSelectedSources.length > 0 && source && !lastSelectedSources.includes(source)) {
        return false;
      }

      if (respectSearchWindow && searchStartedAt) {
        const created =
          Date.parse(p?.created_at) ||
          Date.parse(p?.metadata?.created_at || p?.metadata?.timestamp || "");
        if (!Number.isNaN(created) && created < searchStartedAt.getTime() - 2000) {
          return false;
        }
      }

      return true;
    });
  }

  function selectProposal(id) {
    dispatch("selectProposal", { id });
  }

  function handleSearchInput(e) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      filtersStore.setSearch(e.target.value);
    }, 300); // Debounce 300ms
  }

  function toggleFavorite(id, e) {
    e.stopPropagation();
    favoritesStore.toggle(id);
  }

  function removeFilter(filter) {
    filtersStore.removeFilter(filter.type, filter.value);
  }

  function getStaggerClass(index) {
    return `stagger-${(index % 6) + 1}`;
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  // Generate ASCII balls for votes
  function generateVoteBalls(yesVotes, noVotes, maxBalls = 20) {
    const totalVotes = yesVotes + noVotes;
    if (totalVotes === 0) {
      return { yesBalls: "", noBalls: "", total: 0 };
    }

    // Scale votes to maxBalls if total exceeds it
    let yesCount = yesVotes;
    let noCount = noVotes;
    if (totalVotes > maxBalls) {
      yesCount = Math.round((yesVotes / totalVotes) * maxBalls);
      noCount = maxBalls - yesCount;
    }

    // Green ball (●) for yes votes, red ball (●) for no votes
    const yesBalls = "●".repeat(yesCount);
    const noBalls = "●".repeat(noCount);

    return { yesBalls, noBalls, total: yesCount + noCount };
  }
</script>

<div class="min-h-screen bg-pe-bg pt-16">
  <div class="flex">
    <!-- Sidebar Filters -->
    <aside
      class="fixed lg:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)] w-72 bg-pe-panel border-r border-pe-border overflow-y-auto transition-transform duration-300 lg:translate-x-0"
      class:-translate-x-full={!sidebarOpen}
      aria-label="Filters sidebar"
    >
      <div class="p-6 space-y-8">
        <!-- Filters Header -->
        <div class="flex items-center gap-2">
          <svg
            class="w-5 h-5 text-pe-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"
            />
          </svg>
          <span class="font-display font-semibold text-pe-text">Filters</span>
        </div>

        <!-- Search Box -->
        <div class="relative">
          <svg
            class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-pe-muted"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search..."
            class="search-input-pe pl-10"
            on:input={handleSearchInput}
            aria-label="Search proposals"
          />
        </div>

        <!-- Categories -->
        <div>
          <h3 class="sidebar-label">Categories</h3>
          <div class="space-y-1">
            {#each availableCategories as category}
              <button
                class="category-item w-full"
                class:active={filters.category === category.key}
                on:click={() => filtersStore.setCategory(category.key)}
                aria-pressed={filters.category === category.key}
              >
                <span>{category.name}</span>
                <span class="text-pe-text-dim text-xs">{category.count}</span>
              </button>
            {/each}
          </div>
        </div>

        <!-- Status Filter -->
        <div>
          <h3 class="sidebar-label">Status</h3>
          <div class="space-y-1">
            <button
              class="category-item w-full"
              class:active={!filters.status || filters.status === "all"}
              on:click={() => filtersStore.setStatus("all")}
              aria-pressed={!filters.status || filters.status === "all"}
            >
              <span>All Status</span>
              <span class="text-pe-text-dim text-xs">{proposals.length}</span>
            </button>
            <button
              class="category-item w-full"
              class:active={filters.status === "active"}
              on:click={() => filtersStore.setStatus("active")}
              aria-pressed={filters.status === "active"}
            >
              <span>Active</span>
              <span class="text-pe-text-dim text-xs"
                >{proposals.filter((p) => (p.status || "active") === "active")
                  .length}</span
              >
            </button>
            <button
              class="category-item w-full"
              class:active={filters.status === "approved"}
              on:click={() => filtersStore.setStatus("approved")}
              aria-pressed={filters.status === "approved"}
            >
              <span>Approved</span>
              <span class="text-pe-text-dim text-xs"
                >{proposals.filter((p) => (p.status || "active") === "approved")
                  .length}</span
              >
            </button>
            <button
              class="category-item w-full"
              class:active={filters.status === "rejected"}
              on:click={() => filtersStore.setStatus("rejected")}
              aria-pressed={filters.status === "rejected"}
            >
              <span>Rejected</span>
              <span class="text-pe-text-dim text-xs"
                >{proposals.filter((p) => (p.status || "active") === "rejected")
                  .length}</span
              >
            </button>
          </div>
        </div>

        <!-- Confidence Range -->
        <div>
          <h3 class="sidebar-label">Confidence</h3>

          <!-- Histogram Bars -->
          <div class="flex items-end gap-0.5 h-12 mb-2">
            {#each confidenceHistogram as bar}
              {@const isInRange =
                bar.min >= filters.confidenceMin &&
                bar.max <= filters.confidenceMax}
              <div
                class="histogram-bar flex-1"
                class:active={isInRange}
                style="height: {(bar.count / maxHistogramCount) * 100}%"
                title="{bar.count} items between {bar.min}-{bar.max}%"
              ></div>
            {/each}
          </div>

          <!-- Confidence Axis -->
          <div class="flex justify-between text-xs text-pe-text-dim mb-4 px-0.5">
            <span>0</span>
            <span>25</span>
            <span>50</span>
            <span>75</span>
            <span>100</span>
          </div>

          <!-- Confidence Range Slider -->
          <div class="relative h-6 mb-4">
            <input
              type="range"
              min="0"
              max="100"
              bind:value={filters.confidenceMin}
              on:change={() =>
                filtersStore.setConfidenceRange(
                  filters.confidenceMin,
                  filters.confidenceMax,
                )}
              class="absolute w-full h-1 pointer-events-none"
              style="z-index: 2;"
              aria-label="Minimum confidence"
            />
            <input
              type="range"
              min="0"
              max="100"
              bind:value={filters.confidenceMax}
              on:change={() =>
                filtersStore.setConfidenceRange(
                  filters.confidenceMin,
                  filters.confidenceMax,
                )}
              class="absolute w-full h-1 pointer-events-none"
              style="z-index: 2;"
              aria-label="Maximum confidence"
            />
          </div>

          <!-- Confidence Inputs -->
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1">
              <input
                type="number"
                class="price-input"
                bind:value={filters.confidenceMin}
                on:change={() =>
                  filtersStore.setConfidenceRange(
                    filters.confidenceMin,
                    filters.confidenceMax,
                  )}
                min="0"
                max={filters.confidenceMax}
                aria-label="Minimum confidence input"
              />
              <span class="text-pe-muted text-sm">%</span>
            </div>
            <span class="text-pe-muted">-</span>
            <div class="flex items-center gap-1">
              <input
                type="number"
                class="price-input"
                bind:value={filters.confidenceMax}
                on:change={() =>
                  filtersStore.setConfidenceRange(
                    filters.confidenceMin,
                    filters.confidenceMax,
                  )}
                min={filters.confidenceMin}
                max="100"
                aria-label="Maximum confidence input"
              />
              <span class="text-pe-muted text-sm">%</span>
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div>
          <h3 class="sidebar-label">Tags</h3>
          <div class="flex flex-wrap gap-2">
            {#each availableTags as tag}
              <button
                class="chip-pe"
                class:active={filters.tags.includes(tag)}
                on:click={() => filtersStore.toggleTag(tag)}
                aria-pressed={filters.tags.includes(tag)}
              >
                {tag}
              </button>
            {/each}
          </div>
        </div>
      </div>
    </aside>

    <!-- Sidebar Overlay (Mobile) -->
    {#if sidebarOpen}
      <button
        class="fixed inset-0 bg-black/50 z-30 lg:hidden"
        on:click={toggleSidebar}
        aria-label="Close sidebar"
      ></button>
    {/if}

    <!-- Main Content -->
    <main class="flex-1 min-h-screen lg:ml-0">
      <div
        bind:this={mainContentElement}
        class="p-6 lg:p-8 relative overflow-hidden"
      >
        <!-- Floating Vote Balls Background -->
        <div
          class="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-30"
        >
          <FloatingNetwork
            width={contentWidth}
            height={contentHeight}
            yesVotes={12}
            noVotes={8}
            className="w-full h-full"
          />
        </div>
        <!-- Header -->
        <div class="mb-8 relative z-10">
          <!-- Mobile sidebar toggle -->
          <button
            class="lg:hidden mb-4 p-2 rounded-pe bg-pe-card border border-pe-border hover:bg-pe-card-hover transition-colors"
            on:click={toggleSidebar}
            aria-label="Toggle filters"
          >
            <svg
              class="w-5 h-5 text-pe-muted"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"
              />
            </svg>
          </button>

          <h1 class="font-display text-4xl font-bold text-pe-text mb-2">
            {filters.category === "all"
              ? "Investment Proposals"
              : filters.category}
          </h1>

          <div class="mt-4 relative z-10">
            <div class="card-pe p-4 border border-pe-border">
              <div
                class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3"
              >
                <div>
                  <h3 class="font-display text-lg text-pe-text">
                    Initiate new search
                  </h3>
                  <p class="text-pe-muted text-sm">
                    Choose sources and pull fresh proposals. Existing proposals will
                    be cleared.
                  </p>
                </div>
                <button
                  class="btn-accent-pe px-4 py-2 disabled:opacity-60"
                  on:click={initiateSearch}
                  disabled={searching}
                >
                  {searching ? "Searching..." : "Initiate search"}
                </button>
              </div>

              <div class="grid gap-4 mt-4 md:grid-cols-2">
                <div class="space-y-2">
                  <label class="sidebar-label">Sources</label>
                  <div class="flex flex-wrap gap-3">
                    <label class="flex items-center gap-2 text-sm text-pe-text">
                      <input
                        type="checkbox"
                        value="producthunt"
                        bind:group={searchSources}
                        class="h-4 w-4 rounded border-pe-border text-pe-accent"
                        aria-label="Use Product Hunt"
                      />
                      Product Hunt
                    </label>
                    <label class="flex items-center gap-2 text-sm text-pe-text">
                      <input
                        type="checkbox"
                        value="ycombinator"
                        bind:group={searchSources}
                        class="h-4 w-4 rounded border-pe-border text-pe-accent"
                        aria-label="Use Y Combinator"
                      />
                      Y Combinator
                    </label>
                  </div>
                  <p class="text-xs text-pe-muted">
                    Select where the agent should search for startups.
                  </p>
                </div>

                <div class="space-y-2">
                  <label class="sidebar-label">Number of proposals per source</label>
                  <input
                    type="number"
                    class="price-input w-full"
                    bind:value={proposalLimit}
                    min="1"
                    max="50"
                    aria-label="Number of proposals to fetch"
                  />
                  <p class="text-xs text-pe-muted">Between 1 and 50 per source.</p>
                </div>
              </div>

              <div class="mt-4 space-y-2">
                <label class="sidebar-label">Additional startup fields</label>
                <textarea
                  class="search-input-pe w-full min-h-[80px]"
                  placeholder="e.g. sector=AI; stage=Seed; geography=US"
                  bind:value={additionalFields}
                  aria-label="Additional startup fields"
                ></textarea>
                <p class="text-xs text-pe-muted">
                  Optional hints the agentic pipeline can use when pulling proposals.
                </p>
              </div>

              {#if searchError}
                <p class="text-red-500 text-sm mt-3">{searchError}</p>
              {:else if searchStatus}
                <p class="text-pe-muted text-sm mt-3">{searchStatus}</p>
              {/if}
            </div>
          </div>

          <!-- Active Filters -->
          {#if activeFiltersList.length > 0}
            <div class="flex flex-wrap items-center gap-2 mt-4">
              {#each activeFiltersList as filter}
                <div class="chip-filter">
                  <span>{filter.label}</span>
                  <button
                    on:click={() => removeFilter(filter)}
                    aria-label="Remove filter: {filter.label}"
                    class="hover:text-pe-accent"
                  >
                    <svg
                      class="w-3.5 h-3.5"
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
                  </button>
                </div>
              {/each}
            </div>
          {/if}

          <!-- Sorting -->
          <div class="flex items-center justify-end gap-4 mt-4">
            <button
              class="flex items-center gap-2 text-sm text-pe-muted hover:text-pe-text transition-colors"
              on:click={() =>
                filtersStore.setSortBy(
                  filters.sortBy === "confidence-asc"
                    ? "confidence-desc"
                    : "confidence-asc",
                )}
            >
              Confidence
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                />
              </svg>
            </button>
            <button
              class="flex items-center gap-2 text-sm text-pe-muted hover:text-pe-text transition-colors"
              on:click={() => filtersStore.setSortBy("name")}
            >
              Name
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                />
              </svg>
            </button>
            <button
              class="flex items-center gap-2 text-sm text-pe-muted hover:text-pe-text transition-colors"
              on:click={() => filtersStore.setSortBy("status")}
            >
              Status
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Loading State -->
        {#if loading}
          <div class="flex flex-col justify-center items-center py-20">
            <div
              class="w-12 h-12 border-3 border-pe-accent/30 border-t-pe-accent rounded-full animate-spin"
            ></div>
            <p class="text-pe-muted mt-4">Loading proposals...</p>
          </div>
        {:else if products.length === 0}
          <!-- Empty State -->
          <div class="text-center py-20 relative z-10">
            <svg
              class="w-24 h-24 mx-auto text-pe-muted/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 class="text-xl font-display font-semibold text-pe-text mt-4">
              {#if proposals.length === 0}
                No proposals in database
              {:else}
                No proposals found
              {/if}
            </h3>
            <p class="text-pe-muted mt-2">
              {#if proposals.length === 0}
                The database is empty. Proposals will appear here once they are
                created.
              {:else}
                Try adjusting your filters to see more proposals.
              {/if}
            </p>
            {#if proposals.length > 0}
              <button
                class="mt-4 btn-accent-pe"
                on:click={() => filtersStore.clearAll()}
              >
                Clear all filters
              </button>
            {/if}
            {#if error}
              <div
                class="mt-4 p-4 rounded-pe-lg bg-red-500/10 border border-red-500/20"
              >
                <p class="text-red-400 text-sm">{error}</p>
              </div>
            {/if}
          </div>
        {:else}
          <!-- Product Grid -->
          <div
            class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 relative z-10"
          >
            {#each products as product, index (product.id)}
              <article
                class="card-pe group cursor-pointer {getStaggerClass(index)}"
                class:card-featured={product.featured}
                on:click={() => selectProposal(product.id)}
                on:keydown={(e) =>
                  e.key === "Enter" && selectProposal(product.id)}
                role="button"
                tabindex="0"
                aria-label="View {product.title} details"
              >
                <!-- Product Image -->
                <div
                  class="relative aspect-square p-6 bg-gradient-to-b from-transparent to-black/10 rounded-t-pe-lg overflow-hidden"
                >
                  <img
                    src={product.image}
                    alt={product.title}
                    class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                    style="filter: drop-shadow(0 12px 24px rgba(0,0,0,0.4));"
                    on:error={(e) => handleImageError(e, product)}
                  />

                  <!-- Action Buttons -->
                  <div class="absolute top-4 right-4 flex gap-2 z-10">
                    <!-- Heart/Favorite Button -->
                    <button
                      type="button"
                      class="heart-btn focus-ring"
                      on:click={(e) => toggleFavorite(product.id, e)}
                      on:mousedown|stopPropagation
                      aria-pressed={product.favorite}
                      aria-label={product.favorite
                        ? "Remove from favorites"
                        : "Add to favorites"}
                    >
                      <svg
                        class="w-5 h-5 transition-colors"
                        class:text-red-500={product.favorite}
                        class:fill-red-500={product.favorite}
                        class:text-white={!product.favorite}
                        fill={product.favorite ? "currentColor" : "none"}
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        stroke-width="1.5"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
                        />
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- Product Info -->
                <div class="p-5">
                  <div class="flex justify-between items-start gap-4">
                    <div class="min-w-0 flex-1">
                      <h3
                        class="font-display font-semibold text-pe-text truncate"
                      >
                        {product.title}
                      </h3>
                      <p class="text-sm text-pe-muted mt-0.5 truncate">
                        {product.subtitle}
                      </p>
                    </div>
                    <span
                      class={"px-3 py-1 rounded-pe border text-xs font-semibold uppercase tracking-wide " +
                        getStatusBadgeClasses(product.status)}
                    >
                      {product.status}
                    </span>
                  </div>

                  <!-- Confidence Score (for proposals) -->
                  {#if product.confidence}
                    <div class="mt-3 flex items-center gap-2">
                      <div
                        class="flex-1 h-1.5 bg-pe-chip-bg rounded-full overflow-hidden"
                      >
                        <div
                          class="h-full rounded-full transition-all duration-500"
                          class:bg-pe-accent={product.confidence >= 80}
                          class:bg-yellow-500={product.confidence >= 60 &&
                            product.confidence < 80}
                          class:bg-red-500={product.confidence < 60}
                          style="width: {product.confidence}%"
                        ></div>
                      </div>
                      <span class="text-xs text-pe-muted"
                        >{product.confidence}%</span
                      >
                    </div>
                  {/if}

                  <!-- Vote Bar -->
                  {#if true}
                  {@const yesVotes = product.yes_votes || 0}
                  {@const noVotes = product.no_votes || 0}
                  {@const totalVotes = yesVotes + noVotes}
                  {@const yesPercentage =
                    totalVotes > 0 ? (yesVotes / totalVotes) * 100 : 50}
                  {@const noPercentage =
                    totalVotes > 0 ? (noVotes / totalVotes) * 100 : 50}
                  {@const isEqual = yesVotes === noVotes && totalVotes > 0}

                  <div class="mt-3">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-xs text-pe-muted">Votes</span>
                      <span class="text-xs text-pe-muted">
                        {yesVotes} Yes / {noVotes} No
                      </span>
                    </div>
                    <div
                      class="relative h-2 bg-pe-chip-bg rounded-full overflow-hidden"
                    >
                      {#if isEqual}
                        <!-- Equal votes: green on left, red on right, white line in center -->
                        <div class="absolute inset-0 flex">
                          <div class="flex-1 bg-pe-accent"></div>
                          <div class="w-0.5 bg-white"></div>
                          <div class="flex-1 bg-red-500"></div>\
                        </div>
                        {:else if totalVotes > 0}
                          <!-- Unequal votes: proportional bars -->
                          <div class="absolute inset-0 flex">
                            <div
                              class="bg-pe-accent transition-all duration-500"
                              style="width: {yesPercentage}%"
                            ></div>
                            <div
                              class="bg-red-500 transition-all duration-500"
                              style="width: {noPercentage}%"
                            ></div>
                          </div>
                        {:else}
                          <!-- No votes: neutral gray -->
                          <div class="absolute inset-0 bg-pe-muted/20"></div>
                        {/if}
                      </div>
                    </div>
                  {/if}
                </div>
              </article>
            {/each}
          </div>
        {/if}
      </div>
    </main>
  </div>
</div>

<style>
  /* Custom scrollbar for sidebar */
  aside::-webkit-scrollbar {
    width: 6px;
  }

  aside::-webkit-scrollbar-track {
    background: transparent;
  }

  aside::-webkit-scrollbar-thumb {
    background: var(--pe-chip-border);
    border-radius: 3px;
  }

  aside::-webkit-scrollbar-thumb:hover {
    background: var(--pe-muted);
  }

  /* Featured card rotation */
  .card-featured {
    transform: rotate(-6deg);
    z-index: 10;
  }

  .card-featured:hover {
    transform: rotate(-2deg) translateY(-6px);
  }

  /* Range slider styling for dual slider */
  input[type="range"] {
    pointer-events: auto;
  }

  /* Spinner animation */
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>
