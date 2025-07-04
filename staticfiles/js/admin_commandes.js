document.addEventListener('DOMContentLoaded', function() {
    // Ajouter une confirmation avant l'archivage
    const archiveAction = document.querySelector('select[name="action"]');
    if (archiveAction) {
        archiveAction.addEventListener('change', function(e) {
            if (e.target.value === 'archiver_commandes') {
                const confirmation = confirm('Êtes-vous sûr de vouloir archiver les commandes sélectionnées ?');
                if (!confirmation) {
                    e.target.value = '';
                }
            }
        });
    }

    // Ajouter une animation lors du changement de statut
    const statutSelect = document.querySelector('select[name="statut"]');
    if (statutSelect) {
        statutSelect.addEventListener('change', function(e) {
            e.target.style.transition = 'all 0.3s ease';
            e.target.style.transform = 'scale(1.05)';
            setTimeout(() => {
                e.target.style.transform = 'scale(1)';
            }, 300);
        });
    }
});