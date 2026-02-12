document.addEventListener('DOMContentLoaded', function() {

    // 1. LEER DATOS DESDE EL HTML (Bridge Pattern)
    const dataContainer = document.getElementById('dashboardData');
    const newAchievement = dataContainer.getAttribute('data-new-achievement');
    const progressPct = parseFloat(dataContainer.getAttribute('data-progress')) || 0;

    // 2. CONFIGURACIÓN DE MODALES (Edit & Delete)
    const editModalEl = document.getElementById('editWeightModal');
    if (editModalEl) {
        editModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const id = button.getAttribute('data-id');
            const weight = button.getAttribute('data-weight');
            const date = button.getAttribute('data-date');

            // Rellenar formulario
            editModalEl.querySelector('#editWeightInput').value = weight;
            editModalEl.querySelector('#editDateInput').value = date;
            editModalEl.querySelector('#editForm').action = "/edit_weight/" + id;
        });
    }

    const deleteModalEl = document.getElementById('deleteWeightModal');
    if (deleteModalEl) {
        deleteModalEl.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const id = button.getAttribute('data-id');
            deleteModalEl.querySelector('#deleteForm').action = "/delete_weight/" + id;
        });
    }

    // 3. INICIALIZAR FECHA DE HOY
    const dateInputs = document.querySelectorAll('#dateInput, #editDateInput');
    const today = new Date().toISOString().split('T')[0];
    dateInputs.forEach(input => {
        if (!input.value) input.value = today;
    });

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
            // Rellenar Modal
            const modalTitle = document.getElementById('modalTitle');
            const modalIcon = document.getElementById('modalIcon');

            modalTitle.innerText = data.title;
            modalTitle.style.color = data.color;
            modalIcon.className = `bi display-1 ${data.icon}`;
            modalIcon.style.color = data.color;
            modalIcon.style.filter = `drop-shadow(0 0 15px ${data.color})`;

            // Mostrar Modal (Bootstrap 5 JS)
            const achievementModal = new bootstrap.Modal(document.getElementById('achievementModal'));
            achievementModal.show();

            // Lanzar Confetti
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