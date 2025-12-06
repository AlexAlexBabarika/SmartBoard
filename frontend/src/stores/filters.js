import { writable, derived } from 'svelte/store';

// Sample product/proposal data with visual catalog info
export const sampleProducts = [
  {
    id: 1,
    title: 'NexGenAI Series A',
    subtitle: 'Enterprise AI automation',
    image: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=400&fit=crop',
    category: 'AI & ML',
    size: 'M',
    tags: ['Modern', 'Air-Purifying'],
    favorite: false,
    featured: false,
    confidence: 85,
    status: 'active'
  },
  {
    id: 2,
    title: 'QuantumLeap Biotech',
    subtitle: 'Drug discovery platform',
    image: 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400&h=400&fit=crop',
    category: 'Healthcare',
    size: 'L',
    tags: ['Luxury', 'Minimalist'],
    favorite: true,
    featured: true,
    confidence: 92,
    status: 'active'
  },
  {
    id: 3,
    title: 'GreenGrid Energy',
    subtitle: 'Renewable solutions',
    image: 'https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=400&h=400&fit=crop',
    category: 'CleanTech',
    size: 'S',
    tags: ['Air-Purifying', 'Modern'],
    favorite: false,
    featured: false,
    confidence: 78,
    status: 'active'
  },
  {
    id: 4,
    title: 'MetaVerse Studios',
    subtitle: 'Digital experiences',
    image: 'https://images.unsplash.com/photo-1633356122102-3fe601e05bd2?w=400&h=400&fit=crop',
    category: 'Web3',
    size: 'M',
    tags: ['Mini', 'Modern'],
    favorite: false,
    featured: false,
    confidence: 65,
    status: 'active'
  },
  {
    id: 5,
    title: 'AgriTech Solutions',
    subtitle: 'Smart farming tech',
    image: 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=400&fit=crop',
    category: 'AgTech',
    size: 'XL',
    tags: ['Indoor', 'Air-Purifying'],
    favorite: false,
    featured: false,
    confidence: 71,
    status: 'approved'
  },
  {
    id: 6,
    title: 'FinTech Dynamics',
    subtitle: 'Payment innovations',
    image: 'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=400&h=400&fit=crop',
    category: 'FinTech',
    size: 'L',
    tags: ['Luxury', 'Minimalist', 'Office'],
    favorite: true,
    featured: false,
    confidence: 88,
    status: 'active'
  }
];

// Categories with counts
export const categories = [
  { name: 'All Proposals', count: 445, key: 'all' },
  { name: 'AI & ML', count: 78, key: 'AI & ML' },
  { name: 'Healthcare', count: 59, key: 'Healthcare' },
  { name: 'CleanTech', count: 64, key: 'CleanTech' },
  { name: 'Web3', count: 127, key: 'Web3' },
  { name: 'FinTech', count: 86, key: 'FinTech' }
];

// Available tags
export const availableTags = [
  'Modern', 'Minimalist', 'Air-Purifying', 'Mini', 'Indoor', 'Luxury', 'Office', 'Exotic'
];

// Available sizes
export const availableSizes = ['S', 'M', 'L', 'XL'];

// Confidence histogram data (for visual representation)
export const confidenceHistogram = [
  { min: 0, max: 10, count: 5 },
  { min: 10, max: 20, count: 8 },
  { min: 20, max: 30, count: 12 },
  { min: 30, max: 40, count: 15 },
  { min: 40, max: 50, count: 18 },
  { min: 50, max: 60, count: 22 },
  { min: 60, max: 70, count: 28 },
  { min: 70, max: 80, count: 35 },
  { min: 80, max: 90, count: 42 },
  { min: 90, max: 100, count: 38 }
];

// Create the filters store
function createFiltersStore() {
  const initialState = {
    searchQuery: '',
    category: 'all',
    status: 'all',
    confidenceMin: 0,
    confidenceMax: 100,
    sizes: [], // Default selected size
    tags: [], // Default selected tags
    sortBy: 'default', // 'default', 'confidence-asc', 'confidence-desc', 'name', 'status'
  };

  const { subscribe, set, update } = writable(initialState);

  return {
    subscribe,
    setSearch: (query) => update(state => ({ ...state, searchQuery: query })),
    setCategory: (category) => update(state => ({ ...state, category })),
    setStatus: (status) => update(state => ({ ...state, status })),
    setConfidenceRange: (min, max) => update(state => ({ ...state, confidenceMin: min, confidenceMax: max })),
    toggleSize: (size) => update(state => {
      const sizes = state.sizes.includes(size)
        ? state.sizes.filter(s => s !== size)
        : [...state.sizes, size];
      return { ...state, sizes };
    }),
    toggleTag: (tag) => update(state => {
      const tags = state.tags.includes(tag)
        ? state.tags.filter(t => t !== tag)
        : [...state.tags, tag];
      return { ...state, tags };
    }),
    removeFilter: (type, value) => update(state => {
      if (type === 'confidence') {
        return { ...state, confidenceMin: 0, confidenceMax: 100 };
      } else if (type === 'status') {
        return { ...state, status: 'all' };
      } else if (type === 'size') {
        return { ...state, sizes: state.sizes.filter(s => s !== value) };
      } else if (type === 'tag') {
        return { ...state, tags: state.tags.filter(t => t !== value) };
      } else if (type === 'category') {
        return { ...state, category: 'all' };
      }
      return state;
    }),
    clearAll: () => set({ ...initialState, sizes: [], tags: [] }),
    setSortBy: (sortBy) => update(state => ({ ...state, sortBy })),
    reset: () => set(initialState)
  };
}

export const filtersStore = createFiltersStore();

// Favorites store
function createFavoritesStore() {
  const { subscribe, update } = writable(new Set([2, 6])); // IDs 2 and 6 are favorited by default

  return {
    subscribe,
    toggle: (id) => update(favorites => {
      const newFavorites = new Set(favorites);
      if (newFavorites.has(id)) {
        newFavorites.delete(id);
      } else {
        newFavorites.add(id);
      }
      return newFavorites;
    }),
    isFavorite: (id, favorites) => favorites.has(id)
  };
}

export const favoritesStore = createFavoritesStore();

// Derived store for filtered products
export const filteredProducts = derived(
  [filtersStore, favoritesStore],
  ([$filters, $favorites]) => {
    let products = [...sampleProducts];
    
    // Apply search filter
    if ($filters.searchQuery) {
      const query = $filters.searchQuery.toLowerCase();
      products = products.filter(p => 
        p.title.toLowerCase().includes(query) || 
        p.subtitle.toLowerCase().includes(query)
      );
    }
    
    // Apply category filter
    if ($filters.category !== 'all') {
      products = products.filter(p => p.category === $filters.category);
    }
    
    // Apply confidence range filter
    products = products.filter(p => 
      p.confidence >= $filters.confidenceMin && p.confidence <= $filters.confidenceMax
    );
    
    // Apply size filter (if any sizes selected)
    if ($filters.sizes.length > 0) {
      products = products.filter(p => $filters.sizes.includes(p.size));
    }
    
    // Apply tag filter (if any tags selected, product must have at least one matching tag)
    if ($filters.tags.length > 0) {
      products = products.filter(p => 
        p.tags.some(tag => $filters.tags.includes(tag))
      );
    }
    
    // Apply sorting
    switch ($filters.sortBy) {
      case 'confidence-asc':
        products.sort((a, b) => a.confidence - b.confidence);
        break;
      case 'confidence-desc':
        products.sort((a, b) => b.confidence - a.confidence);
        break;
      case 'name':
        products.sort((a, b) => a.title.localeCompare(b.title));
        break;
      default:
        // Keep original order
        break;
    }
    
    // Add favorite status from favorites store
    products = products.map(p => ({
      ...p,
      favorite: $favorites.has(p.id)
    }));
    
    return products;
  }
);

// Active filters for display
export const activeFilters = derived(filtersStore, ($filters) => {
  const filters = [];
  
  if ($filters.confidenceMin > 0 || $filters.confidenceMax < 100) {
    filters.push({ 
      type: 'confidence', 
      label: `Confidence: ${$filters.confidenceMin} - ${$filters.confidenceMax}`,
      value: 'confidence'
    });
  }
  
  if ($filters.status && $filters.status !== 'all') {
    filters.push({ 
      type: 'status', 
      label: `Status: ${$filters.status}`,
      value: 'status'
    });
  }
  
  $filters.sizes.forEach(size => {
    filters.push({ type: 'size', label: `Size: ${size}`, value: size });
  });
  
  $filters.tags.forEach(tag => {
    filters.push({ type: 'tag', label: tag, value: tag });
  });
  
  if ($filters.category !== 'all') {
    filters.push({ type: 'category', label: $filters.category, value: $filters.category });
  }
  
  return filters;
});

