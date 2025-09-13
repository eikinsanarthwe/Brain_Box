// Toggle sidebar on mobile
document.getElementById('sidebarToggle').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('show');
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    
    if (window.innerWidth < 768 && sidebar.classList.contains('show') && 
        !sidebar.contains(event.target) && event.target !== toggleBtn) {
        sidebar.classList.remove('show');
    }
});