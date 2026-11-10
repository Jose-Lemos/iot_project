let miGrafico = null;

export function renderChart(graficoData) {
    const ctx = document.getElementById('iotChart');
    if (!ctx) return;

    if (miGrafico) {
        miGrafico.destroy();
    }

    miGrafico = new window.Chart(ctx, {
        type: 'line',
        data: {
            labels: graficoData.labels || [],
            datasets: [
                {
                    label: 'Temperatura (°C)',
                    data: graficoData.temperatura || [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37,99,235,0.08)',
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: 'Humedad (%)',
                    data: graficoData.humedad || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16,185,129,0.08)',
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: 'Gas (ppm)',
                    data: graficoData.gas || [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245,158,11,0.08)',
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: 'CO (ppm)',
                    data: graficoData.co || [],
                    borderColor: '#dc2626',
                    backgroundColor: 'rgba(220,38,38,0.08)',
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointRadius: 2,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: { precision: 0 }
                }
            }
        }
    });
}
