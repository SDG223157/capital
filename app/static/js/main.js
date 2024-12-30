document.addEventListener('DOMContentLoaded', function() {
    const tickerInput = document.getElementById('ticker');
    const suggestionsDiv = document.querySelector('.suggestions');
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
    if (!tickerInput || !suggestionsDiv) {
        console.error('Required elements not found');
        return;
    }

    tickerInput.addEventListener('input', function() {
        clearTimeout(debounceTimeout);
        const query = this.value.trim();
        
        if (query.length < 1) {
            suggestionsDiv.style.display = 'none';
            suggestionsDiv.innerHTML = '';
            return;
        }
        
        debounceTimeout = setTimeout(() => {
            console.log('Searching for:', query); // Debug log
            fetch(`/search_ticker?query=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Search results:', data); // Debug log
                    suggestionsDiv.innerHTML = '';
                    
                    if (data.length > 0) {
                        data.forEach(item => {
                            const div = document.createElement('div');
                            div.className = 'suggestion-item';
                            
                            const symbolSpan = document.createElement('span');
                            symbolSpan.className = 'symbol';
                            symbolSpan.textContent = item.symbol;
                            
                            const nameSpan = document.createElement('span');
                            nameSpan.className = 'name';
                            nameSpan.textContent = item.name;
                            
                            div.appendChild(symbolSpan);
                            div.appendChild(nameSpan);
                            
                            div.addEventListener('click', function() {
                                tickerInput.value = item.symbol;
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
    
    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!tickerInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });

    // Form submission (if needed)
    const analyzeForm = document.getElementById('analyze-form');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            if (!tickerInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a ticker symbol');
            }
        });
    }
});

// Password toggle functionality
function togglePassword(button) {
    const input = button.closest('.input-with-icon').querySelector('input');
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    
    const icon = button.querySelector('i');
    icon.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
}

// Make togglePassword globally available
window.togglePassword = togglePassword;