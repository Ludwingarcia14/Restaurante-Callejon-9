/* Enviar formularios via AJAX */
const formularios_ajax = document.querySelectorAll(".FormularioAjax");

formularios_ajax.forEach(formulario => {
    formulario.addEventListener("submit", function (e) {
        e.preventDefault();

        // Determina cuál botón se presionó
        let botonPresionado = e.submitter; // 'submitter' es la referencia al botón que se usó para enviar el formulario
        let mensaje = '';

        if (botonPresionado.classList.contains('btn-submit-cliente')) {
            // Mensaje específico para el botón de cliente
            mensaje = "Al aceptar, autorizas  que  POTENCIAL PYME  se compromete a proteger y respetar tu privacidad, y solo usaremos tu información personal para administrar tu cuenta y proporcionar los productos y servicios que nos solicitaste.";
        } else if (botonPresionado.classList.contains('button')) {
            // Mensaje general para otros usuarios
            mensaje = "Quieres realizar la acción solicitada.";
        }

        // Mostrar la alerta con el mensaje correspondiente
        Swal.fire({
            title: 'Aceptar',
            text: mensaje,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Aceptar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                //Muestra el modal de carga
                const loadingModal = document.getElementById('loading-modal');
                loadingModal.style.display = 'block';

                let data = new FormData(this);
                let method = this.getAttribute("method");
                let action = this.getAttribute("action");

                let encabezados = new Headers();

                let config = {
                    method: method,
                    headers: encabezados,
                    mode: 'cors',
                    cache: 'no-cache',
                    body: data
                };

                fetch(action, config)
                    .then(respuesta => respuesta.json())
                    .then(respuesta => {
                        // Oculta el modal antes de la alerta
                        loadingModal.style.display = 'none';
                        return alertas_ajax(respuesta);
                    })
                    .catch(error => {
                        console.error("Error:", error);
                        // Ocultar el modal si ocurre un error
                        loadingModal.style.display = 'none';
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'Ha ocurrido un problema al procesar la solicitud.'
                        });
                    });
            }
        });
    });
});




function alertas_ajax(alerta) {
    if (alerta.tipo == "simple") {

        Swal.fire({
            icon: alerta.icono,
            title: alerta.titulo,
            text: alerta.texto,
            confirmButtonText: 'Aceptar'
        });

    } else if (alerta.tipo == "recargar") {

        Swal.fire({
            icon: alerta.icono,
            title: alerta.titulo,
            text: alerta.texto,
            confirmButtonText: 'Aceptar'
        }).then((result) => {
            if (result.isConfirmed) {
                location.reload();
            }
        });

    } else if (alerta.tipo == "limpiar") {

        Swal.fire({
            icon: alerta.icono,
            title: alerta.titulo,
            text: alerta.texto,
            confirmButtonText: 'Aceptar'
        }).then((result) => {
            if (result.isConfirmed) {
                document.querySelector(".FormularioAjax").reset();
            }
        });

    } else if (alerta.tipo == "redireccionar") {
        window.location.href = alerta.url;
    }
}



/* Boton cerrar sesion */
let btn_exit = document.querySelectorAll(".btn-exit");

btn_exit.forEach(exitSystem => {
    exitSystem.addEventListener("click", function (e) {

        e.preventDefault();

        Swal.fire({
            title: '¿Quieres salir del sistema?',
            text: "La sesión actual se cerrará y saldrás del sistema",
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Si, salir',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                let url = this.getAttribute("href");
                window.location.href = url;
            }
        });

    });
});