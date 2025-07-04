document.addEventListener('DOMContentLoaded', function() {
    // Gestion des images produit (miniatures)
    const productThumbs = document.querySelectorAll('.product-thumb');
    const mainImage = document.querySelector('.main-product-image');

    if (productThumbs.length > 0 && mainImage) {
        productThumbs.forEach(thumb => {
            thumb.addEventListener('click', function() {
                const imgSrc = this.getAttribute('data-img-src');
                const imgAlt = this.getAttribute('alt');

                // Mettre à jour l'image principale
                mainImage.setAttribute('src', imgSrc);
                mainImage.setAttribute('alt', imgAlt);

                // Mettre à jour la classe active
                productThumbs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // Animation du compteur de produits
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

    // Utilisation de IntersectionObserver pour les animations au scroll
    const observerOptions = {
        root: null, // viewport
        rootMargin: '0px',
        threshold: 0.1 // Trigger when 10% of the element is visible
    };

    const observerCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('slide-up'); // Apply your animation class
                observer.unobserve(entry.target); // Stop observing once animated
            }
        });
    };

    const scrollAnimationObserver = new IntersectionObserver(observerCallback, observerOptions);

    // Observe all elements with the 'animate-on-scroll' class
    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        scrollAnimationObserver.observe(element);
    });

    // Trigger counter animation if already in view on load
    let animatedCounters = false;
    const checkCounters = () => {
        if (!animatedCounters && counterElements.length > 0) {
            counterElements.forEach(counter => {
                const rect = counter.getBoundingClientRect();
                if (rect.top < (window.innerHeight || document.documentElement.clientHeight) && rect.bottom > 0) {
                    const target = parseInt(counter.getAttribute('data-target'));
                    animateValue(counter, 0, target, 2000);
                    animatedCounters = true; // Only animate once
                }
            });
        }
    };

    // Initial check for counters
    checkCounters();
    // Add scroll listener for counters if not already animated
    window.addEventListener('scroll', checkCounters);

    // Validation de formulaire
    const forms = document.querySelectorAll('.needs-validation');

    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });
});
