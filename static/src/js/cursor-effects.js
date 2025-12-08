// Efecto de cursor personalizado
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si el elemento cursor follower existe o crearlo
    let cursorFollower = document.querySelector('.cursor-follower');
    
    if (!cursorFollower) {
        // Crear el elemento del cursor personalizado
        cursorFollower = document.createElement('div');
        cursorFollower.classList.add('cursor-follower');
        document.body.appendChild(cursorFollower);
    }
    
    // Establecer posición inicial
    cursorFollower.style.opacity = '0.3';
    cursorFollower.style.transform = 'translate(-50%, -50%)';
    
    // Seguir el cursor
    document.addEventListener('mousemove', (e) => {
        cursorFollower.style.left = e.clientX + 'px';
        cursorFollower.style.top = e.clientY + 'px';
    });
    
    // Efectos en elementos interactivos
    const interactiveElements = document.querySelectorAll('a, button, input, textarea, select, .interactive, [role="button"]');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursorFollower.style.transform = 'translate(-50%, -50%) scale(1.5)';
            cursorFollower.style.opacity = '0.2';
            cursorFollower.style.backgroundColor = '#4895ef'; // accent color
        });
        
        el.addEventListener('mouseleave', () => {
            cursorFollower.style.transform = 'translate(-50%, -50%) scale(1)';
            cursorFollower.style.opacity = '0.3';
            cursorFollower.style.backgroundColor = '#4361ee'; // primary color
        });
    });
    
    // Efectos de clic
    document.addEventListener('mousedown', () => {
        cursorFollower.style.transform = 'translate(-50%, -50%) scale(0.8)';
    });
    
    document.addEventListener('mouseup', () => {
        cursorFollower.style.transform = 'translate(-50%, -50%) scale(1)';
    });
    
    // Ocultar el cursor cuando sale de la ventana
    document.addEventListener('mouseleave', () => {
        cursorFollower.style.opacity = '0';
    });
    
    document.addEventListener('mouseenter', () => {
        cursorFollower.style.opacity = '0.3';
    });
});
