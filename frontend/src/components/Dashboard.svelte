<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { proposalAPI } from '../lib/api.js';
  import { 
    filtersStore, 
    favoritesStore, 
    filteredProducts, 
    activeFilters,
    categories,
    availableTags,
    confidenceHistogram,
    sampleProducts
  } from '../stores/filters.js';
  
  const dispatch = createEventDispatcher();
  
  let proposals = [];
  let loading = true;
  let error = null;
  let sidebarOpen = true;
  let searchTimeout;
  
  // Subscribe to stores
  $: filters = $filtersStore;
  $: favorites = $favoritesStore;
  $: products = $filteredProducts;
  $: activeFiltersList = $activeFilters;
  
  // Get max histogram count for scaling bars
  $: maxHistogramCount = Math.max(...confidenceHistogram.map(h => h.count));
  
  onMount(async () => {
    await loadProposals();
  });
  
  async function loadProposals() {
    const safetyTimeout = setTimeout(() => {
      if (loading) {
        loading = false;
        // Fall back to sample data if backend unavailable
        proposals = sampleProducts;
      }
    }, 5000);
    
    try {
      loading = true;
      error = null;
      
      // Try to load from API
      if (typeof proposalAPI !== 'undefined' && proposalAPI.getProposals) {
        const fetchedProposals = await proposalAPI.getProposals();
        clearTimeout(safetyTimeout);
        
        if (Array.isArray(fetchedProposals) && fetchedProposals.length > 0) {
          proposals = fetchedProposals;
        } else {
          // Use sample products if no proposals
          proposals = sampleProducts;
        }
      } else {
        // Use sample products
        proposals = sampleProducts;
      }
    } catch (e) {
      clearTimeout(safetyTimeout);
      // Use sample data on error
      proposals = sampleProducts;
    } finally {
      clearTimeout(safetyTimeout);
      loading = false;
    }
  }
  
  function selectProposal(id) {
    dispatch('selectProposal', { id });
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
          <svg class="w-5 h-5 text-pe-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
          </svg>
          <span class="font-display font-semibold text-pe-text">Filters</span>
        </div>
        
        <!-- Search Box -->
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-pe-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
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
            {#each categories as category}
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
        
        <!-- Confidence Range -->
        <div>
          <h3 class="sidebar-label">Confidence</h3>
          
          <!-- Histogram Bars -->
          <div class="flex items-end gap-0.5 h-12 mb-4">
            {#each confidenceHistogram as bar}
              {@const isInRange = bar.min >= filters.confidenceMin && bar.max <= filters.confidenceMax}
              <div 
                class="histogram-bar flex-1"
                class:active={isInRange}
                style="height: {(bar.count / maxHistogramCount) * 100}%"
                title="{bar.count} items between {bar.min}-{bar.max}%"
              ></div>
            {/each}
          </div>
          
          <!-- Confidence Range Slider -->
          <div class="relative h-6 mb-4">
            <input 
              type="range" 
              min="0" 
              max="100" 
              bind:value={filters.confidenceMin}
              on:change={() => filtersStore.setConfidenceRange(filters.confidenceMin, filters.confidenceMax)}
              class="absolute w-full h-1 pointer-events-none"
              style="z-index: 2;"
              aria-label="Minimum confidence"
            />
            <input 
              type="range" 
              min="0" 
              max="100" 
              bind:value={filters.confidenceMax}
              on:change={() => filtersStore.setConfidenceRange(filters.confidenceMin, filters.confidenceMax)}
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
                on:change={() => filtersStore.setConfidenceRange(filters.confidenceMin, filters.confidenceMax)}
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
                on:change={() => filtersStore.setConfidenceRange(filters.confidenceMin, filters.confidenceMax)}
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
      <div class="p-6 lg:p-8">
        <!-- Header -->
        <div class="mb-8">
          <!-- Mobile sidebar toggle -->
          <button 
            class="lg:hidden mb-4 p-2 rounded-pe bg-pe-card border border-pe-border hover:bg-pe-card-hover transition-colors"
            on:click={toggleSidebar}
            aria-label="Toggle filters"
          >
            <svg class="w-5 h-5 text-pe-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
            </svg>
          </button>
          
          <h1 class="font-display text-4xl font-bold text-pe-text mb-2">
            {filters.category === 'all' ? 'Investment Proposals' : filters.category}
          </h1>
          
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
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
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
              on:click={() => filtersStore.setSortBy(filters.sortBy === 'confidence-asc' ? 'confidence-desc' : 'confidence-asc')}
            >
              Default Sorting
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            <button 
              class="flex items-center gap-2 text-sm text-pe-muted hover:text-pe-text transition-colors"
              on:click={() => filtersStore.setSortBy('name')}
            >
              Categories
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Loading State -->
        {#if loading}
          <div class="flex flex-col justify-center items-center py-20">
            <div class="w-12 h-12 border-3 border-pe-accent/30 border-t-pe-accent rounded-full animate-spin"></div>
            <p class="text-pe-muted mt-4">Loading proposals...</p>
          </div>
        {:else if products.length === 0}
          <!-- Empty State -->
          <div class="text-center py-20">
            <svg class="w-24 h-24 mx-auto text-pe-muted/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 class="text-xl font-display font-semibold text-pe-text mt-4">No proposals found</h3>
            <p class="text-pe-muted mt-2">Try adjusting your filters</p>
            <button 
              class="mt-4 btn-accent-pe"
              on:click={() => filtersStore.clearAll()}
            >
              Clear all filters
            </button>
          </div>
        {:else}
          <!-- Product Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {#each products as product, index (product.id)}
              <article 
                class="card-pe group cursor-pointer {getStaggerClass(index)}"
                class:card-featured={product.featured}
                on:click={() => selectProposal(product.id)}
                on:keydown={(e) => e.key === 'Enter' && selectProposal(product.id)}
                role="button"
                tabindex="0"
                aria-label="View {product.title} details"
              >
                <!-- Product Image -->
                <div class="relative aspect-square p-6 bg-gradient-to-b from-transparent to-black/10 rounded-t-pe-lg overflow-hidden">
                  <img 
                    src={product.image}
                    alt={product.title}
                    class="w-full h-full object-contain transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                    style="filter: drop-shadow(0 12px 24px rgba(0,0,0,0.4));"
                  />
                  
                  <!-- Heart/Favorite Button -->
                  <button 
                    class="heart-btn absolute top-4 right-4 focus-ring"
                    on:click={(e) => toggleFavorite(product.id, e)}
                    aria-pressed={product.favorite}
                    aria-label={product.favorite ? 'Remove from favorites' : 'Add to favorites'}
                  >
                    <svg 
                      class="w-5 h-5 transition-colors"
                      class:text-red-500={product.favorite}
                      class:fill-red-500={product.favorite}
                      class:text-white={!product.favorite}
                      fill={product.favorite ? 'currentColor' : 'none'}
                      viewBox="0 0 24 24" 
                      stroke="currentColor" 
                      stroke-width="1.5"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                    </svg>
                  </button>
                </div>
                
                <!-- Product Info -->
                <div class="p-5">
                  <div class="flex justify-between items-start gap-4">
                    <div class="min-w-0 flex-1">
                      <h3 class="font-display font-semibold text-pe-text truncate">
                        {product.title}
                      </h3>
                      <p class="text-sm text-pe-muted mt-0.5 truncate">
                        {product.subtitle}
                      </p>
                    </div>
                  </div>
                  
                  <!-- Confidence Score (for proposals) -->
                  {#if product.confidence}
                    <div class="mt-3 flex items-center gap-2">
                      <div class="flex-1 h-1.5 bg-pe-chip-bg rounded-full overflow-hidden">
                        <div 
                          class="h-full rounded-full transition-all duration-500"
                          class:bg-pe-accent={product.confidence >= 80}
                          class:bg-yellow-500={product.confidence >= 60 && product.confidence < 80}
                          class:bg-red-500={product.confidence < 60}
                          style="width: {product.confidence}%"
                        ></div>
                      </div>
                      <span class="text-xs text-pe-muted">{product.confidence}%</span>
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
    to { transform: rotate(360deg); }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>
