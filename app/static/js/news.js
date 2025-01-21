document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const searchButton = document.getElementById('searchButton');
    const resetButton = document.getElementById('resetButton');
    const fetchButton = document.getElementById('fetchNews');
    
    // Function to update loading state
    function setLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.originalText = button.textContent;
            button.textContent = 'Loading...';
        } else {
            button.disabled = false;
            button.textContent = button.originalText || 'Search';
        }
    }

    // Function to perform search
    async function performSearch(formData) {
        try {
            setLoading(searchButton, true);
            
            const searchParams = new URLSearchParams(formData);
            const response = await fetch(`${searchForm.action}?${searchParams.toString()}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Update results count
            const resultsCount = document.querySelector('.text-gray-600');
            if (resultsCount) {
                resultsCount.textContent = `${data.total} articles found`;
            }

            // Update search results
            if (searchResults) {
                if (data.articles && data.articles.length > 0) {
                    renderSearchResults(data.articles);
                } else {
                    searchResults.innerHTML = `
                        <div class="text-center py-8">
                            <p class="text-gray-500">No articles found matching your search criteria</p>
                        </div>
                    `;
                }
            }

            // Update URL without page reload
            const url = new URL(window.location);
            formData.forEach((value, key) => {
                if (value) {
                    url.searchParams.set(key, value);
                } else {
                    url.searchParams.delete(key);
                }
            });
            window.history.pushState({}, '', url);

        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = `
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                    <strong class="font-bold">Error!</strong>
                    <span class="block sm:inline"> Failed to perform search. Please try again.</span>
                </div>
            `;
        } finally {
            setLoading(searchButton, false);
        }
    }

    // Function to render search results
    function renderSearchResults(articles) {
        searchResults.innerHTML = articles.map(article => `
            <div class="border-b border-gray-200 pb-4 last:border-b-0 mb-4">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-medium">
                        <a href="${article.url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                            ${article.title}
                        </a>
                    </h3>
                    <span class="text-sm text-gray-500">${article.published_at}</span>
                </div>
                
                <div class="mb-2">
                    <p class="text-gray-600">${article.summary?.brief || article.content}</p>
                </div>

                ${article.summary?.key_points ? `
                    <div class="mb-2">
                        <h4 class="text-sm font-semibold text-gray-700">Key Points:</h4>
                        <p class="text-sm text-gray-600">${article.summary.key_points}</p>
                    </div>
                ` : ''}

                ${article.summary?.market_impact ? `
                    <div class="mb-2">
                        <h4 class="text-sm font-semibold text-gray-700">Market Impact:</h4>
                        <p class="text-sm text-gray-600">${article.summary.market_impact}</p>
                    </div>
                ` : ''}

                <div class="flex flex-wrap gap-2">
                    ${article.symbols.map(symbol => `
                        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">${symbol}</span>
                    `).join('')}
                    
                    <span class="bg-${article.sentiment?.overall_sentiment?.toLowerCase()}-100 
                               text-${article.sentiment?.overall_sentiment?.toLowerCase()}-700 
                               px-2 py-1 rounded text-sm">
                        ${article.sentiment?.overall_sentiment || 'NEUTRAL'}
                        ${article.sentiment?.confidence ? `(${(article.sentiment.confidence * 100).toFixed(1)}%)` : ''}
                    </span>
                    
                    <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
                        ${article.source}
                    </span>
                </div>
            </div>
        `).join('');
    }

    // Search form submit handler
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(searchForm);
            await performSearch(formData);
        });
    }

    // Reset button handler
    if (resetButton) {
        resetButton.addEventListener('click', async function() {
            searchForm.reset();
            const formData = new FormData(searchForm);
            await performSearch(formData);
        });
    }

    // Fetch news button handler
    if (fetchButton) {
        fetchButton.addEventListener('click', async function() {
            try {
                setLoading(fetchButton, true);
                const symbol = document.getElementById('symbol').value;
                
                if (!symbol) {
                    alert('Please enter a stock symbol');
                    return;
                }

                const response = await fetch('/news/api/fetch', {
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
                
                if (data.error) {
                    throw new Error(data.error);
                }

                alert(`Successfully fetched ${data.articles?.length || 0} articles. You can now search for them.`);
                
                // Perform search with current form data
                const formData = new FormData(searchForm);
                await performSearch(formData);

            } catch (error) {
                console.error('Error fetching news:', error);
                alert('Failed to fetch news: ' + error.message);
            } finally {
                setLoading(fetchButton, false);
            }
        });
    }
});