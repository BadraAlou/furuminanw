from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from utilisateurs.models import Profil
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Supprime définitivement les comptes dont le délai de grâce de 30 jours est expiré'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les comptes qui seraient supprimés sans les supprimer réellement',
        )
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Envoie des rappels aux comptes qui seront supprimés dans 7, 3 et 1 jour(s)',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']
        send_reminders = options['send_reminders']

        # Trouver les comptes à supprimer (délai de 30 jours expiré)
        date_limite_suppression = now - timedelta(days=30)
        profils_a_supprimer = Profil.objects.filter(
            suppression_demandee=True,
            date_demande_suppression__lte=date_limite_suppression
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'MODE DRY-RUN: {profils_a_supprimer.count()} compte(s) seraient supprimé(s)')
            )
            for profil in profils_a_supprimer:
                self.stdout.write(f'  - {profil.utilisateur.username} ({profil.utilisateur.email})')
        else:
            # Supprimer définitivement les comptes
            comptes_supprimes = 0
            for profil in profils_a_supprimer:
                username = profil.utilisateur.username
                email = profil.utilisateur.email

                # Supprimer l'utilisateur (cascade supprimera le profil)
                profil.utilisateur.delete()
                comptes_supprimes += 1

                self.stdout.write(
                    self.style.SUCCESS(f'Compte supprimé: {username} ({email})')
                )

            self.stdout.write(
                self.style.SUCCESS(f'{comptes_supprimes} compte(s) supprimé(s) définitivement')
            )

        # Envoyer des rappels si demandé
        if send_reminders:
            self.envoyer_rappels(now)

    def envoyer_rappels(self, now):
        """Envoie des rappels aux comptes qui seront supprimés bientôt"""
        rappels_envoyes = 0

        # Rappels pour 7, 3 et 1 jour(s) avant suppression
        for jours in [7, 3, 1]:
            date_rappel = now - timedelta(days=30 - jours)

            profils_rappel = Profil.objects.filter(
                suppression_demandee=True,
                date_demande_suppression__date=date_rappel.date()
            )

            for profil in profils_rappel:
                try:
                    profil.envoyer_rappel_suppression(jours)
                    rappels_envoyes += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Rappel envoyé à {profil.utilisateur.email} ({jours} jour(s) restant(s))'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Erreur lors de l\'envoi du rappel à {profil.utilisateur.email}: {e}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f'{rappels_envoyes} rappel(s) envoyé(s)')
        )