from decimal import Decimal
from produits.models import Pack, Option


class Panier:
    def __init__(self, request):
        """
        Initialise le panier
        """
        self.session = request.session
        panier = self.session.get('panier')
        if not panier:
            # Sauvegarder un panier vide dans la session
            panier = self.session['panier'] = {}
        self.panier = panier

    def ajouter(self, pack_id, quantite=1, options=None):
        """
        Ajouter un produit au panier ou mettre à jour sa quantité
        """
        pack_id = str(pack_id)

        if options is None:
            options = []

        if pack_id not in self.panier:
            self.panier[pack_id] = {'quantite': quantite, 'options': options}
        else:
            self.panier[pack_id]['quantite'] += quantite

        self.sauvegarder()

    def sauvegarder(self):
        # Marquer la session comme "modifiée" pour être sûr qu'elle est sauvegardée
        self.session.modified = True

    def supprimer(self, pack_id):
        """
        Supprimer un produit du panier
        """
        pack_id = str(pack_id)

        if pack_id in self.panier:
            del self.panier[pack_id]
            self.sauvegarder()

    def modifier_quantite(self, pack_id, quantite):
        """
        Modifier la quantité d'un produit
        """
        pack_id = str(pack_id)

        if pack_id in self.panier and quantite > 0:
            self.panier[pack_id]['quantite'] = quantite
            self.sauvegarder()

    def get_produits(self):
        """
        Retourner tous les produits dans le panier
        """
        pack_ids = self.panier.keys()

        # Récupérer les objets produits et les ajouter au panier
        packs = Pack.objects.filter(id__in=pack_ids)

        for pack in packs:
            self.panier[str(pack.id)]['pack'] = pack

        for item in self.panier.values():
            item['prix'] = Decimal(item['pack'].prix)
            item['prix_total'] = item['prix'] * item['quantite']

            # Ajouter les informations sur les options
            if 'options' in item and item['options']:
                options_ids = item['options']
                options = Option.objects.filter(id__in=options_ids)
                item['options_details'] = options

        return self.panier.values()

    def get_nombre_produits(self):
        """
        Calculer le nombre total de produits dans le panier
        """
        return sum(item['quantite'] for item in self.panier.values())

    def get_total(self):
        """
        Calculer le prix total du panier
        """
        return sum(Decimal(item['pack'].prix) * item['quantite'] for item in self.get_produits())

    def vider(self):
        """
        Vider le panier
        """
        self.session['panier'] = {}
        self.sauvegarder()