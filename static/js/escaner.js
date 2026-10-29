/* Lectura de códigos con la cámara de la tablet (html5-qrcode 2.3.8).
   Todo campo con data-escaner="barras" o "qr" recibe un botón de cámara; el lector inalámbrico
   opcional funciona igual porque escribe en el campo como un teclado. */
(function () {
  "use strict";
  let lector = null;
  let campoActivo = null;
  const modalEl = document.getElementById("modalEscaner");
  if (!modalEl || typeof Html5Qrcode === "undefined") return;
  const modal = new bootstrap.Modal(modalEl);
  const estado = document.getElementById("estadoEscaner");

  function formatos(tipo) {
    const F = Html5QrcodeSupportedFormats;
    return tipo === "qr" ? [F.QR_CODE] : [F.EAN_13, F.EAN_8, F.UPC_A, F.UPC_E, F.CODE_128, F.CODE_39, F.ITF];
  }

  async function detener() {
    if (lector) {
      try { await lector.stop(); } catch (e) { /* ya detenido */ }
      try { lector.clear(); } catch (e) { /* nada que limpiar */ }
      lector = null;
    }
  }

  modalEl.addEventListener("shown.bs.modal", async function () {
    estado.textContent = "Iniciando cámara...";
    lector = new Html5Qrcode("lectorCamara", { formatsToSupport: formatos(campoActivo.dataset.escaner), verbose: false });
    try {
      await lector.start({ facingMode: "environment" }, { fps: 10, qrbox: { width: 260, height: 180 } },
        function (texto) {
          campoActivo.value = texto.trim();
          campoActivo.dispatchEvent(new Event("change", { bubbles: true }));
          modal.hide();
        });
      estado.textContent = "Centre el código dentro del recuadro.";
    } catch (err) {
      estado.textContent = "No se pudo abrir la cámara. Puede digitar el código o usar el lector inalámbrico.";
    }
  });
  modalEl.addEventListener("hidden.bs.modal", detener);

  document.querySelectorAll("[data-escaner]").forEach(function (input) {
    const grupo = document.createElement("div");
    grupo.className = "input-group campo-escaner";
    input.parentNode.insertBefore(grupo, input);
    grupo.appendChild(input);
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "btn btn-ism";
    boton.title = "Escanear con la cámara";
    boton.setAttribute("aria-label", "Escanear con la cámara");
    boton.innerHTML = '<i class="bi bi-camera"></i>';
    boton.addEventListener("click", function () { campoActivo = input; modal.show(); });
    grupo.appendChild(boton);

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
        info.textContent = d.encontrado ? "✔ " + d.nombre + " · " + d.cajas_por_pallet + " cajas por pallet" : "✖ " + d.mensaje;
      };
      input.addEventListener("change", buscar);
      input.addEventListener("blur", buscar);
    }
  });
})();
