// news.js
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const searchButton = document.getElementById('searchButton');
    const resetButton = document.getElementById('resetButton');
    const fetchButton = document.getElementById('fetchNews');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsCount = document.getElementById('resultsCount');

    // Set default dates if not set
    const endDateInput = document.getElementById('end_date');
    const startDateInput = document.getElementById('start_date');
    
    if (!endDateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        endDateInput.value = today;
    }
    if (!startDateInput.value) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
    }

    // Helper function to show/hide loading state
    function setLoading(isLoading) {
        if (isLoading) {
            loadingIndicator.classList.remove('hidden');
            searchButton.disabled = true;
            fetchButton.disabled = true;
            resetButton.disabled = true;
        } else {
            loadingIndicator.classList.add('hidden');
            searchButton.disabled = false;
            fetchButton.disabled = false;
            resetButton.disabled = false;
        }
    }

    // Helper function to show error message
    function showError(message, duration = 5000) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4';
        errorDiv.role = 'alert';
        errorDiv.innerHTML = `
            <strong class="font-bold">Error!</strong>
            <span class="block sm:inline"> ${message}</span>
            <span class="absolute top-0 bottom-0 right-0 px-4 py-3">
                <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                    <title>Close</title>
                    <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/>
                </svg>
            </span>
        `;
        
        // Add click handler to close button
        const closeButton = errorDiv.querySelector('svg');
        closeButton.onclick = () => errorDiv.remove();
        
        // Insert error at the top of search results
        searchResults.insertBefore(errorDiv, searchResults.firstChild);
        
        // Automatically remove after duration
        if (duration) {
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.remove();
                }
            }, duration);
        }
    }

    // Function to render a single article
    function renderArticle(article) {
        return `
            <div class="border-b border-gray-200 pb-6 last:border-b-0">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-medium text-gray-900">
                        <a href="${article.url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                            ${article.title}
                        </a>
                    </h3>
                    <span class="text-sm text-gray-500">${article.published_at}</span>
                </div>

                <div class="mb-3">
                    <p class="text-gray-600">${article.summary?.brief || article.content || ''}</p>
                </div>

                ${article.summary?.key_points ? `
                    <div class="mb-3">
                        <h4 class="text-sm font-semibold text-gray-700">Key Points:</h4>
                        <p class="text-sm text-gray-600">${article.summary.key_points}</p>
                    </div>
                ` : ''}

                ${article.summary?.market_impact ? `
                    <div class="mb-3">
                        <h4 class="text-sm font-semibold text-gray-700">Market Impact:</h4>
                        <p class="text-sm text-gray-600">${article.summary.market_impact}</p>
                    </div>
                ` : ''}

                <div class="flex flex-wrap gap-2">
                    ${(article.symbols || []).map(symbol => `
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            ${symbol}
                        </span>
                    `).join('')}

                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
                        ${article.sentiment?.overall_sentiment === 'POSITIVE' ? 'bg-green-100 text-green-800' :
                          article.sentiment?.overall_sentiment === 'NEGATIVE' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'}">
                        ${article.sentiment?.overall_sentiment || 'NEUTRAL'}
                        ${article.sentiment?.confidence ? 
                            `(${(article.sentiment.confidence * 100).toFixed(1)}%)` : 
                            ''}
                    </span>

                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ${article.source || 'Unknown'}
                    </span>
                </div>
            </div>
        `;
    }

    // Function to perform search
    async function performSearch(formData) {
        try {
            setLoading(true);
            console.log('Performing search with data:', Object.fromEntries(formData));
            
            const searchParams = new URLSearchParams(formData);
            const response = await fetch(`/news/search?${searchParams.toString()}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Search failed with status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Search response:', data);

            // Update results count
            if (resultsCount) {
                resultsCount.textContent = `${data.total} articles found`;
            }

            // Update search results
            if (searchResults) {
                if (data.articles && data.articles.length > 0) {
                    searchResults.innerHTML = data.articles.map(renderArticle).join('');
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
            showError('Failed to perform search. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    // Event Listeners
    if (searchForm) {
        // Handle form submission
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(searchForm);
            await performSearch(formData);
        });

        // Handle reset button
        resetButton.addEventListener('click', async function() {
            searchForm.reset();
            // Set default dates
            const today = new Date();
            endDateInput.value = today.toISOString().split('T')[0];
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
            // Perform empty search
            const formData = new FormData(searchForm);
            await performSearch(formData);
        });

        // Handle fetch news button
        fetchButton.addEventListener('click', async function() {
            try {
                setLoading(true);
                const symbol = document.getElementById('symbol').value;
                
                if (!symbol) {
                    alert('Please enter a stock symbol');
                    return;
                }

                console.log('Fetching news for symbol:', symbol);
                
                const requestData = {
                    symbols: [symbol],
                    limit: 10
                };
                
                console.log('Sending request with data:', requestData);

                const response = await fetch('/news/api/fetch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });

                console.log('Response status:', response.status);
                
                const responseText = await response.text();
                console.log('Response text:', responseText);
                
                if (!response.ok) {
                    throw new Error(`Failed to fetch news: ${response.status} - ${responseText}`);
                }

                let data;
                try {
                    data = JSON.parse(responseText);
                    console.log('Parsed response data:', data);
                } catch (e) {
                    console.error('Failed to parse response:', e);
                    throw new Error('Invalid response format from server');
                }

                if (data.error) {
                    throw new Error(data.error);
                }

                const articleCount = data.articles?.length || 0;
                alert(`Successfully fetched ${articleCount} articles. You can now search for them.`);
                
                // Update the form with the current symbol and dates
                const formData = new FormData(searchForm);
                formData.set('symbol', symbol);  // Set the symbol
                await performSearch(formData);

            } catch (error) {
                console.error('Error fetching news:', error);
                showError(`Failed to fetch news: ${error.message}`);
            } finally {
                setLoading(false);
            }
        });

        // Handle pagination buttons
        document.querySelectorAll('[data-page]').forEach(button => {
            button.addEventListener('click', async () => {
                const page = button.dataset.page;
                const formData = new FormData(searchForm);
                formData.set('page', page);
                await performSearch(formData);
                // Scroll to top of results
                searchResults.scrollIntoView({ behavior: 'smooth' });
            });
        });
    }
});