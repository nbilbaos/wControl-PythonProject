// app/static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Actualizar año en el footer automáticamente
    const yearElement = document.getElementById('year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    // Aquí puedes inicializar tooltips de Bootstrap globalmente si los usas a futuro
});