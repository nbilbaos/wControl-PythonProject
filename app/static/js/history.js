document.addEventListener('DOMContentLoaded', function() {

    // 1. FECHA DEL REPORTE
    const dateHeader = document.getElementById('report-date-header');
    if (dateHeader) {
        dateHeader.innerText = new Date().toLocaleDateString('es-CL', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
    }

    // 2. LÓGICA DE MODALES (Edit & Delete)
    // Esto es mucho más eficiente: escuchamos el evento de apertura del modal

    // A) Modal de Edición
    const editModal = document.getElementById('editModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function (event) {
            // Botón que disparó el modal
            const button = event.relatedTarget;

            // Extraer info de los data-attributes
            const url = button.getAttribute('data-url');
            const weight = button.getAttribute('data-weight');
            const date = button.getAttribute('data-date');

            // Actualizar el contenido del modal
            const form = editModal.querySelector('#editForm');
            form.action = url;
            editModal.querySelector('#editWeightInput').value = weight;
            editModal.querySelector('#editDateInput').value = date;
        });
    }

    // B) Modal de Eliminación
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const url = button.getAttribute('data-url');
            const weight = button.getAttribute('data-weight');
            const date = button.getAttribute('data-date');

            // Actualizar textos y acción del formulario
            const form = deleteModal.querySelector('#deleteForm');
            form.action = url;
            document.getElementById('deleteDateText').innerText = date;
            document.getElementById('deleteWeightText').innerText = weight + " kg";
        });
    }

    // 3. GENERACIÓN DE PDF
    const btnPDF = document.getElementById('btnDownloadPDF');
    if (btnPDF) {
        btnPDF.addEventListener('click', generateHistoryPDF);
    }
});

function generateHistoryPDF() {
    const element = document.getElementById('history-report');

    // Obtener nombre de usuario limpio
    const userDiv = document.getElementById('userData');
    const userName = userDiv ? userDiv.getAttribute('data-username').replace(/\s+/g, '_') : 'Usuario';

    const opt = {
        margin:       [10, 10, 10, 10], // Márgenes en mm
        filename:     `Historial_WeightControl_${userName}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true, logging: false },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // Agregar clase para ocultar botones durante la impresión
    element.classList.add('printing-mode');

    html2pdf().set(opt).from(element).save().then(() => {
        // Restaurar vista normal
        element.classList.remove('printing-mode');
    }).catch(err => {
        console.error("Error generando PDF:", err);
        element.classList.remove('printing-mode');
    });
}