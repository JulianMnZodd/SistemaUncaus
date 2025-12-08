// Animaciones generales para elementos de la interfaz
document.addEventListener('DOMContentLoaded', function() {
  // Animación al hacer hover en botones
  document.querySelectorAll('.btn-hover').forEach(element => {
    element.addEventListener('mouseenter', () => {
      element.classList.add('animate__animated', 'animate__pulse');
    });
    
    element.addEventListener('animationend', () => {
      element.classList.remove('animate__animated', 'animate__pulse');
    });
  });
  
  // Efecto de scroll con Intersection Observer
  const animateOnScroll = function() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate__animated', 'animate__fadeInUp');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1
    });
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
      observer.observe(el);
    });
  };
  
  animateOnScroll();
});
