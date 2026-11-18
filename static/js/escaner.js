/* Lectura de códigos de barras y QR (html5-qrcode 2.3.8).
   Todo campo con data-escaner="barras" o "qr" recibe dos botones: cámara y subir imagen.
   El lector inalámbrico opcional sigue funcionando porque escribe en el campo como un teclado. */
(function () {
  "use strict";

  let lectorCam = null;        // instancia en uso para la cámara
  let campoActivo = null;      // input que recibirá el código leído
  let modoActual = "camara";

  const modalEl = document.getElementById("modalEscaner");
  if (!modalEl || typeof Html5Qrcode === "undefined") return;

  const modal = new bootstrap.Modal(modalEl);
  const estado = document.getElementById("estadoEscaner");
  const panelCamara = document.getElementById("panelCamara");
  const panelImagen = document.getElementById("panelImagen");
  const zonaImagen = document.getElementById("zonaImagen");
  const archivo = document.getElementById("archivoEscaner");
  const lectorImagenEl = document.getElementById("lectorImagen");
  const botonesModo = modalEl.querySelectorAll("[data-modo]");

  function aviso(texto, tipo) {
    estado.textContent = texto;
    estado.className = "small mt-2 mb-0 " + (tipo === "error" ? "text-danger"
      : tipo === "ok" ? "text-success fw-semibold" : "text-muted");
  }

  function formatos(tipo) {
    const F = Html5QrcodeSupportedFormats;
    return tipo === "qr"
      ? [F.QR_CODE, F.DATA_MATRIX, F.AZTEC]
      : [F.EAN_13, F.EAN_8, F.UPC_A, F.UPC_E, F.CODE_128, F.CODE_39, F.ITF, F.QR_CODE];
  }

  /* Entrega el código leído al campo y cierra el modal. */
  function entregar(texto) {
    campoActivo.value = String(texto).trim();
    campoActivo.dispatchEvent(new Event("change", { bubbles: true }));
    campoActivo.dispatchEvent(new Event("input", { bubbles: true }));
    aviso("Código leído: " + campoActivo.value, "ok");
    setTimeout(function () { modal.hide(); }, 400);
  }

  async function detenerCamara() {
    if (lectorCam) {
      const l = lectorCam;
      lectorCam = null;
      try { await l.stop(); } catch (e) { /* ya estaba detenido */ }
      try { l.clear(); } catch (e) { /* nada que limpiar */ }
    }
  }

  async function iniciarCamara() {
    if (lectorCam || !campoActivo) return;
    aviso("Iniciando cámara...");
    const l = new Html5Qrcode("lectorCamara",
      { formatsToSupport: formatos(campoActivo.dataset.escaner), verbose: false });
    lectorCam = l;
    try {
      await l.start({ facingMode: "environment" },
        { fps: 10, qrbox: { width: 260, height: 180 } },
        function (texto) { detenerCamara(); entregar(texto); });
      aviso("Centre el código dentro del recuadro.");
    } catch (err) {
      lectorCam = null;
      aviso("No se pudo abrir la cámara. Use «Subir imagen», digite el código o use el lector inalámbrico.", "error");
      cambiarModo("imagen");
    }
  }

  /* Lee un código a partir de un archivo de imagen (foto, captura de pantalla, etiqueta escaneada). */
  async function leerImagen(file) {
    if (!file || !campoActivo) return;
    if (!file.type || file.type.indexOf("image/") !== 0) {
      aviso("El archivo debe ser una imagen (JPG, PNG, WEBP, GIF...).", "error");
      return;
    }
    await detenerCamara();
    aviso("Analizando la imagen...");
    zonaImagen.classList.add("cargando");
    const lectorImg = new Html5Qrcode("lectorImagen",
      { formatsToSupport: formatos(campoActivo.dataset.escaner), verbose: false });
    try {
      const texto = await lectorImg.scanFile(file, true);
      entregar(texto);
    } catch (err) {
      aviso("No se encontró ningún código en la imagen. Pruebe con una foto más nítida, " +
            "de cerca, con el código completo y lo más derecho posible.", "error");
    } finally {
      zonaImagen.classList.remove("cargando");
      try { lectorImg.clear(); } catch (e) { /* nada que limpiar */ }
      archivo.value = "";
    }
  }

  function cambiarModo(modo) {
    modoActual = modo;
    botonesModo.forEach(function (b) { b.classList.toggle("active", b.dataset.modo === modo); });
    panelCamara.classList.toggle("d-none", modo !== "camara");
    panelImagen.classList.toggle("d-none", modo !== "imagen");
    if (modo === "camara") {
      iniciarCamara();
    } else {
      detenerCamara();
      aviso("Elija una foto donde se vea el código completo.");
    }
  }

  botonesModo.forEach(function (b) {
    b.addEventListener("click", function () { cambiarModo(b.dataset.modo); });
  });

  archivo.addEventListener("change", function () { leerImagen(archivo.files[0]); });

  /* Arrastrar y soltar una imagen sobre la zona. */
  ["dragenter", "dragover"].forEach(function (ev) {
    zonaImagen.addEventListener(ev, function (e) {
      e.preventDefault();
      zonaImagen.classList.add("encima");
    });
  });
  ["dragleave", "drop"].forEach(function (ev) {
    zonaImagen.addEventListener(ev, function (e) {
      e.preventDefault();
      zonaImagen.classList.remove("encima");
    });
  });
  zonaImagen.addEventListener("drop", function (e) {
    if (e.dataTransfer && e.dataTransfer.files.length) leerImagen(e.dataTransfer.files[0]);
  });

  /* Pegar una captura de pantalla con Ctrl+V mientras el modal está abierto. */
  modalEl.addEventListener("paste", function (e) {
    const items = (e.clipboardData || {}).items || [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image/") === 0) {
        cambiarModo("imagen");
        leerImagen(items[i].getAsFile());
        break;
      }
    }
  });

  modalEl.addEventListener("shown.bs.modal", function () {
    lectorImagenEl.innerHTML = "";
    cambiarModo(modoActual);
  });
  modalEl.addEventListener("hidden.bs.modal", function () {
    detenerCamara();
    lectorImagenEl.innerHTML = "";
  });

  /* Botones en cada campo marcado con data-escaner. */
  document.querySelectorAll("[data-escaner]").forEach(function (input) {
    const esQr = input.dataset.escaner === "qr";
    const grupo = document.createElement("div");
    grupo.className = "input-group campo-escaner";
    input.parentNode.insertBefore(grupo, input);
    grupo.appendChild(input);

    function agregarBoton(icono, titulo, modo, clase) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn " + clase;
      b.title = titulo;
      b.setAttribute("aria-label", titulo);
      b.innerHTML = '<i class="bi ' + icono + '"></i>';
      b.addEventListener("click", function () {
        campoActivo = input;
        modoActual = modo;
        modalEl.querySelector(".modal-title").innerHTML =
          '<i class="bi ' + (esQr ? "bi-qr-code" : "bi-upc-scan") + '"></i> Leer código ' +
          (esQr ? "QR" : "de barras");
        modal.show();
      });
      grupo.appendChild(b);
    }

    agregarBoton("bi-camera", "Escanear con la cámara", "camara", "btn-ism");
    agregarBoton("bi-image", "Subir una imagen del código", "imagen", "btn-ism-claro");

    if (input.dataset.buscarProducto) {
      const info = document.createElement("div");
      info.className = "form-text fs-6";
      grupo.after(info);
      const buscar = async function () {
        const codigo = input.value.trim();
        if (!codigo) { info.textContent = ""; return; }
        const r = await fetch(window.URL_BUSCAR_PRODUCTO + "?codigo=" + encodeURIComponent(codigo));
        const d = await r.json();
        info.className = "form-text fs-6 " + (d.encontrado ? "text-success" : "text-danger");
        info.textContent = d.encontrado
          ? "✔ " + d.nombre + " · " + d.cajas_por_pallet + " cajas por pallet"
          : "✖ " + d.mensaje;
      };
      input.addEventListener("change", buscar);
      input.addEventListener("blur", buscar);
    }
  });
})();
