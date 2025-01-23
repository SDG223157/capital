// Enhanced news.js
// User Preferences Management
const UserPreferences = {
    KEYS: {
        LAST_SEARCH: 'lastSearch',
        VIEW_MODE: 'viewMode',
        SORT_ORDER: 'sortOrder'
    },

    save(key, value) {
        try {
            localStorage.setItem(`news_${key}`, JSON.stringify(value));
        } catch (e) {
            console.warn('Failed to save preference:', e);
        }
    },

    load(key, defaultValue = null) {
        try {
            const value = localStorage.getItem(`news_${key}`);
            return value ? JSON.parse(value) : defaultValue;
        } catch (e) {
            console.warn('Failed to load preference:', e);
            return defaultValue;
        }
    }
};

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function fetchWithRetry(url, options, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            return response;
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
        }
    }
}

// Notification System
class NotificationSystem {
    static show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-x-full
            ${type === 'error' ? 'bg-red-500' : 
              type === 'success' ? 'bg-green-500' : 
              'bg-blue-500'} text-white`;

        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200 focus:outline-none">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(notification);
        requestAnimationFrame(() => notification.classList.remove('translate-x-full'));

        const close = () => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        };

        notification.querySelector('button').addEventListener('click', close);
        if (duration) setTimeout(close, duration);

        return notification;
    }
}

// Main Application Class
class NewsApp {
    constructor() {
        this.initializeElements();
        this.initializeEventListeners();
        this.loadUserPreferences();
        this.setupKeyboardShortcuts();
    }

    initializeElements() {
        this.elements = {
            searchForm: document.getElementById('searchForm'),
            searchResults: document.getElementById('searchResults'),
            searchButton: document.getElementById('searchButton'),
            resetButton: document.getElementById('resetButton'),
            fetchButton: document.getElementById('fetchNews'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            resultsCount: document.getElementById('resultsCount'),
            startDateInput: document.getElementById('start_date'),
            endDateInput: document.getElementById('end_date')
        };

        this.setDefaultDates();
    }

    setDefaultDates() {
        if (!this.elements.endDateInput.value) {
            const today = new Date().toISOString().split('T')[0];
            this.elements.endDateInput.value = today;
        }

        if (!this.elements.startDateInput.value) {
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            this.elements.startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
        }
    }

    initializeEventListeners() {
        // Search form handlers
        this.elements.searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(this.elements.searchForm);
            await this.performSearch(formData);
        });

        // Reset button handler
        this.elements.resetButton.addEventListener('click', () => this.handleReset());

        // Fetch button handler
        this.elements.fetchButton.addEventListener('click', () => this.handleFetch());

        // Real-time search on input changes
        this.initializeRealtimeSearch();

        // Initialize pagination
        this.initializePagination();
    }

    initializeRealtimeSearch() {
        const debouncedSearch = debounce(() => {
            const formData = new FormData(this.elements.searchForm);
            this.performSearch(formData);
        }, 500);

        ['keyword', 'symbol', 'sentiment', 'start_date', 'end_date'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', debouncedSearch);
            }
        });
    }

    async performSearch(formData) {
        try {
            this.setLoading(true);
            this.elements.searchResults.innerHTML = this.renderSkeleton(3);

            const searchParams = new URLSearchParams(formData);
            const response = await fetchWithRetry(`/news/search?${searchParams.toString()}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            const data = await response.json();
            
            // Update results count
            this.elements.resultsCount.textContent = `${data.total} articles found`;

            // Update search results
            if (data.articles?.length) {
                this.elements.searchResults.innerHTML = data.articles
                    .map((article, index) => this.renderArticle(article, index))
                    .join('');
                    
                setTimeout(() => {
                    this.animateArticles();
                    this.setupArticleFeatures();
                }, 100);
            } else {
                this.elements.searchResults.innerHTML = this.renderEmptyState();
            }

            // Update URL
            this.updateUrl(formData);
            
            // Save search state
            UserPreferences.save(UserPreferences.KEYS.LAST_SEARCH, Object.fromEntries(formData));

        } catch (error) {
            console.error('Search error:', error);
            NotificationSystem.show(error.message, 'error');
            this.elements.searchResults.innerHTML = this.renderError(error);
        } finally {
            this.setLoading(false);
        }
    }

    async handleFetch() {
        try {
            const symbol = document.getElementById('symbol').value?.trim();
            
            if (!symbol) {
                NotificationSystem.show('Please enter a stock symbol', 'error');
                return;
            }

            this.setLoading(true);
            NotificationSystem.show('Fetching latest news...', 'info');

            const response = await fetchWithRetry('/news/api/fetch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    symbols: [symbol],
                    limit: 10
                })
            });

            const data = await response.json();
            NotificationSystem.show(
                `Successfully fetched ${data.articles?.length || 0} articles for ${symbol}`, 
                'success'
            );

            // Update search results
            const formData = new FormData(this.elements.searchForm);
            formData.set('symbol', symbol);
            await this.performSearch(formData);

            // Update URL
            this.updateUrl(formData);
        } catch (error) {
            NotificationSystem.show('Failed to fetch news', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    handleReset() {
        this.elements.searchForm.reset();
        this.setDefaultDates();
        const formData = new FormData(this.elements.searchForm);
        this.performSearch(formData);
    }

    setLoading(isLoading) {
        const buttons = [
            this.elements.searchButton,
            this.elements.resetButton,
            this.elements.fetchButton
        ];
        
        buttons.forEach(button => button.disabled = isLoading);
        
        if (isLoading) {
            this.elements.loadingIndicator.classList.remove('hidden');
            this.elements.searchForm.classList.add('opacity-50', 'pointer-events-none');
        } else {
            this.elements.loadingIndicator.classList.add('hidden');
            this.elements.searchForm.classList.remove('opacity-50', 'pointer-events-none');
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('keyword').focus();
            }
            // Ctrl/Cmd + F to fetch news
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                if (!this.elements.fetchButton.disabled) {
                    this.elements.fetchButton.click();
                }
            }
            // Escape to clear search
            if (e.key === 'Escape') {
                this.elements.resetButton.click();
            }
        });
    }

    setupArticleFeatures() {
        // Article expansion
        document.querySelectorAll('.expand-button').forEach(button => {
            button.addEventListener('click', () => {
                const content = button.closest('.article-card').querySelector('.article-content');
                const isExpanded = content.classList.contains('max-h-96');
                
                if (isExpanded) {
                    // Collapse
                    content.classList.remove('max-h-96', 'opacity-100');
                    content.classList.add('max-h-0', 'opacity-0');
                    button.textContent = 'Show More';
                    button.setAttribute('aria-expanded', 'false');
                } else {
                    // Expand
                    content.classList.remove('max-h-0', 'opacity-0');
                    content.classList.add('max-h-96', 'opacity-100');
                    button.textContent = 'Show Less';
                    button.setAttribute('aria-expanded', 'true');
                }
            });
        });

        // Add copy and share buttons
        this.addCopyFeature();
        this.addShareFeature();
    }

    // Rendering Methods
    renderArticle(article, index) {
        const delay = index * 100; // Stagger animation
        return `
            <div class="article-card opacity-0 translate-y-4 border-b border-gray-200 pb-6 last:border-b-0 mb-4 transition-all duration-500 ease-out"
                 data-index="${index}"
                 style="animation-delay: ${delay}ms">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex-1">
                        <div class="flex items-start">
                            <h3 class="text-lg font-medium text-gray-900">
                                <a href="${article.url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                                    ${article.title}
                                </a>
                            </h3>
                            <div class="flex ml-2 space-x-1">
                                <button class="copy-button p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
                                        aria-label="Copy article">
                                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                              d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                                    </svg>
                                </button>
                                <button class="share-button p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
                                        aria-label="Share article">
                                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div class="text-sm text-gray-500 mt-1">
                            ${article.source} · ${this.formatDate(article.published_at)}
                        </div>
                    </div>
                </div>

                <div class="article-content max-h-0 overflow-hidden transition-all duration-500 ease-out">
                    <p class="text-gray-600">
                        ${article.summary?.brief || article.content || ''}
                    </p>

                    ${article.summary?.market_impact ? `
                        <div class="mb-3">
                            <h4 class="text-sm font-semibold text-gray-700">Market Impact:</h4>
                            <p class="text-sm text-gray-600">${article.summary.market_impact}</p>
                        </div>
                    ` : ''}

                    <div class="flex flex-wrap gap-2 mt-3">
                        ${article.symbols.map(symbol => `
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                ${symbol}
                            </span>
                        `).join('')}

                        <span class="sentiment-tag inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                            ${this.getSentimentClasses(article.sentiment?.overall_sentiment)}">
                            ${article.sentiment?.overall_sentiment || 'NEUTRAL'}
                            ${article.sentiment?.confidence ? 
                                `(${(article.sentiment.confidence * 100).toFixed(1)}%)` : 
                                ''}
                        </span>
                    </div>
                </div>
                
                <button class="expand-button mt-2 text-sm text-blue-600 hover:text-blue-800 focus:outline-none"
                        aria-expanded="false">
                    Show More
                </button>
            </div>
        `;
    }

    renderSkeleton(count = 3) {
        return Array(count).fill(0).map(() => `
            <div class="animate-pulse">
                <div class="flex justify-between items-start mb-4">
                    <div class="w-3/4">
                        <div class="h-4 bg-gray-200 rounded w-3/4"></div>
                    </div>
                    <div class="w-1/4">
                        <div class="h-4 bg-gray-200 rounded w-1/2 ml-auto"></div>
                    </div>
                </div>
                <div class="space-y-3">
                    <div class="h-4 bg-gray-200 rounded w-full"></div>
                    <div class="h-4 bg-gray-200 rounded w-5/6"></div>
                </div>
                <div class="flex gap-2 mt-4">
                    <div class="h-6 bg-gray-200 rounded-full w-20"></div>
                    <div class="h-6 bg-gray-200 rounded-full w-20"></div>
                </div>
            </div>
        `).join('<div class="border-b border-gray-200 my-6"></div>');
    }

    renderEmptyState() {
        return `
            <div class="text-center py-12">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01M12 12h.01" />
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No articles found</h3>
                <p class="mt-1 text-sm text-gray-500">Try adjusting your search parameters</p>
                <div class="mt-6">
                    <button type="button" onclick="window.newsApp.handleReset()"
                            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                        Clear Filters
                    </button>
                </div>
            </div>
        `;
    }

    renderError(error) {
        return `
            <div class="bg-red-50 border-l-4 border-red-400 p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" 
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" 
                                  clip-rule="evenodd" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">Error loading articles</h3>
                        <p class="mt-2 text-sm text-red-700">${error.message}</p>
                        <div class="mt-4">
                            <button type="button" onclick="window.location.reload()"
                                    class="text-sm font-medium text-red-800 hover:text-red-900">
                                Retry <span aria-hidden="true">&rarr;</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Helper Methods
    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric'
        }).format(date);
    }

    getSentimentClasses(sentiment) {
        switch (sentiment) {
            case 'POSITIVE':
                return 'bg-green-100 text-green-800';
            case 'NEGATIVE':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    updateUrl(formData) {
        const url = new URL(window.location);
        formData.forEach((value, key) => {
            if (value) {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });
        window.history.pushState({}, '', url);
    }

    animateArticles() {
        const articles = document.querySelectorAll('.article-card');
        articles.forEach(article => {
            article.classList.remove('opacity-0', 'translate-y-4');
        });
    }

    addCopyFeature() {
        document.querySelectorAll('.copy-button').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const article = button.closest('.article-card');
                const title = article.querySelector('h3 a').textContent.trim();
                const content = article.querySelector('.article-content p').textContent.trim();
                const url = article.querySelector('a').href;
                
                try {
                    await navigator.clipboard.writeText(`${title}\n\n${content}\n\nRead more: ${url}`);
                    NotificationSystem.show('Article copied to clipboard', 'success');
                } catch (err) {
                    NotificationSystem.show('Failed to copy article', 'error');
                }
            });
        });
    }

    addShareFeature() {
        document.querySelectorAll('.share-button').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const article = button.closest('.article-card');
                const title = article.querySelector('h3 a').textContent.trim();
                const url = article.querySelector('a').href;

                if (navigator.share) {
                    try {
                        await navigator.share({
                            title: title,
                            url: url
                        });
                        NotificationSystem.show('Article shared successfully', 'success');
                    } catch (err) {
                        if (err.name !== 'AbortError') {
                            NotificationSystem.show('Failed to share article', 'error');
                        }
                    }
                } else {
                    try {
                        await navigator.clipboard.writeText(url);
                        NotificationSystem.show('Article URL copied to clipboard', 'success');
                    } catch (err) {
                        NotificationSystem.show('Failed to copy URL', 'error');
                    }
                }
            });
        });
    }

    loadUserPreferences() {
        // Load last search parameters
        const lastSearch = UserPreferences.load(UserPreferences.KEYS.LAST_SEARCH);
        if (lastSearch) {
            Object.entries(lastSearch).forEach(([key, value]) => {
                const input = document.getElementById(key);
                if (input) input.value = value;
            });
        }
    }

    initializePagination() {
        const paginationContainer = document.querySelector('nav');
        if (paginationContainer) {
            paginationContainer.addEventListener('click', async (e) => {
                const pageButton = e.target.closest('button[data-page]');
                if (pageButton) {
                    const page = pageButton.dataset.page;
                    const formData = new FormData(this.elements.searchForm);
                    formData.set('page', page);
                    await this.performSearch(formData);
                }
            });
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.newsApp = new NewsApp();
});