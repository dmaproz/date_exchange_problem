// Exchange Rate Visualizer App
function exchangeApp() {
    return {
        // Data properties
        startDate: '2025-07-01',
        endDate: '2025-07-10',
        fromCurrency: 'USD',
        toCurrency: 'EUR',
        data: null,
        error: null,
        loading: false,

        // Chart instances
        rateChart: null,
        changeChart: null,

        // Initialize the app
        init() {
            this.fetchData();
        },

        // Fetch data from API
        async fetchData() {
            this.loading = true;
            this.error = null;

            try {
                const params = new URLSearchParams({
                    start: this.startDate,
                    end: this.endDate,
                    from: this.fromCurrency,
                    to: this.toCurrency
                });

                const response = await fetch(`/api/rates?${params}`);
                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || 'Failed to fetch data');
                }

                this.data = result;
                this.error = null;

                // Update charts after data is loaded
                this.$nextTick(() => {
                    this.updateCharts();
                });

            } catch (err) {
                this.error = err.message;
                this.data = null;
            } finally {
                this.loading = false;
            }
        },

        // Update both charts
        updateCharts() {
            if (!this.data) return;

            this.updateRateChart();
            this.updateChangeChart();
        },

        // Update the rate trend chart
        updateRateChart() {
            const ctx = document.getElementById('rateChart');
            if (!ctx) return;

            // Destroy existing chart
            if (this.rateChart) {
                this.rateChart.destroy();
            }

            const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.1)');

            this.rateChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.data.labels,
                    datasets: [{
                        label: `${this.fromCurrency} to ${this.toCurrency}`,
                        data: this.data.rates,
                        borderColor: '#3b82f6',
                        backgroundColor: gradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: '#1d4ed8',
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: '#e2e8f0',
                                font: {
                                    size: 14,
                                    weight: '500'
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#ffffff',
                            bodyColor: '#e2e8f0',
                            borderColor: '#3b82f6',
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    return `Rate: ${context.parsed.y.toFixed(5)} ${context.dataset.label.split(' to ')[1]}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                                borderColor: 'rgba(255, 255, 255, 0.2)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                font: {
                                    size: 12
                                }
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                                borderColor: 'rgba(255, 255, 255, 0.2)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                font: {
                                    size: 12
                                },
                                callback: function(value) {
                                    return value.toFixed(5);
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    elements: {
                        point: {
                            hoverRadius: 8
                        }
                    }
                }
            });
        },

        // Update the daily changes chart
        updateChangeChart() {
            const ctx = document.getElementById('changeChart');
            if (!ctx) return;

            // Destroy existing chart
            if (this.changeChart) {
                this.changeChart.destroy();
            }

            // Create colors based on positive/negative changes
            const colors = this.data.changes.map(change =>
                change >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'
            );

            const borderColors = this.data.changes.map(change =>
                change >= 0 ? '#22c55e' : '#ef4444'
            );

            this.changeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: this.data.labels,
                    datasets: [{
                        label: 'Daily Change (%)',
                        data: this.data.changes,
                        backgroundColor: colors,
                        borderColor: borderColors,
                        borderWidth: 2,
                        borderRadius: 4,
                        borderSkipped: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: '#e2e8f0',
                                font: {
                                    size: 14,
                                    weight: '500'
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#ffffff',
                            bodyColor: '#e2e8f0',
                            borderColor: '#8b5cf6',
                            borderWidth: 1,
                            cornerRadius: 8,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const sign = value >= 0 ? '+' : '';
                                    return `Change: ${sign}${value.toFixed(2)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                                borderColor: 'rgba(255, 255, 255, 0.2)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                font: {
                                    size: 12
                                }
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)',
                                borderColor: 'rgba(255, 255, 255, 0.2)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                font: {
                                    size: 12
                                },
                                callback: function(value) {
                                    return value.toFixed(2) + '%';
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        },

        // Format currency for display
        formatCurrency(value, currency) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 5,
                maximumFractionDigits: 5
            }).format(value);
        },

        // Format percentage for display
        formatPercentage(value) {
            const sign = value >= 0 ? '+' : '';
            return `${sign}${value.toFixed(2)}%`;
        },

        // Get trend icon
        getTrendIcon(change) {
            if (change > 0) return 'fas fa-arrow-up text-green-400';
            if (change < 0) return 'fas fa-arrow-down text-red-400';
            return 'fas fa-minus text-gray-400';
        },

        // Get change color class
        getChangeColor(change) {
            if (change > 0) return 'text-green-400';
            if (change < 0) return 'text-red-400';
            return 'text-gray-400';
        }
    }
}

// Initialize Chart.js defaults for dark theme
Chart.defaults.color = '#e2e8f0';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.1)';

// Set default font
Chart.defaults.font.family = "'Inter', 'system-ui', 'sans-serif'";
Chart.defaults.font.size = 12;