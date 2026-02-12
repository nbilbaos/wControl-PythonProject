document.addEventListener('DOMContentLoaded', function() {

    // 1. FECHA CABECERA (Para el reporte PDF)
    const dateHeader = document.getElementById('report-date-header');
    if (dateHeader) {
        dateHeader.innerText = new Date().toLocaleDateString('es-CL', {
            year: 'numeric', month: 'long', day: 'numeric'
        });
    }

    // 2. CONTROL DE FILTROS (Mostrar inputs si es Custom)
    const timeFilter = document.getElementById('timeFilter');
    const customInputs = document.getElementById('customDateInputs');

    function checkCustom() {
        if (timeFilter && customInputs) {
            customInputs.style.display = (timeFilter.value === 'custom') ? 'flex' : 'none';
        }
    }

    if (timeFilter) {
        timeFilter.addEventListener('change', checkCustom);
        checkCustom(); // Ejecutar al inicio para verificar estado
    }

    // 3. GENERACIÓN DE PDF PROFESIONAL
    const btnPDF = document.getElementById('btnDownloadPDF');
    if (btnPDF) {
        btnPDF.addEventListener('click', generateMedicalPDF);
    }

    // 4. LÓGICA DE MODALES (Edit & Delete)

    // Modal Editar
    const editModal = document.getElementById('editModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const url = button.getAttribute('data-url');
            const weight = button.getAttribute('data-weight');
            const date = button.getAttribute('data-date');

            const form = editModal.querySelector('#editForm');
            if (form) {
                form.action = url;
                editModal.querySelector('#editWeightInput').value = weight;
                editModal.querySelector('#editDateInput').value = date;
            }
        });
    }

    // Modal Eliminar
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const url = button.getAttribute('data-url');
            const weight = button.getAttribute('data-weight');
            const date = button.getAttribute('data-date');

            const form = deleteModal.querySelector('#deleteForm');
            if (form) form.action = url;

            document.getElementById('deleteDateText').innerText = date;
            document.getElementById('deleteWeightText').innerText = weight + " kg";
        });
    }
});

function generateMedicalPDF() {
    const element = document.getElementById('history-report');
    const userDiv = document.getElementById('userData');
    const userName = userDiv ? userDiv.getAttribute('data-username').replace(/\s+/g, '_') : 'Paciente';

    if (!element) return;

    const opt = {
        margin:       [10, 10, 10, 10],
        filename:     `Reporte_Clinico_${userName}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  {
            scale: 2,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff'
        },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // Añadir clase para estilos de impresión
    element.classList.add('printing-mode');

    html2pdf().set(opt).from(element).save().then(() => {
        element.classList.remove('printing-mode');
    }).catch(err => {
        console.error("Error generando PDF:", err);
        element.classList.remove('printing-mode');
    });
}