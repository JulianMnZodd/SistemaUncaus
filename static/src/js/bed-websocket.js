document.addEventListener("DOMContentLoaded", function() {
  let socket;
  const connectWebSocket = () => {
    socket = new WebSocket('ws://' + window.location.host + '/ws/camas/');

    socket.onopen = function(e) {
      console.log('WebSocket conectado');
    };

    socket.onmessage = function(e) {
      const data = JSON.parse(e.data);
      console.log('Mensaje recibido:', data);
      
      // Actualizar la interfaz según el tipo de mensaje
      if (data.type === 'cama_actualizada') {
        actualizarCamaUI(data);
      }
    };

    socket.onclose = function(e) {
      console.log('WebSocket desconectado. Intentando reconectar en 5 segundos...');
      setTimeout(connectWebSocket, 5000);
    };

    socket.onerror = function(err) {
      console.error('Error de WebSocket:', err);
      socket.close();
    };
  };

  connectWebSocket();

  // Función para actualizar la UI cuando se recibe una actualización
  const actualizarCamaUI = (data) => {
    const camaContainer = document.querySelector(`[data-cama-id="${data.idcama}"]`);
    if (!camaContainer) return;
    
    // Actualizar el estado de la cama
    const estadoElement = camaContainer.querySelector('.status-badge');
    if (estadoElement) {
      estadoElement.className = 'status-badge';
      
      if (data.estado === 'L') {
        estadoElement.classList.add('bg-green-500');
        estadoElement.textContent = 'Libre';
      } else if (data.estado === 'O') {
        estadoElement.classList.add('bg-red-500');
        estadoElement.textContent = 'Ocupada';
      } else if (data.estado === 'R') {
        estadoElement.classList.add('bg-yellow-500');
        estadoElement.textContent = 'Reservada';
      } else if (data.estado === 'M') {
        estadoElement.classList.add('bg-gray-500');
        estadoElement.textContent = 'Mantenimiento';
      } else if (data.estado === 'B') {
        estadoElement.classList.add('bg-purple-500');
        estadoElement.textContent = 'Bloqueada';
      }
    }
    
    // Actualizar la imagen de la cama
    const camaImage = camaContainer.querySelector('.bed-image');
    if (camaImage) {
      if (data.estado === 'L') {
        camaImage.src = '/static/src/img/cama-libre.png';
      } else if (data.estado === 'O') {
        camaImage.src = '/static/src/img/cama-ocupada.png';
      } else if (data.estado === 'R') {
        camaImage.src = '/static/src/img/cama-reservada.png';
      } else if (data.estado === 'M') {
        camaImage.src = '/static/src/img/cama-mantenimiento.png';
      } else if (data.estado === 'B') {
        camaImage.src = '/static/src/img/cama-bloqueada.png';
      }
    }
    
    // Actualizar la información del paciente
    const pacienteElement = camaContainer.querySelector('.patient-info');
    if (pacienteElement) {
      if (data.estado === 'L') {
        pacienteElement.innerHTML = '';
      } else if (data.estado === 'O' && data.paciente_id) {
        if (pacienteElement.innerHTML === '') {
          const pacienteDiv = document.createElement('div');
          pacienteDiv.className = 'mt-2 text-sm';
          pacienteDiv.innerHTML = `
            <a href="/detalle_paciente/${data.paciente_id}" 
               class="hover:text-blue-600 transition-colors flex items-center justify-center space-x-1">
               <svg class="compact-user-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
               </svg>
               <span>${data.paciente_nombre}</span>
            </a>
          `;
          
          const estadoContainer = camaContainer.querySelector('.text-center.space-y-2');
          if (estadoContainer) {
            estadoContainer.appendChild(pacienteDiv);
          }
        } else {
          pacienteElement.innerHTML = `
            <a href="/detalle_paciente/${data.paciente_id}" 
               class="hover:text-blue-600 transition-colors flex items-center justify-center space-x-1">
               <svg class="compact-user-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
               </svg>
               <span>${data.paciente_nombre}</span>
            </a>
          `;
        }
      }
    
      const actionsContainer = camaContainer.querySelector(`#actions-${data.idcama}`);
      if (actionsContainer) {
        let newActions = '';
        if (data.estado === 'L') {
          newActions = `
            <a href="/asignar_cama/${data.idcama}" 
              class="w-full text-white bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 rounded-lg btn-hover text-xs px-3 py-2 text-center inline-flex items-center justify-center transition-all shadow-md hover:shadow-lg">
              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              <span>Asignar</span>
            </a>
            <a href="/reservar_cama/${data.idcama}" 
              class="w-full text-white bg-gradient-to-r from-yellow-500 to-yellow-400 hover:from-yellow-600 hover:to-yellow-500 rounded-lg btn-hover text-xs px-3 py-2 text-center inline-flex items-center justify-center transition-all shadow-md hover:shadow-lg">
              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <span>Reservar</span>
            </a>`;
        } else if (data.estado === 'R') {
          newActions = `
            <a href="/ver_reserva/${data.idcama}" 
              class="w-full text-white bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 rounded-lg btn-hover text-xs px-3 py-2 text-center inline-flex items-center justify-center transition-all shadow-md hover:shadow-lg">
              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
              <span>Ver Reserva</span>
            </a>`;
        } else if (data.estado === 'O') {
          newActions = `
            <form class="inline w-full" method="POST" action="/liberar_cama/${data.idcama}" id="formLiberar-${data.idcama}">
              <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">
              <button type="button" 
                      onclick="confirmarLiberacion('formLiberar-${data.idcama}')"
                      class="w-full text-white bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-800 hover:to-gray-700 rounded-lg btn-hover text-xs px-3 py-2 text-center inline-flex items-center justify-center transition-all shadow-md hover:shadow-lg">
                  <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                  <span>Liberar</span>
              </button>
            </form>
            <a href="#" 
              onclick="mostrarDerivacionModal(${data.idcama})"
              class="w-full text-white bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 rounded-lg btn-hover text-xs px-3 py-2 text-center inline-flex items-center justify-center transition-all shadow-md hover:shadow-lg">
              <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
              </svg>
              <span>Derivar</span>
            </a>`;
        }
        actionsContainer.innerHTML = newActions;
      }
    }
  };

  const getCSRFToken = () => {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  };
});
