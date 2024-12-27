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
    
    // Clear input immediately when clicked/focused
    tickerInput.addEventListener('focus', function() {
        if (this.value) {  // Only clear if there's text
            this.value = '';
            suggestionsDiv.style.display = 'none';
        }
    });
    
    tickerInput.addEventListener('input', function() {
        clearTimeout(debounceTimeout);
        const query = this.value.trim();
        
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
    
    // Updated form submit handler with ticker verification
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Prevent default submission initially
        
        const ticker = tickerInput.value.trim().split(/\s+/)[0];
        if (!ticker) {
            alert('Please enter a stock ticker symbol');
            return;
        }
        
        loadingDiv.style.display = 'block';
        
        try {
            // First verify if it's a valid ticker and needs to be added
            const response = await fetch(`/verify_and_add_ticker/${ticker}`);
            const result = await response.json();
            
            if (!result.success) {
                alert(result.message);
                loadingDiv.style.display = 'none';
                return;
            }
            
            // If it's a new ticker that was added, show a notification
            if (!result.exists) {
                alert(result.message);
            }
            
            // If everything is good, submit the form
            form.submit();
            
        } catch (error) {
            console.error('Error:', error);
            alert('Error processing ticker. Please try again.');
            loadingDiv.style.display = 'none';
        }
    });
});