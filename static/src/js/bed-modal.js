// Funciones para el modal de derivación
window.mostrarDerivacionModal = (idCamaOrigen) => {
  const modal = document.getElementById('derivarModal');
  const modalContent = document.getElementById('derivarModalContent');
  const inputOrigen = document.getElementById('idcama_origen');
  
  inputOrigen.value = idCamaOrigen;
  modal.classList.remove('hidden');
  
  setTimeout(() => {
    modalContent.classList.remove('scale-95', 'opacity-0');
    modalContent.classList.add('scale-100', 'opacity-100');
  }, 10);
};

window.cerrarDerivacionModal = () => {
  const modal = document.getElementById('derivarModal');
  const modalContent = document.getElementById('derivarModalContent');
  
  modalContent.classList.remove('scale-100', 'opacity-100');
  modalContent.classList.add('scale-95', 'opacity-0');
  
  modal.classList.add('hidden');
};
