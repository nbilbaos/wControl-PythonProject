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

    // 1. Dataset: META (Primero para que quede al fondo)
    const datasets = [];

    // 1. Dataset: META
    if (apiData.goal) {
        const goalLine = new Array(apiData.data.length).fill(apiData.goal);
        datasets.push({
            label: 'Meta',
            data: goalLine,
            borderColor: '#1cc88a',
            borderWidth: 2,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            // Esto evita que la meta fuerce la escala si está muy lejos.
            // Si quieres que SIEMPRE salga, quita esto.
            // Si quieres priorizar el zoom en los datos, descomenta las líneas de abajo si tuvieras un segundo eje.
            // Pero la solución más simple es filtrar los datos antes de enviarlos.
        });
    }

    // 2. Dataset: TENDENCIA
    if (apiData.show_trend && apiData.trendline.length > 0) {
        datasets.push({
            label: 'Tendencia',
            data: apiData.trendline,
            borderColor: '#e74a3b', // Rojo
            borderWidth: 2,
            borderDash: [3, 3],     // Punteado fino
            pointRadius: 0,
            fill: false,
            tension: 0.4            // Suavizado ligero para que se vea orgánica
        });
    }

    // 3. Dataset: PESO REAL (Al final para que quede encima)
    datasets.push({
        label: 'Peso',
        data: apiData.data,
        borderColor: '#4e73df', // Azul
        backgroundColor: 'rgba(78, 115, 223, 0.05)',
        borderWidth: 3,
        pointRadius: 4,
        pointBackgroundColor: '#fff',
        pointBorderColor: '#4e73df',
        pointBorderWidth: 2,
        fill: true,
        tension: 0.3
    });

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
            responsive: true,

            // --- CORRECCIÓN DE MÁRGENES ---
            layout: {
                padding: {
                    left: -10,  // Truco: Margen negativo para pegar el eje Y al borde
                    right: 10,
                    top: 10,
                    bottom: 0
                }
            },

            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end', // Leyenda a la derecha
                    labels: { boxWidth: 10, usePointStyle: true, padding: 15 }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#6e707e',
                    bodyColor: '#858796',
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    padding: 10
                }
            },

        scales: {
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { maxTicksLimit: 7, maxRotation: 0 }
                },
                y: {
                    // --- CORRECCIÓN DE ZOOM ---
                    // No forzamos el 'min' ni 'max' para incluir la meta.
                    // Dejamos que Chart.js se ajuste AUTOMÁTICAMENTE a los datos de PESO (datasets[2]).
                    grace: '8%', // Agrega un 10% de espacio extra arriba/abajo de tus datos reales

                    grid: {
                        color: "rgb(234, 236, 244)",
                        zeroLineColor: "transparent",
                        drawBorder: false,
                        borderDash: [2]
                    },
                    ticks: {
                        padding: 10,
                        maxTicksLimit: 6,
                        callback: function(value) { return Math.round(value); }
                    }
                }
            }
        }
    });
}