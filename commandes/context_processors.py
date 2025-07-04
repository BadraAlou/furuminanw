from .panier import Panier

def panier_processor(request):
    panier = Panier(request)
    return {'panier': panier}