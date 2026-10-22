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

    var panelToggles = Array.from(document.querySelectorAll('[data-panel-toggle]'));
    function closePanels() {
        panelToggles.forEach(function (toggle) {
            var panel = document.getElementById(toggle.dataset.panelToggle);
            if (panel) {
                panel.hidden = true;
            }
            toggle.setAttribute('aria-expanded', 'false');
            if (toggle.dataset.panelToggle === 'upload-form') {
                toggle.setAttribute('aria-label', 'Show upload form');
            } else {
                toggle.setAttribute('aria-label', 'Show uploaded files');
            }
        });
    }

    panelToggles.forEach(function (toggle) {
        toggle.addEventListener('click', function () {
            var panel = document.getElementById(toggle.dataset.panelToggle);
            if (!panel) {
                return;
            }
            var wasExpanded = toggle.getAttribute('aria-expanded') === 'true';
            closePanels();
            if (!wasExpanded) {
                panel.hidden = false;
                toggle.setAttribute('aria-expanded', 'true');
                toggle.setAttribute(
                    'aria-label',
                    toggle.dataset.panelToggle === 'upload-form'
                        ? 'Hide upload form'
                        : 'Hide uploaded files',
                );
                if (toggle.dataset.panelToggle === 'upload-form') {
                    var categorySelect = panel.querySelector('select');
                    if (categorySelect) {
                        categorySelect.focus();
                    }
                }
            }
        });
    });

    if (panelToggles.length) {
        document.addEventListener('click', function (event) {
            if (!event.target.closest('.quick-actions')) {
                closePanels();
            }
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                var expandedToggle = panelToggles.find(function (toggle) {
                    return toggle.getAttribute('aria-expanded') === 'true';
                });
                if (expandedToggle) {
                    closePanels();
                    expandedToggle.focus();
                }
            }
        });
    }

    document.querySelectorAll('[data-delete-upload]').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!window.confirm(
                'Permanently delete "' + form.dataset.documentName + '"?'
            )) {
                event.preventDefault();
            }
        });
    });

    var search = document.getElementById('document-search');
    var typeFilter = document.getElementById('document-type-filter');
    var noResults = document.getElementById('no-document-results');
    var emptyFilesToast = document.querySelector('.empty-files-toast');
    var emptyFilesToastTimeout;
    var emptyFilesToastHideTimeout;

    function showEmptyFilesToast() {
        if (!emptyFilesToast) {
            return;
        }
        window.clearTimeout(emptyFilesToastTimeout);
        window.clearTimeout(emptyFilesToastHideTimeout);
        emptyFilesToast.hidden = false;
        emptyFilesToast.classList.remove('is-visible');
        void emptyFilesToast.offsetWidth;
        emptyFilesToast.classList.add('is-visible');
        emptyFilesToastTimeout = window.setTimeout(function () {
            emptyFilesToast.classList.remove('is-visible');
            emptyFilesToastHideTimeout = window.setTimeout(function () {
                emptyFilesToast.hidden = true;
            }, 180);
        }, 2000);
    }

    if (emptyFilesToast && !emptyFilesToast.hidden) {
        showEmptyFilesToast();
    }

    document.querySelectorAll('[data-empty-service]').forEach(function (button) {
        button.addEventListener('click', showEmptyFilesToast);
    });

    function filterDocuments() {
        if (!search || !typeFilter) {
            return;
        }
        var searchValue = search.value.trim().toLowerCase();
        var selectedType = typeFilter.value;
        var visibleCount = 0;
        document.querySelectorAll('.document-file-card').forEach(function (card) {
            var nameMatches = card.dataset.documentName.indexOf(searchValue) !== -1;
            var kind = card.dataset.officeKind === 'yes'
                ? (card.dataset.documentType === 'XLS' ||
                    card.dataset.documentType === 'XLSX' ||
                    card.dataset.documentType === 'XLSM' ? 'excel' : 'word')
                : '';
            var typeMatches = !selectedType || kind === selectedType;
            card.hidden = !nameMatches || !typeMatches;
            if (!card.hidden) {
                visibleCount += 1;
            }
        });
        if (noResults) {
            noResults.hidden = visibleCount !== 0;
        }
    }

    if (search) {
        search.addEventListener('input', filterDocuments);
    }
    if (typeFilter) {
        typeFilter.addEventListener('change', filterDocuments);
    }

});
