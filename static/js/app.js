'use strict';

document.addEventListener('DOMContentLoaded', function () {
    var logoutForm = document.querySelector('.navbar-account form');
    if (logoutForm) {
        logoutForm.addEventListener('submit', function (event) {
            if (!window.confirm('Are you sure you want to sign out?')) {
                event.preventDefault();
            }
        });
    }

    var sidebar = document.getElementById('main-sidebar');
    var toggleButton = document.querySelector('.sidebar-toggle');

    if (!sidebar || !toggleButton) {
        return;
    }

    var isCollapsed = sessionStorage.getItem('sidebar-collapsed') === 'true';
    sidebar.classList.toggle('sidebar-collapsed', isCollapsed);
    toggleButton.setAttribute('aria-expanded', String(!isCollapsed));
    toggleButton.setAttribute(
        'aria-label',
        isCollapsed ? 'Open navigation' : 'Close navigation'
    );

    toggleButton.addEventListener('click', function () {
        var isCollapsed = sidebar.classList.toggle('sidebar-collapsed');
        sessionStorage.setItem('sidebar-collapsed', String(isCollapsed));
        toggleButton.setAttribute('aria-expanded', String(!isCollapsed));
        toggleButton.setAttribute(
            'aria-label',
            isCollapsed ? 'Open navigation' : 'Close navigation'
        );
    });
});
