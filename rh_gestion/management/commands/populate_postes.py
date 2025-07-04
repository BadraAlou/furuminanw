from django.core.management.base import BaseCommand
from rh_gestion.models import Poste


class Command(BaseCommand):
    help = 'Pré-remplit la base de données avec les postes prédéfinis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime tous les postes existants avant de créer les nouveaux',
        )

    def handle(self, *args, **options):
        # Données des postes prédéfinis
        postes_data = [
            {
                'nom': 'Gérant',
                'departement': 'direction',
                'description': 'Responsable de la gestion générale de l\'entreprise, supervision des opérations et prise de décisions stratégiques.'
            },
            {
                'nom': 'Responsable',
                'departement': 'direction',
                'description': 'Responsable adjoint, assistance à la direction générale et coordination des équipes.'
            },
            {
                'nom': 'Responsable Administratif',
                'departement': 'administration',
                'description': 'Gestion des procédures administratives, coordination des services et supervision du personnel administratif.'
            },
            {
                'nom': 'Financier',
                'departement': 'comptabilite',
                'description': 'Gestion de la comptabilité, des finances, du budget et des déclarations fiscales de l\'entreprise.'
            },
            {
                'nom': 'Responsable Webmaster',
                'departement': 'it',
                'description': 'Développement et maintenance du site web, gestion des systèmes informatiques et support technique.'
            },
            {
                'nom': 'Responsable Commercial',
                'departement': 'commercial',
                'description': 'Développement des ventes, gestion de la clientèle et stratégies commerciales.'
            },
            {
                'nom': 'Marketing',
                'departement': 'marketing',
                'description': 'Élaboration et mise en œuvre des stratégies marketing, promotion des produits et analyse de marché.'
            },
            {
                'nom': 'Responsable Communication',
                'departement': 'communication',
                'description': 'Gestion de la communication interne et externe, relations publiques et image de marque.'
            },
            {
                'nom': 'Chargé de la Clientèle',
                'departement': 'service_client',
                'description': 'Accueil et conseil clientèle, traitement des réclamations et suivi de la satisfaction client.'
            },
            {
                'nom': 'Chauffeur',
                'departement': 'logistique',
                'description': 'Transport des marchandises et du personnel, livraisons et maintenance des véhicules.'
            },
            {
                'nom': 'Agent de Nettoyage',
                'departement': 'services_generaux',
                'description': 'Entretien et nettoyage des locaux, maintenance de la propreté des espaces de travail.'
            },
            {
                'nom': 'Agent de Sécurité',
                'departement': 'securite',
                'description': 'Surveillance des locaux, contrôle des accès et sécurité du personnel et des biens.'
            }
        ]

        if options['clear']:
            # Supprimer tous les postes existants
            deleted_count = Poste.objects.all().count()
            Poste.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'{deleted_count} poste(s) existant(s) supprimé(s)')
            )

        # Créer les nouveaux postes
        created_count = 0
        updated_count = 0

        for poste_data in postes_data:
            poste, created = Poste.objects.get_or_create(
                nom=poste_data['nom'],
                departement=poste_data['departement'],
                defaults={'description': poste_data['description']}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Poste créé: {poste.nom} - {poste.get_departement_display()}')
                )
            else:
                # Mettre à jour la description si elle a changé
                if poste.description != poste_data['description']:
                    poste.description = poste_data['description']
                    poste.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Poste mis à jour: {poste.nom} - {poste.get_departement_display()}')
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(f'→ Poste existant: {poste.nom} - {poste.get_departement_display()}')
                    )

        # Résumé
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✓ {created_count} nouveau(x) poste(s) créé(s)')
        )
        if updated_count > 0:
            self.stdout.write(
                self.style.WARNING(f'↻ {updated_count} poste(s) mis à jour')
            )

        total_postes = Poste.objects.count()
        self.stdout.write(
            self.style.HTTP_INFO(f'📊 Total des postes en base: {total_postes}')
        )

        # Afficher les statistiques par département
        self.stdout.write('\n📈 Répartition par département:')
        for dept_code, dept_name in Poste.DEPARTEMENTS_CHOICES:
            count = Poste.objects.filter(departement=dept_code).count()
            if count > 0:
                self.stdout.write(f'   • {dept_name}: {count} poste(s)')

        self.stdout.write('\n🎉 Initialisation des postes terminée avec succès!')