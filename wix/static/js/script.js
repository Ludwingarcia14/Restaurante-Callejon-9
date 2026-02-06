// Navegación suave y activación de enlaces
document.addEventListener('DOMContentLoaded', function() {
    // Navegación suave
    const navLinks = document.querySelectorAll('.nav-link');
    const menuToggle = document.getElementById('menu-toggle');
    const mainNav = document.getElementById('main-nav');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            // Cerrar menú en móvil si está abierto
            if (mainNav.classList.contains('active')) {
                mainNav.classList.remove('active');
            }
            
            // Desplazamiento suave
            window.scrollTo({
                top: targetSection.offsetTop - 100,
                behavior: 'smooth'
            });
            
            // Actualizar enlace activo
            navLinks.forEach(link => link.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Toggle del menú en móvil
    menuToggle.addEventListener('click', function() {
        mainNav.classList.toggle('active');
    });
    
    // Cambiar enlace activo al hacer scroll
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const scrollPos = window.scrollY + 150;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    });
    
    // Funcionalidad del carrusel
    const carouselSlides = document.querySelectorAll('.carousel-slide');
    const indicators = document.querySelectorAll('.indicator');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    let currentSlide = 0;
    
    // Función para mostrar slide
    function showSlide(index) {
        // Ocultar todos los slides
        carouselSlides.forEach(slide => {
            slide.classList.remove('active');
        });
        
        // Remover active de todos los indicadores
        indicators.forEach(indicator => {
            indicator.classList.remove('active');
        });
        
        // Mostrar slide actual y activar indicador
        carouselSlides[index].classList.add('active');
        indicators[index].classList.add('active');
        
        currentSlide = index;
    }
    
    // Event listeners para botones
    prevBtn.addEventListener('click', function() {
        let newIndex = currentSlide - 1;
        if (newIndex < 0) {
            newIndex = carouselSlides.length - 1;
        }
        showSlide(newIndex);
    });
    
    nextBtn.addEventListener('click', function() {
        let newIndex = currentSlide + 1;
        if (newIndex >= carouselSlides.length) {
            newIndex = 0;
        }
        showSlide(newIndex);
    });
    
    // Event listeners para indicadores
    indicators.forEach(indicator => {
        indicator.addEventListener('click', function() {
            const slideIndex = parseInt(this.getAttribute('data-slide'));
            showSlide(slideIndex);
        });
    });
    
    // Cambio automático de slides cada 5 segundos
    let carouselInterval = setInterval(function() {
        let newIndex = currentSlide + 1;
        if (newIndex >= carouselSlides.length) {
            newIndex = 0;
        }
        showSlide(newIndex);
    }, 5000);
    
    // Pausar carrusel al interactuar con él
    const carouselContainer = document.querySelector('.carousel-container');
    carouselContainer.addEventListener('mouseenter', function() {
        clearInterval(carouselInterval);
    });
    
    carouselContainer.addEventListener('mouseleave', function() {
        carouselInterval = setInterval(function() {
            let newIndex = currentSlide + 1;
            if (newIndex >= carouselSlides.length) {
                newIndex = 0;
            }
            showSlide(newIndex);
        }, 5000);
    });
    
    // Manejo del formulario de reservas con Flask
    const reservationForm = document.getElementById('reservation-form');
    const reservationMessage = document.getElementById('reservation-message');
    
    if (reservationForm) {
        reservationForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Mostrar indicador de carga
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Procesando...';
            submitBtn.disabled = true;
            
            try {
                const formData = new FormData(this);
                
                const response = await fetch('/reservar', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    reservationMessage.textContent = result.message;
                    reservationMessage.className = 'message success';
                    this.reset();
                } else {
                    reservationMessage.textContent = result.message;
                    reservationMessage.className = 'message error';
                }
            } catch (error) {
                reservationMessage.textContent = 'Error al procesar la reserva. Por favor, inténtalo de nuevo.';
                reservationMessage.className = 'message error';
                console.error('Error:', error);
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                
                // Ocultar mensaje después de 5 segundos
                setTimeout(() => {
                    reservationMessage.style.display = 'none';
                }, 5000);
            }
        });
    }
    
    // Manejo del formulario de newsletter con Flask
    const newsletterForm = document.getElementById('newsletter-form');
    const newsletterMessage = document.getElementById('newsletter-message');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Mostrar indicador de carga
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Procesando...';
            submitBtn.disabled = true;
            
            try {
                const formData = new FormData(this);
                
                const response = await fetch('/newsletter', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    newsletterMessage.textContent = result.message;
                    newsletterMessage.className = 'message success';
                    this.reset();
                } else {
                    newsletterMessage.textContent = result.message;
                    newsletterMessage.className = 'message error';
                }
            } catch (error) {
                newsletterMessage.textContent = 'Error al procesar la suscripción. Por favor, inténtalo de nuevo.';
                newsletterMessage.className = 'message error';
                console.error('Error:', error);
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                
                // Ocultar mensaje después de 5 segundos
                setTimeout(() => {
                    newsletterMessage.style.display = 'none';
                }, 5000);
            }
        });
    }
});