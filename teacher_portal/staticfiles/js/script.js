// ===== MOBILE MENU TOGGLE =====
document.addEventListener('DOMContentLoaded', function() {
    // More robust sidebar toggle
    const sidebarToggle = document.querySelector('#sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-toggled');
            sidebar.classList.toggle('toggled');
            
            localStorage.setItem('sidebarState', 
                sidebar.classList.contains('toggled') ? 'toggled' : '');
        });

        // Restore sidebar state
        if (localStorage.getItem('sidebarState') === 'toggled') {
            document.body.classList.add('sidebar-toggled');
            sidebar.classList.add('toggled');
        }
    }

    // ===== DUE DATE COUNTDOWN =====
    function updateDueDates() {
        document.querySelectorAll('[data-due-date]').forEach(el => {
            try {
                const dueDate = new Date(el.dataset.dueDate);
                if (isNaN(dueDate.getTime())) return;
                
                const now = new Date();
                const diff = dueDate - now;
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                
                // Clear previous content
                while (el.firstChild) {
                    el.removeChild(el.firstChild);
                }
                
                const icon = document.createElement('i');
                const text = document.createElement('span');
                
                // Reset classes
                el.className = 'due-date-countdown';
                
                if (diff < 0) {
                    el.classList.add('past-due');
                    icon.className = 'fas fa-exclamation-circle me-2';
                    text.textContent = `${Math.abs(days)} day${Math.abs(days) !== 1 ? 's' : ''} overdue`;
                } else {
                    icon.className = 'fas fa-clock me-2';
                    text.textContent = `${days} day${days !== 1 ? 's' : ''} remaining`;
                    
                    if (days < 3) {
                        el.classList.add('urgent');
                    } else {
                        el.classList.add('normal');
                    }
                }
                
                el.appendChild(icon);
                el.appendChild(text);
            } catch (e) {
                console.error('Error processing due date:', e);
            }
        });
    }

    // Initialize if countdown elements exist
    if (document.querySelector('[data-due-date]')) {
        updateDueDates();
        setInterval(updateDueDates, 60000);
    }

    // ===== AUTO-RESIZE TEXTAREAS =====
    function autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }

    const textareas = document.querySelectorAll('textarea');
    if (textareas.length > 0) {
        textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                autoResizeTextarea(this);
            });
            // Initial resize
            autoResizeTextarea(textarea);
        });
    }

    // ===== DROPDOWN MENUS =====
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdown = this.closest('.dropdown');
            dropdown.classList.toggle('show');
            
            // Close other open dropdowns
            document.querySelectorAll('.dropdown.show').forEach(openDropdown => {
                if (openDropdown !== dropdown) {
                    openDropdown.classList.remove('show');
                }
            });
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown.show').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
});