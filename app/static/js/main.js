document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const tickerInput = document.getElementById('ticker');
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'suggestions';
    tickerInput.parentNode.appendChild(suggestionsDiv);
    
    let debounceTimeout;

    function formatCompanyName(name) {
        return name.replace(/\\'/g, "'");
    }
    
    // Clear input on double click
    tickerInput.addEventListener('dblclick', function() {
        if (this.value) {
            this.value = '';
            suggestionsDiv.style.display = 'none';
        }
    });
    
    tickerInput.addEventListener('input', async function() {
        clearTimeout(debounceTimeout);
        const query = this.value.trim();
        
        if (query.length < 1) {
            suggestionsDiv.style.display = 'none';
            return;
        }
        
        debounceTimeout = setTimeout(async () => {
            // First search in local tickers
            const response = await fetch(`/search_ticker?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.length > 0) {
                // Show suggestions from local tickers
                suggestionsDiv.innerHTML = '';
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    const formattedName = formatCompanyName(item.name);
                    
                    div.innerHTML = `
                        <span class="symbol">${item.symbol}</span>
                        <span class="name">${formattedName}</span>
                    `;
                    
                    div.addEventListener('click', function() {
                        tickerInput.value = `${item.symbol}                    ${formattedName}`;
                        suggestionsDiv.style.display = 'none';
                    });
                    suggestionsDiv.appendChild(div);
                });
                suggestionsDiv.style.display = 'block';
            } else {
                // If not found in local tickers, verify with yfinance
                const verifyResponse = await fetch(`/verify_and_add_ticker/${query}`);
                const verifyResult = await verifyResponse.json();
                
                if (verifyResult.success) {
                    // Valid ticker found - update input with spacing
                    tickerInput.value = `${verifyResult.symbol}                    ${verifyResult.name}`;
                    suggestionsDiv.style.display = 'none';
                } else {
                    // Only show invalid alert if user has typed a complete ticker
                    if (query.length >= 1) {
                        suggestionsDiv.style.display = 'none';
                    }
                }
            }
        }, 300);
    });
    
    document.addEventListener('click', function(e) {
        if (!tickerInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = 'Analyzing data, please wait...';
    form.appendChild(loadingDiv);
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const ticker = tickerInput.value.trim().split(/\s+/)[0];
        if (!ticker) {
            alert('Please enter a stock ticker symbol');
            return;
        }
        
        loadingDiv.style.display = 'block';
        
        try {
            // Submit form
            form.submit();
            
        } catch (error) {
            loadingDiv.style.display = 'none';
            console.error('Error:', error);
            alert('Error processing request');
        }
    });
});