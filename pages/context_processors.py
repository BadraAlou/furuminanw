def contact_info(request):
    """Context processor pour les informations de contact de l'entreprise"""
    return {
        'COMPANY_ADDRESS': 'Bacodjokoroni Aci',
        'COMPANY_CITY': 'Bamako',
        'COMPANY_COUNTRY': 'Mali',
        'COMPANY_PHONE': '62 98 03 18',
        'COMPANY_PHONE_LINK': 'tel:+22362980318',
        'COMPANY_EMAIL': 'furuminanw@gmail.com',
        'COMPANY_MAPS_URL': 'https://maps.app.goo.gl/kjm7iFSPfGDtNgvGA?g_st=iw',
        'COMPANY_FACEBOOK': 'https://www.facebook.com/profile.php?id=61576750467318',
        'COMPANY_INSTAGRAM': 'https://www.instagram.com/furuminanw?igsh=anE5YXhoeXMybnl2&utm_source=qr',
    }
