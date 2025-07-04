/**
 * Furu Minanw - UI Enhancements
 * Script pour améliorer l'expérience utilisateur et l'interactivité
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===== ANIMATIONS AU SCROLL =====
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll');

        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;

            if (elementPosition < windowHeight - 100) {
                element.classList.add('slide-up');
            }
        });
    };

    // Appeler la fonction au chargement et au scroll
    if (document.querySelectorAll('.animate-on-scroll').length > 0) {
        animateOnScroll();
        window.addEventListener('scroll', animateOnScroll);
    }

    // ===== GESTION DES IMAGES PRODUIT (MINIATURES) =====
    const productThumbs = document.querySelectorAll('.product-thumb');
    const mainImage = document.querySelector('.main-product-image');

    if (productThumbs.length > 0 && mainImage) {
        productThumbs.forEach(thumb => {
            thumb.addEventListener('click', function() {
                const imgSrc = this.getAttribute('data-img-src');
                const imgAlt = this.getAttribute('alt');

                // Mettre à jour l'image principale avec transition
                mainImage.style.opacity = '0';
                setTimeout(() => {
                    mainImage.setAttribute('src', imgSrc);
                    mainImage.setAttribute('alt', imgAlt);
                    mainImage.style.opacity = '1';
                }, 300);

                // Mettre à jour la classe active
                productThumbs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // ===== ANIMATION DU COMPTEUR DE PRODUITS =====
    const animateValue = (obj, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };

    const counterElements = document.querySelectorAll('.counter');

    const isInViewport = (element) => {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    };

    let animated = false;

    if (counterElements.length > 0) {
        const checkCounters = function() {
            if (!animated && counterElements.length > 0 && isInViewport(counterElements[0])) {
                animated = true;
                counterElements.forEach(counter => {
                    const target = parseInt(counter.getAttribute('data-target'));
                    animateValue(counter, 0, target, 2000);
                });
            }
        };

        window.addEventListener('scroll', checkCounters);
        // Vérifier aussi au chargement
        checkCounters();
    }

    // ===== VALIDATION DE FORMULAIRE =====
    const forms = document.querySelectorAll('.needs-validation');

    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();

                // Trouver le premier champ invalide et le mettre en focus
                const invalidField = form.querySelector(':invalid');
                if (invalidField) {
                    invalidField.focus();

                    // Scroll doux vers le champ invalide
                    invalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }

            form.classList.add('was-validated');
        }, false);
    });

    // ===== GESTION DES QUANTITÉS =====
    const quantityBtns = document.querySelectorAll('.quantity-btn');

    quantityBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const currentValue = parseInt(input.value);
            const isIncrement = this.classList.contains('increment');

            if (isIncrement) {
                if (currentValue < parseInt(input.getAttribute('max') || 10)) {
                    input.value = currentValue + 1;
                }
            } else {
                if (currentValue > parseInt(input.getAttribute('min') || 1)) {
                    input.value = currentValue - 1;
                }
            }

            // Déclencher l'événement change pour mettre à jour les calculs
            const event = new Event('change', { bubbles: true });
            input.dispatchEvent(event);
        });
    });

    // ===== GESTION DES FAVORIS =====
    const favoriteBtns = document.querySelectorAll('.favorite-btn');

    favoriteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Empêcher la propagation pour éviter les conflits avec d'autres événements
            e.stopPropagation();

            // L'animation et la logique sont gérées dans la fonction toggleFavorite
            // qui est définie dans les templates individuels
        });
    });

    // ===== AMÉLIORATION DE L'ACCESSIBILITÉ =====
    // Ajouter des attributs ARIA pour améliorer l'accessibilité
    const dropdowns = document.querySelectorAll('.dropdown-toggle');

    dropdowns.forEach(dropdown => {
        dropdown.setAttribute('aria-haspopup', 'true');
        dropdown.setAttribute('aria-expanded', 'false');

        dropdown.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !expanded);
        });
    });

    // ===== OPTIMISATION DES IMAGES =====
    // Chargement paresseux des images hors écran
    if ('loading' in HTMLImageElement.prototype) {
        // Le navigateur prend en charge le chargement paresseux natif
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback pour les navigateurs qui ne prennent pas en charge le chargement paresseux natif
        const lazyImages = document.querySelectorAll('.lazy-image');

        const lazyLoad = function() {
            const lazyImageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const lazyImage = entry.target;
                        lazyImage.src = lazyImage.dataset.src;
                        lazyImage.classList.remove('lazy-image');
                        lazyImageObserver.unobserve(lazyImage);
                    }
                });
            });

            lazyImages.forEach(function(lazyImage) {
                lazyImageObserver.observe(lazyImage);
            });
        };

        // Vérifier si IntersectionObserver est pris en charge
        if ('IntersectionObserver' in window) {
            lazyLoad();
        } else {
            // Fallback pour les navigateurs qui ne prennent pas en charge IntersectionObserver
            lazyImages.forEach(function(lazyImage) {
                lazyImage.src = lazyImage.dataset.src;
            });
        }
    }

    // ===== AMÉLIORATION DES PERFORMANCES =====
    // Débounce pour les événements fréquents
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Appliquer le debounce au redimensionnement de la fenêtre
    const handleResize = debounce(() => {
        // Code à exécuter lors du redimensionnement
        console.log('Window resized');
    }, 100);

    window.addEventListener('resize', handleResize);

    // ===== AMÉLIORATION DE L'EXPÉRIENCE MOBILE =====
    // Détecter si l'appareil est tactile
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0;

    if (isTouchDevice) {
        document.body.classList.add('touch-device');

        // Améliorer l'expérience des menus déroulants sur mobile
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('touchstart', function() {
                this.classList.add('active-touch');
            });

            item.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('active-touch');
                }, 300);
            });
        });
    }
});