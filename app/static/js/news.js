document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');

    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(searchForm);
            const searchParams = new URLSearchParams(formData);
            
            try {
                const response = await fetch(`${searchForm.action}?${searchParams.toString()}`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Update the results count
                const resultsCount = document.querySelector('.results-count');
                if (resultsCount) {
                    resultsCount.textContent = `${data.total} articles found`;
                }
                
                // Update the results container
                if (searchResults && data.articles) {
                    renderSearchResults(data.articles);
                }
                
                // Update URL with search parameters without reloading
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
                console.error('Error:', error);
                alert('An error occurred while searching. Please try again.');
            }
        });
    }

    // Reset button handler
    const resetButton = searchForm.querySelector('button[type="reset"]');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            // Clear all form fields
            searchForm.reset();
            // Optionally trigger a new search with empty parameters
            searchForm.dispatchEvent(new Event('submit'));
        });
    }
});

function renderSearchResults(articles) {
    const searchResults = document.getElementById('searchResults');
    if (!searchResults) return;

    searchResults.innerHTML = articles.map(article => `
        <div class="border-b border-gray-200 pb-4 last:border-b-0">
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-lg font-medium">
                    <a href="${article.url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                        ${article.title}
                    </a>
                </h3>
                <span class="text-sm text-gray-500">${article.published_at}</span>
            </div>
            
            <div class="mb-2">
                <p class="text-gray-600">${article.summary.brief}</p>
            </div>

            ${article.summary.key_points ? `
                <div class="mb-2">
                    <h4 class="text-sm font-semibold text-gray-700">Key Points:</h4>
                    <p class="text-sm text-gray-600">${article.summary.key_points}</p>
                </div>
            ` : ''}

            ${article.summary.market_impact ? `
                <div class="mb-2">
                    <h4 class="text-sm font-semibold text-gray-700">Market Impact:</h4>
                    <p class="text-sm text-gray-600">${article.summary.market_impact}</p>
                </div>
            ` : ''}

            <div class="flex flex-wrap gap-2">
                ${article.symbols.map(symbol => `
                    <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">${symbol}</span>
                `).join('')}
                
                <span class="bg-${article.sentiment.overall_sentiment.toLowerCase()}-100 
                           text-${article.sentiment.overall_sentiment.toLowerCase()}-700 
                           px-2 py-1 rounded text-sm">
                    ${article.sentiment.overall_sentiment}
                    (${(article.sentiment.confidence * 100).toFixed(1)}%)
                </span>
                
                <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
                    ${article.source}
                </span>
            </div>
        </div>
    `).join('');
}