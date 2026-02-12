document.addEventListener('DOMContentLoaded', function() {

    // 1. LEER DATOS DESDE EL HTML (Bridge Pattern)
    const dataContainer = document.getElementById('dashboardData');
    if (!dataContainer) return; // Seguridad

    const newAchievement = dataContainer.getAttribute('data-new-achievement');

    // 2. LÓGICA DE MODALES (Edit & Delete) - VERSIÓN OPTIMIZADA

    // A) Modal Editar
    const editModalEl = document.getElementById('editWeightModal');
    if (editModalEl) {
        editModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;

            // Extraer datos (URL directa desde Flask)
            const url = button.getAttribute('data-url');
            const weight = button.getAttribute('data-weight');
            const date = button.getAttribute('data-date');

            // Actualizar DOM
            const form = editModalEl.querySelector('#editForm');
            form.action = url;

            editModalEl.querySelector('#editWeightInput').value = weight;
            editModalEl.querySelector('#editDateInput').value = date;
        });
    }

    // B) Modal Eliminar
    const deleteModalEl = document.getElementById('deleteWeightModal');
    if (deleteModalEl) {
        deleteModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;

            const url = button.getAttribute('data-url');
            const date = button.getAttribute('data-date'); // Ahora pasamos la fecha formateada para mostrarla

            // Actualizar DOM
            const form = deleteModalEl.querySelector('#deleteForm');
            form.action = url;

            // Mostrar fecha para confirmar (Mejora de UX)
            const dateText = deleteModalEl.querySelector('#deleteDateText');
            if (dateText) dateText.innerText = date;
        });
    }

    // 3. INICIALIZAR FECHA DE HOY (Para el modal de "Nuevo Registro")
    const dateInput = document.getElementById('dateInput');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    // 4. ANIMACIÓN DE MEDALLAS EXISTENTES
    const activeAchievements = document.querySelectorAll('.achievement-wrapper.active');
    activeAchievements.forEach((el, index) => {
        el.style.opacity = "0";
        setTimeout(() => {
            el.style.opacity = "1";
        }, 200 * index);
    });

    // 5. SISTEMA DE LOGROS NUEVOS (Confetti)
    if (newAchievement) {
        const badgeData = {
            'bronce': { title: 'Medalla de Bronce', color: '#cd7f32', icon: 'bi-medal-fill' },
            'plata':  { title: 'Medalla de Plata',  color: '#7a7a7a', icon: 'bi-medal-fill' },
            'oro':    { title: 'Medalla de Oro',    color: '#ffc107', icon: 'bi-medal-fill' },
            'campeon':{ title: 'Trofeo de Campeón', color: '#0d6efd', icon: 'bi-trophy-fill' }
        };

        const data = badgeData[newAchievement];
        if (data) {
            const modalTitle = document.getElementById('modalTitle');
            const modalIcon = document.getElementById('modalIcon');

            modalTitle.innerText = data.title;
            modalTitle.style.color = data.color;
            modalIcon.className = `bi display-1 ${data.icon}`;
            modalIcon.style.color = data.color;
            modalIcon.style.filter = `drop-shadow(0 0 15px ${data.color})`;

            const achievementModal = new bootstrap.Modal(document.getElementById('achievementModal'));
            achievementModal.show();

            launchConfetti();
        }
    }
});

function launchConfetti() {
    var duration = 3 * 1000;
    var animationEnd = Date.now() + duration;
    var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 2000 };

    function randomInRange(min, max) { return Math.random() * (max - min) + min; }

    var interval = setInterval(function() {
        var timeLeft = animationEnd - Date.now();
        if (timeLeft <= 0) { return clearInterval(interval); }
        var particleCount = 50 * (timeLeft / duration);
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
    }, 250);
}