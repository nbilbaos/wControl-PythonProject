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

    // --- 1. GUARDAR TEMA ACTUAL Y FORZAR MODO CLARO ---
    const htmlEl = document.documentElement;
    const currentTheme = htmlEl.getAttribute('data-bs-theme');
    htmlEl.setAttribute('data-bs-theme', 'light');

    // --- 2. PREPARAR ELEMENTOS VISUALES ---
    element.classList.add('printing-mode');

    // Ocultar manualmente los botones de edición/borrar para asegurar que no salgan
    const noPrintElements = element.querySelectorAll('.no-print');
    noPrintElements.forEach(el => el.style.display = 'none');

    // Mostrar el mensaje de pie de página ("Reporte generado automáticamente...")
    const printFooter = element.querySelector('.printing-footer');
    if (printFooter) printFooter.style.display = 'block';

    // --- 3. CONFIGURACIÓN DEL PDF ---
    const opt = {
        margin:       [15, 10, 15, 10], // Margen un poco más grande abajo para el footer
        filename:     `Reporte_Clinico_${userName}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  {
            scale: 2,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff',

        },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // --- 4. GENERAR PDF Y RESTAURAR ---
    html2pdf().set(opt).from(element).save().then(() => {
        // Restaurar el tema oscuro (si estaba activado)
        if (currentTheme) {
            htmlEl.setAttribute('data-bs-theme', currentTheme);
        }

        // Restaurar la vista normal
        element.classList.remove('printing-mode');
        noPrintElements.forEach(el => el.style.display = '');
        if (printFooter) printFooter.style.display = 'none';

    }).catch(err => {
        console.error("Error generando PDF:", err);

        // Restaurartodo también en caso de que falle la generación
        if (currentTheme) htmlEl.setAttribute('data-bs-theme', currentTheme);
        element.classList.remove('printing-mode');
        noPrintElements.forEach(el => el.style.display = '');
        if (printFooter) printFooter.style.display = 'none';
    });
}
document.addEventListener('DOMContentLoaded', function() {
    const fabContainer = document.querySelector('.fab-container');
    // Busca tu footer (ajusta el selector si tu footer tiene otra clase/ID)
    const footer = document.querySelector('footer') || document.querySelector('.footer');

    if (fabContainer && footer) {
        window.addEventListener('scroll', () => {
            const footerRect = footer.getBoundingClientRect();
            const windowHeight = window.innerHeight;

            if (footerRect.top < windowHeight) {
                // El footer está visible, calculamos cuánto empujar
                const overlap = windowHeight - footerRect.top;

                // Usamos translate3d para subirlo (eje Y) y mantener el parche de iOS (eje Z)
                fabContainer.style.transform = `translate3d(0, -${overlap}px, 0)`;
            } else {
                // El footer no se ve, devolvemos el botón a su lugar original
                fabContainer.style.transform = 'translate3d(0, 0, 0)';
            }
        });
    }
});