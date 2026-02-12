let myChart = null;

document.addEventListener("DOMContentLoaded", function() {
    updateChart();
});

function toggleCustomDate() {
    const filterSelect = document.getElementById('timeFilter');
    const customDiv = document.getElementById('customDateRange');
    if (filterSelect && customDiv) {
        customDiv.style.display = (filterSelect.value === 'custom') ? 'block' : 'none';
    }
}

async function updateChart() {
    // 1. CERRAR MODAL (Versión Bootstrap 5 compatible)
    const modalEl = document.getElementById('chartSettingsModal');
    // Verificamos si existe una instancia de modal abierta
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) {
        modalInstance.hide();
    }

    // 2. LEER URL DESDE EL HTML (Bridge)
    const dataContainer = document.getElementById('dashboardData');
    const baseUrl = dataContainer.getAttribute('data-chart-api-url');

    if (!baseUrl) {
        console.error("No se encontró la URL de la API del gráfico");
        return;
    }

    const filter = document.getElementById('timeFilter').value;
    let url = `${baseUrl}?filter=${filter}`;

    if (filter === 'custom') {
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        url += `&start_date=${start}&end_date=${end}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        renderChart(data);
    } catch (error) {
        console.error('Error cargando gráfico:', error);
    }
}

function renderChart(apiData) {
    const ctx = document.getElementById('weightChart').getContext('2d');

    const datasets = [{
        label: 'Peso (kg)',
        data: apiData.data,
        borderColor: '#4e73df',
        backgroundColor: 'rgba(78, 115, 223, 0.05)',
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#fff',
        pointBorderWidth: 2,
        fill: true,
        tension: 0.3
    }];

    if (apiData.show_trend && apiData.trendline && apiData.trendline.length > 0) {
        datasets.push({
            label: 'Tendencia',
            data: apiData.trendline,
            borderColor: '#e74a3b',
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
            tension: 0,
            spanGaps: true
        });
    }

    if (myChart) {
        myChart.destroy();
    }

    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: apiData.labels,
            datasets: datasets
        },
        options: {
            maintainAspectRatio: false,
            layout: { padding: { left: 10, right: 25, top: 25, bottom: 0 } },
            scales: {
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { maxTicksLimit: 7 }
                },
                y: {
                    beginAtZero: false,
                    grace: '10%', // Zoom inteligente
                    ticks: {
                        maxTicksLimit: 5,
                        padding: 10,
                        callback: function(value) { return value + ' kg'; }
                    },
                    grid: {
                        color: "rgb(234, 236, 244)",
                        zeroLineColor: "rgb(234, 236, 244)",
                        drawBorder: false,
                        borderDash: [2],
                        zeroLineBorderDash: [2]
                    }
                }
            },
            plugins: {
                legend: { display: datasets.length > 1 }, // Solo muestra leyenda si hay tendencia
                tooltip: {
                    backgroundColor: "rgb(255,255,255)",
                    bodyColor: "#858796",
                    titleMarginBottom: 10,
                    titleColor: '#6e707e',
                    titleFont: { size: 14 },
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    xPadding: 15,
                    yPadding: 15,
                    displayColors: false,
                    intersect: false,
                    mode: 'index',
                    caretPadding: 10,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + ' kg';
                        }
                    }
                }
            }
        }
    });
}