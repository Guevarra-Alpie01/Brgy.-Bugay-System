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
});
