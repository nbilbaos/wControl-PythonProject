// app/static/js/theme.js

document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const htmlElement = document.documentElement;

    // Función para aplicar el tema y cambiar el icono
    function applyTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);

        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.classList.replace('bi-moon-stars-fill', 'bi-sun-fill');
                themeIcon.classList.add('text-warning'); // Sol amarillo
                themeIcon.classList.remove('text-secondary');
            } else {
                themeIcon.classList.replace('bi-sun-fill', 'bi-moon-stars-fill');
                themeIcon.classList.add('text-secondary'); // Luna gris
                themeIcon.classList.remove('text-warning');
            }
        }

        // Disparar un evento personalizado para que Chart.js lo escuche
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: theme } }));
    }

    // Configurar estado inicial del icono
    const currentTheme = htmlElement.getAttribute('data-bs-theme');
    applyTheme(currentTheme);

    // Evento del botón
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const newTheme = htmlElement.getAttribute('data-bs-theme') === 'light' ? 'dark' : 'light';
            applyTheme(newTheme);
        });
    }
});
