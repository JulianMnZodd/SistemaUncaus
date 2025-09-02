// Animación para los elementos del sidebar
document.addEventListener('DOMContentLoaded', function() {
    // Animación para los elementos del sidebar
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.addEventListener('mouseenter', () => {
            const icon = item.querySelector('.sidebar-icon');
            icon.classList.add('animate__animated', 'animate__fadeInRight');
        });
        
        item.addEventListener('mouseleave', () => {
            const icon = item.querySelector('.sidebar-icon');
            icon.classList.remove('animate__animated', 'animate__fadeInRight');
        });
    });
    
    // Mejorar la experiencia del dropdown de usuario
    const userButton = document.querySelector('[data-dropdown-toggle="dropdown-user"]');
    const userDropdown = document.getElementById('dropdown-user');
    
    if (userButton && userDropdown) {
        userButton.addEventListener('click', () => {
            userDropdown.classList.toggle('hidden');
            userDropdown.classList.toggle('animate__animated', 'animate__fadeIn');
        });
    }
});
