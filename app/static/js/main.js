document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const tickerInput = document.getElementById('ticker');
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'suggestions';
    tickerInput.parentNode.appendChild(suggestionsDiv);
    
    let debounceTimeout;
    let selectedSymbol = '';  // Store the selected symbol

    function formatCompanyName(name) {
        return name.replace(/\\'/g, "'");
    }
    
    // Clear input on double click
    tickerInput.addEventListener('dblclick', function() {
        if (this.value) {
            this.value = '';
            selectedSymbol = '';
            suggestionsDiv.style.display = 'none';
        }
    });
    tickerInput.addEventListener('input', function() {
        clearTimeout(debounceTimeout);
        const query = this.value.trim();
        selectedSymbol = '';  // Clear selected symbol on new input
        
        if (query.length < 1) {
            suggestionsDiv.style.display = 'none';
            return;
        }
        
        debounceTimeout = setTimeout(() => {
            fetch(`/search_ticker?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    suggestionsDiv.innerHTML = '';
                    
                    if (data.length > 0) {
                        data.forEach(item => {
                            const div = document.createElement('div');
                            div.className = 'suggestion-item';
                            const formattedName = formatCompanyName(item.name);
                            
                            // Show the exchange symbol instead of just the base symbol
                            div.innerHTML = `
                                <span class="symbol">${item.exchange_symbol}</span>
                                <span class="name">${formattedName}</span>
                            `;
                            
                            div.addEventListener('click', function() {
                                selectedSymbol = item.exchange_symbol;  // Store the exchange symbol
                                tickerInput.value = `${item.exchange_symbol}    ${formattedName}`;
                                suggestionsDiv.style.display = 'none';
                            });
                            suggestionsDiv.appendChild(div);
                        });
                        suggestionsDiv.style.display = 'block';
                    } else {
                        suggestionsDiv.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    suggestionsDiv.style.display = 'none';
                });
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
    
    form.addEventListener('submit', function(e) {
        const ticker = selectedSymbol || tickerInput.value.trim().split(/\s+/)[0];
        if (!ticker) {
            e.preventDefault();
            alert('Please enter a stock ticker symbol');
            return;
        }
        
        loadingDiv.style.display = 'block';
        setTimeout(() => {
            loadingDiv.style.display = 'none';
        }, 1000);
    });
});