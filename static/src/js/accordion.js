// Script para el acordeón mejorado
document.addEventListener('DOMContentLoaded', function() {
  const accordionButtons = document.querySelectorAll('[data-accordion-target]');
  
  accordionButtons.forEach(button => {
      button.addEventListener('click', function() {
          const targetId = this.getAttribute('data-accordion-target');
          const target = document.querySelector(targetId);
          const icon = this.querySelector('[data-accordion-icon]');
          
          // Animación suave
          if (target.classList.contains('hidden')) {
              target.classList.remove('hidden');
              target.style.maxHeight = '0';
              target.style.overflow = 'hidden';
              setTimeout(() => {
                  target.style.maxHeight = target.scrollHeight + 'px';
                  setTimeout(() => {
                      target.style.maxHeight = 'none';
                  }, 300);
              }, 10);
          } else {
              target.style.maxHeight = target.scrollHeight + 'px';
              setTimeout(() => {
                  target.style.maxHeight = '0';
                  setTimeout(() => {
                      target.classList.add('hidden');
                      target.style.maxHeight = '';
                  }, 300);
              }, 10);
          }
          
          // Rotar icono
          icon.style.transform = target.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
          this.setAttribute('aria-expanded', !target.classList.contains('hidden'));
      });
  });
});
