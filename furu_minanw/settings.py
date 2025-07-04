# furu_minanw/furu_minanw/settings.py
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-furu-minanw-secret-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

#ALLOWED_HOSTS = []
ALLOWED_HOSTS = ['31.207.35.193', 'localhost', '127.0.0.1', 'furuminanw.com']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',

    # Custom apps
    'produits.apps.ProduitsConfig',
    'commandes.apps.CommandesConfig',
    'utilisateurs.apps.UtilisateursConfig',
    'pages.apps.PagesConfig',
    'rh_gestion.apps.RhGestionConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'furu_minanw.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'commandes.context_processors.panier_processor',
                'pages.context_processors.contact_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'furu_minanw.wsgi.application'

# Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myproject',
        'USER': 'myprojectuser',
        'PASSWORD': 'Db12345$',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Authentication
LOGIN_REDIRECT_URL = 'pages:accueil'
LOGIN_URL = 'utilisateurs:connexion'
LOGOUT_REDIRECT_URL = 'pages:accueil'

# Email configuration (for development)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'in-v3.mailjet.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'd7df8921fc98fadd6bd1561aa634b012'  # Ex: ab12345678901234
EMAIL_HOST_PASSWORD = '86fe7a160bc5519daefc82e76e112699'  # La clé SMTP copiée
DEFAULT_FROM_EMAIL = 'furuminanw@gmail.com'


# Informations de contact de l'entreprise
COMPANY_INFO = {
    'name': 'Furu Minanw',
    'address': 'Bacodjokoroni Aci',
    'city': 'Bamako',
    'country': 'Mali',
    'phone': '62 98 03 18',
    'phone_international': '+223 62 98 03 18',
    'email': 'furuminanw@gmail.com',
    'maps_url': 'https://maps.app.goo.gl/kjm7iFSPfGDtNgvGA?g_st=iw',
    'facebook': 'https://www.facebook.com/profile.php?id=61576750467318',
    'instagram': 'https://www.instagram.com/furuminanw?igsh=anE5YXhoeXMybnl2&utm_source=qr',
}
