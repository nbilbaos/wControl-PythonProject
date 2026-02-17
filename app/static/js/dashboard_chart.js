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
        // Calculamos min y max de los datos actuales
        const minWeight = Math.min(...apiData.data);
        const maxWeight = Math.max(...apiData.data);

        // Solo mostramos la meta si está "razonablemente cerca" (ej: dentro de un rango de 15kg del dato visible)
        // O si el usuario quiere verla sí o sí, puedes quitar este IF.
        // Pero para solucionar tu problema de zoom, esto es lo mejor:

        const isGoalClose = (apiData.goal >= minWeight - 15) && (apiData.goal <= maxWeight + 15);

        if (isGoalClose) {
            const goalLine = new Array(apiData.data.length).fill(apiData.goal);
            datasets.push({
                label: 'Meta',
                data: goalLine,
                borderColor: '#1cc88a',
                borderWidth: 2,
                borderDash: [6, 4],
                pointRadius: 0,
                fill: false,
                tension: 0
            });
        }
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

    // --- NUEVO: Detectar tema antes de dibujar ---
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const textColor = currentTheme === 'dark' ? '#adb5bd' : '#858796';
    const gridColor = currentTheme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgb(234, 236, 244)';

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
                    align: 'end',
                    labels: {
                        boxWidth: 10,
                        usePointStyle: true,
                        padding: 15,
                        color: textColor // <--- APLICAR AQUÍ
                    }
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
                    ticks: { maxTicksLimit: 7, maxRotation: 0, color: textColor}
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
                        color: textColor,
                        callback: function(value) { return Math.round(value); }
                    }
                }
            }
        }
    });
}
// ESCUCHAR CAMBIO DE TEMA PARA ACTUALIZAR EL GRÁFICO
window.addEventListener('themeChanged', function(e) {
    if (myChart) {
        const theme = e.detail.theme;

        // Definir colores según el tema
        const textColor = theme === 'dark' ? '#adb5bd' : '#858796';
        const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgb(234, 236, 244)';

        // Actualizar opciones
        myChart.options.scales.x.ticks.color = textColor;
        myChart.options.scales.y.ticks.color = textColor;
        myChart.options.scales.y.grid.color = gridColor;
        myChart.options.plugins.legend.labels.color = textColor;

        // Actualizar tooltip para modo oscuro
        if (theme === 'dark') {
            myChart.options.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            myChart.options.plugins.tooltip.titleColor = '#fff';
            myChart.options.plugins.tooltip.bodyColor = '#ccc';
            myChart.options.plugins.tooltip.borderColor = '#333';
        } else {
            myChart.options.plugins.tooltip.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            myChart.options.plugins.tooltip.titleColor = '#6e707e';
            myChart.options.plugins.tooltip.bodyColor = '#858796';
            myChart.options.plugins.tooltip.borderColor = '#dddfeb';
        }

        // Re-dibujar
        myChart.update();
    }
});