document.addEventListener('DOMContentLoaded', function() {
    // Existing ticker search functionality
    const form = document.getElementById('analysis-form');
    const tickerInput = document.getElementById('ticker');
    if (tickerInput) {
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
    }

    // Form submission
    const analyzeForm = document.getElementById('analyze-form');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            if (!tickerInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a ticker symbol');
            }
        });
    }

    // Flash messages functionality
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        // Add close button if it doesn't exist
        if (!message.querySelector('.close-flash')) {
            const closeButton = document.createElement('button');
            closeButton.className = 'close-flash';
            closeButton.innerHTML = '&times;';
            closeButton.addEventListener('click', () => {
                message.style.display = 'none';
            });
            message.appendChild(closeButton);
        }

        // Auto-hide flash messages after 5 seconds
        setTimeout(() => {
            message.style.display = 'none';
        }, 5000);
    });

    // Password toggle functionality
    function togglePassword(button) {
        const input = button.closest('.input-with-icon').querySelector('input');
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);
        
        const icon = button.querySelector('i');
        icon.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
    }

    // Initialize password toggle buttons
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            togglePassword(this);
        });
    });

    // Google Sign-In button enhancement
    const googleButton = document.querySelector('.google-auth-button');
    if (googleButton) {
        googleButton.addEventListener('mousedown', function(e) {
            this.style.backgroundColor = '#f1f1f1';
        });

        googleButton.addEventListener('mouseup', function(e) {
            this.style.backgroundColor = '#ffffff';
        });

        googleButton.addEventListener('mouseleave', function(e) {
            this.style.backgroundColor = '#ffffff';
        });
    }

    // Dropdown menu functionality
    const dropdownButton = document.querySelector('.dropdown-button');
    if (dropdownButton) {
        const dropdownContent = document.querySelector('.dropdown-content');
        
        dropdownButton.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownContent.style.display = dropdownContent.style.display === 'block' ? 'none' : 'block';
        });

        document.addEventListener('click', function() {
            if (dropdownContent) {
                dropdownContent.style.display = 'none';
            }
        });
    }
});

// Make togglePassword globally available
window.togglePassword = togglePassword;