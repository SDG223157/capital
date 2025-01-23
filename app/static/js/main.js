document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const tickerInput = document.getElementById('ticker');

    let suggestionsDiv;
    if (tickerInput) {
        suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'suggestions';
        tickerInput.parentNode.appendChild(suggestionsDiv);
    }

    let debounceTimeout;

    function formatCompanyName(name) {
        return name.replace(/\\'/g, "'");
    }

    if (tickerInput) {
        tickerInput.addEventListener('dblclick', function() {
            if (this.value) {
                this.value = '';
                if (suggestionsDiv) suggestionsDiv.style.display = 'none';
            }
        });

        tickerInput.addEventListener('input', function() {
            clearTimeout(debounceTimeout);
            const query = this.value.trim();

            if (query.length < 1) {
                if (suggestionsDiv) suggestionsDiv.style.display = 'none';
                return;
            }

            debounceTimeout = setTimeout(() => {
                fetch(`/search_ticker?query=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (suggestionsDiv) suggestionsDiv.innerHTML = '';

                        if (data.length > 0) {
                            const filteredData = data.filter(item => 
                                item.symbol.toUpperCase() !== item.name.toUpperCase()
                            );

                            if (filteredData.length > 0 && suggestionsDiv) {
                                filteredData.forEach(item => {
                                    const div = document.createElement('div');
                                    div.className = 'suggestion-item';
                                    const formattedName = formatCompanyName(item.name);

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
                                        if (suggestionsDiv) suggestionsDiv.style.display = 'none';
                                    });

                                    suggestionsDiv.appendChild(div);
                                });
                                suggestionsDiv.style.display = 'block';
                            } else if (suggestionsDiv) {
                                suggestionsDiv.style.display = 'none';
                            }
                        } else if (suggestionsDiv) {
                            suggestionsDiv.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                        if (suggestionsDiv) suggestionsDiv.style.display = 'none';
                    });
            }, 300);
        });

        document.addEventListener('click', function(e) {
            if (suggestionsDiv && (!tickerInput.contains(e.target) && !suggestionsDiv.contains(e.target))) {
                suggestionsDiv.style.display = 'none';
            }
        });

        tickerInput.addEventListener('click', function(e) {
            e.stopPropagation();
            if (this.value.trim().length > 0 && suggestionsDiv) {
                suggestionsDiv.style.display = 'block';
            }
        });
    }

    const analyzeForm = document.getElementById('analyze-form');
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            const tickerInput = document.getElementById('ticker');
            if (!tickerInput || !tickerInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a ticker symbol');
            }
        });
    }

    function togglePassword(button) {
        const input = button.closest('.input-with-icon').querySelector('input');
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);

        const icon = button.querySelector('i');
        icon.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
    }

    window.togglePassword = togglePassword;
});