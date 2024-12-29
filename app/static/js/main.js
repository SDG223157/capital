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
                        // Filter out results where symbol equals name
                        const filteredData = data.filter(item => 
                            item.symbol.toUpperCase() !== item.name.toUpperCase()
                        );
                        
                        if (filteredData.length > 0) {
                            filteredData.forEach(item => {
                                const div = document.createElement('div');
                                div.className = 'suggestion-item';
                                const formattedName = formatCompanyName(item.name);
                                
                                // Create separate spans for symbol and name
                                const symbolSpan = document.createElement('span');
                                symbolSpan.className = 'symbol';
                                symbolSpan.textContent = item.symbol;
                                
                                const nameSpan = document.createElement('span');
                                nameSpan.className = 'name';
                                nameSpan.textContent = formattedName;
                                
                                div.appendChild(symbolSpan);
                                div.appendChild(nameSpan);
                                
                                div.addEventListener('click', function() {
                                    // Set input value to both symbol and name
                                    tickerInput.value = `${item.symbol}    ${formattedName}`;
                                    suggestionsDiv.style.display = 'none';
                                });
                                
                                suggestionsDiv.appendChild(div);
                            });
                            suggestionsDiv.style.display = 'block';
                        } else {
                            suggestionsDiv.style.display = 'none';
                        }
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
    
    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!tickerInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });

    // Prevent suggestions from closing when clicking inside the input
    tickerInput.addEventListener('click', function(e) {
        e.stopPropagation();
        if (this.value.trim().length > 0) {
            suggestionsDiv.style.display = 'block';
        }
    });
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = 'Analyzing data, please wait...';
    form.appendChild(loadingDiv);
    
    form.addEventListener('submit', function(e) {
        const ticker = tickerInput.value.trim().split(/\s+/)[0];
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

// Password visibility toggle
function togglePassword(button) {
    const input = button.previousElementSibling;
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    
    // Update eye icon
    const icon = button.querySelector('i');
    icon.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
}

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.querySelector('form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.querySelector('input[name="password"]');
            const confirmPassword = document.querySelector('input[name="confirm_password"]');
            
            if (confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }
});