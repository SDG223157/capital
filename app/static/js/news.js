// app/static/js/news.js

class NewsAnalysis {
    constructor(symbol) {
        this.symbol = symbol;
        this.charts = {};
        this.initializeCharts();
        this.setupEventListeners();
        this.updateInterval = null;
        this.startAutoRefresh();
    }

    initializeCharts() {
        // Initialize sentiment timeline chart
        const timelineCtx = document.getElementById('sentimentChart')?.getContext('2d');
        if (timelineCtx) {
            this.charts.timeline = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Sentiment Score',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += context.parsed.y.toFixed(2);
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            suggestedMin: -1,
                            suggestedMax: 1,
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    setupEventListeners() {
        // Setup refresh button
        const refreshBtn = document.getElementById('refreshData');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Setup date range filter
        const dateFilter = document.getElementById('dateRange');
        if (dateFilter) {
            dateFilter.addEventListener('change', () => this.refreshData());
        }
    }

    async refreshData() {
        try {
            this.setLoading(true);
            const dateRange = document.getElementById('dateRange')?.value || '7d';
            
            // Fetch all data in parallel
            const [timelineData, analysisData] = await Promise.all([
                this.fetchTimelineData(dateRange),
                this.fetchAnalysisData(dateRange)
            ]);

            // Update visualizations
            this.updateCharts(timelineData);
            this.updateAnalysis(analysisData);

        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh news analysis data');
        } finally {
            this.setLoading(false);
        }
    }

    async fetchTimelineData(dateRange) {
        const response = await fetch(`/api/news/${this.symbol}/timeline?range=${dateRange}`);
        if (!response.ok) throw new Error('Failed to fetch timeline data');
        return await response.json();
    }

    async fetchAnalysisData(dateRange) {
        const response = await fetch(`/api/news/${this.symbol}/analysis?range=${dateRange}`);
        if (!response.ok) throw new Error('Failed to fetch analysis data');
        return await response.json();
    }

    updateCharts(timelineData) {
        if (this.charts.timeline) {
            this.charts.timeline.data.labels = timelineData.dates;
            this.charts.timeline.data.datasets[0].data = timelineData.sentiments;
            this.charts.timeline.update();
        }
    }

    updateAnalysis(data) {
        // Update summary statistics
        this.updateElement('totalArticles', data.total_articles);
        this.updateElement('positiveCount', data.sentiment_distribution.positive);
        this.updateElement('negativeCount', data.sentiment_distribution.negative);
        this.updateElement('neutralCount', data.sentiment_distribution.neutral);
        
        // Update average sentiment
        const avgSentiment = document.getElementById('averageSentiment');
        if (avgSentiment) {
            avgSentiment.textContent = data.average_sentiment.toFixed(2);
            avgSentiment.className = this.getSentimentClass(data.average_sentiment);
        }

        // Update articles list
        this.updateArticlesList(data.articles);
    }

    updateArticlesList(articles) {
        const container = document.getElementById('articlesList');
        if (!container) return;

        container.innerHTML = articles.map(article => `
            <div class="news-card mb-4">
                <h3 class="text-lg font-semibold mb-2">
                    <a href="${article.url}" target="_blank" class="hover:text-blue-600">
                        ${this.escapeHtml(article.title)}
                    </a>
                </h3>
                <div class="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                    <span>${article.source}</span>
                    <span>${this.formatDate(article.published_at)}</span>
                    <span class="sentiment-badge ${this.getSentimentBadgeClass(article.sentiment.score)}">
                        ${article.sentiment.label} (${article.sentiment.score.toFixed(2)})
                    </span>
                </div>
                <p class="text-gray-700">${this.escapeHtml(article.summary)}</p>
            </div>
        `).join('');
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    getSentimentClass(score) {
        return score > 0.05 ? 'text-green-600' :
               score < -0.05 ? 'text-red-600' :
               'text-gray-600';
    }

    getSentimentBadgeClass(score) {
        return score > 0.05 ? 'positive' :
               score < -0.05 ? 'negative' :
               'neutral';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    setLoading(isLoading) {
        const loader = document.getElementById('dataLoader');
        if (loader) {
            loader.style.display = isLoading ? 'block' : 'none';
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mt-4';
        errorDiv.innerHTML = `
            <strong class="font-bold">Error!</strong>
            <span class="block sm:inline">${this.escapeHtml(message)}</span>
        `;

        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(errorDiv, container.firstChild);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }

    startAutoRefresh() {
        // Refresh every 5 minutes
        this.updateInterval = setInterval(() => this.refreshData(), 300000);
    }

    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const symbolElement = document.getElementById('symbolData');
    if (symbolElement) {
        const symbol = symbolElement.dataset.symbol;
        window.newsAnalysis = new NewsAnalysis(symbol);
    }
});