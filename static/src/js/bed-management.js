// Scripts para la gestión de camas
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar modal de liberación
  const liberarModal = new Modal(document.getElementById('liberarModal'), {
    backdrop: 'static',
    keyboard: false,
    focus: true
  });
  
  let currentForm = null;

  window.confirmarLiberacion = (formId) => {
    currentForm = document.getElementById(formId);
    liberarModal.show();
  }

  document.getElementById('confirmLiberar').addEventListener('click', async () => {
    if(currentForm) {
      try {
        // Enviar el formulario normalmente
        currentForm.submit();
        
        // Esperar un momento para que el servidor procese la liberación
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Recargar solo la sección de camas afectada
        const camaId = currentForm.action.split('/').pop();
        const camaContainer = document.querySelector(`[data-cama-id="${camaId}"]`).closest('.grid');
        const response = await fetch(window.location.href);
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const newCamaContainer = doc.querySelector(`[data-cama-id="${camaId}"]`).closest('.grid');
        camaContainer.innerHTML = newCamaContainer.innerHTML;
        
      } catch (error) {
        console.error('Error:', error);
        // Si hay error, recargar toda la página
        window.location.reload();
      } finally {
        const liberarModal = document.getElementById('liberarModal');
        liberarModal.classList.add('hidden');
      }
    }
  });

  // Animación al hacer hover en botones
  document.querySelectorAll('.btn-hover').forEach(element => {
    element.addEventListener('mouseenter', () => {
      element.classList.add('animate__animated', 'animate__pulse');
    });
    
    element.addEventListener('animationend', () => {
      element.classList.remove('animate__animated', 'animate__pulse');
    });
  });
  
  // Efecto de scroll con Intersection Observer (más moderno)
  const animateOnScroll = function() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate__animated', 'animate__fadeInUp');
          observer.unobserve(entry.target);
        }
      });
    }, {
      root: null,
      threshold: 0.1,
      rootMargin: '0px'
    });
    
    document.querySelectorAll('.scroll-animate').forEach(element => {
      observer.observe(element);
    });
  };
  
  animateOnScroll();
});
