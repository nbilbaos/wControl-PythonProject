// app/static/js/admin_screenshots.js

document.addEventListener('DOMContentLoaded', function() {
    const urlTab = document.getElementById('url-tab');
    const fileTab = document.getElementById('file-tab');
    const inputUrl = document.getElementById('inputUrl');
    const inputFile = document.getElementById('inputFile');

    // Validación: Si no existen los elementos, no hacemos nada (evita errores en otras pág)
    if (!urlTab || !fileTab || !inputUrl || !inputFile) return;

    // A) Si seleccionamos la pestaña "URL Externa"
    urlTab.addEventListener('shown.bs.tab', function () {
        // Hacemos obligatorio el campo URL
        inputUrl.setAttribute('required', '');

        // Quitamos obligatorio al archivo y lo limpiamos
        inputFile.removeAttribute('required');
        inputFile.value = '';
    });

    // B) Si seleccionamos la pestaña "Archivo Local"
    fileTab.addEventListener('shown.bs.tab', function () {
        // Hacemos obligatorio el campo Archivo
        inputFile.setAttribute('required', '');

        // Quitamos obligatorio a la URL y la limpiamos
        inputUrl.removeAttribute('required');
        inputUrl.value = '';
    });
});