/* ============ MAIN JS ============ */

// ---- Theme Toggle ----
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    html.setAttribute('data-bs-theme', theme); // Bootstrap 5 native dark mode
    localStorage.setItem('canteen-theme', theme);
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark'
            ? '<i class="bi bi-moon-stars-fill"></i>'
            : '<i class="bi bi-sun-fill"></i>';
    }
}

// Load saved theme
const savedTheme = localStorage.getItem('canteen-theme') || 'dark';
setTheme(savedTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const current = html.getAttribute('data-theme');
        setTheme(current === 'dark' ? 'light' : 'dark');
    });
}

// ---- Sidebar Toggle ----
const sidebar = document.getElementById('sidebar');
const mainWrapper = document.getElementById('mainWrapper');
const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
const sidebarToggle = document.getElementById('sidebarToggle');

let isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
let isMobile = window.innerWidth < 992;

function updateSidebar() {
    isMobile = window.innerWidth < 992;
    if (isMobile) {
        sidebar?.classList.remove('collapsed');
        mainWrapper?.classList.remove('sidebar-collapsed');
    } else {
        if (isCollapsed) {
            sidebar?.classList.add('collapsed');
            mainWrapper?.classList.add('sidebar-collapsed');
        } else {
            sidebar?.classList.remove('collapsed');
            mainWrapper?.classList.remove('sidebar-collapsed');
        }
    }
}

sidebarToggleBtn?.addEventListener('click', () => {
    if (isMobile) {
        sidebar?.classList.toggle('mobile-open');
        document.querySelector('.sidebar-overlay')?.classList.toggle('active');
    } else {
        isCollapsed = !isCollapsed;
        localStorage.setItem('sidebar-collapsed', isCollapsed);
        updateSidebar();
    }
});

sidebarToggle?.addEventListener('click', () => {
    if (isMobile) {
        sidebar?.classList.remove('mobile-open');
        document.querySelector('.sidebar-overlay')?.classList.remove('active');
    }
});

// Create overlay for mobile
const overlay = document.createElement('div');
overlay.className = 'sidebar-overlay';
overlay.addEventListener('click', () => {
    sidebar?.classList.remove('mobile-open');
    overlay.classList.remove('active');
});
document.body.appendChild(overlay);

window.addEventListener('resize', updateSidebar);
updateSidebar();

// ---- Live Clock ----
const timeEl = document.getElementById('topbarTime');
function updateTime() {
    if (!timeEl) return;
    const now = new Date();
    timeEl.textContent = now.toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}
updateTime();
setInterval(updateTime, 1000);

// ---- Auto-dismiss alerts ----
document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert?.close();
    }, 5000);
});

// ---- Utils ----
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Expose globally
window.formatCurrency = formatCurrency;
window.getCookie = getCookie;
