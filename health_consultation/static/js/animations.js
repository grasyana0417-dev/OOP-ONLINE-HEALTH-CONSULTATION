/**
 * Animations and Effects for Barangay Guimbala Health Consultation System
 */

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', function() {
    const hero = document.querySelector('.hero-section');
    if (hero) {
        const scrolled = window.pageYOffset;
        const parallax = hero.querySelector('.hero-pattern');
        if (parallax) {
            parallax.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    }
});

// Intersection Observer for scroll animations
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animated');
            
            // Handle stagger animations
            const staggerParent = entry.target.closest('.stagger-children');
            if (staggerParent) {
                const children = staggerParent.children;
                Array.from(children).forEach((child, index) => {
                    setTimeout(() => {
                        child.style.opacity = '1';
                        child.style.transform = 'translateY(0)';
                    }, index * 100);
                });
            }
        }
    });
}, observerOptions);

// Observe all elements with animation classes
document.querySelectorAll('.slide-up, .slide-in-right, .fade-in, .scale-in').forEach(el => {
    observer.observe(el);
});

// Card hover effects with 3D transform
document.querySelectorAll('.card-hover').forEach(card => {
    card.addEventListener('mousemove', function(e) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
    });
    
    card.addEventListener('mouseleave', function() {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
    });
});

// Button click ripple effect
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function(e) {
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const ripple = document.createElement('span');
        ripple.classList.add('ripple-effect');
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Add ripple effect styles
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple-effect {
        position: absolute;
        width: 100px;
        height: 100px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: translate(-50%, -50%) scale(0);
        animation: rippleAnimation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes rippleAnimation {
        to {
            transform: translate(-50%, -50%) scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyle);

// Typing effect for hero title
function typeWriter(element, text, speed = 50) {
    let i = 0;
    element.textContent = '';
    
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Counter animation for statistics
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    function updateCounter() {
        start += increment;
        if (start < target) {
            element.textContent = Math.floor(start);
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    }
    
    updateCounter();
}

// Observe statistics for counter animation
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const target = parseInt(stat.textContent);
                if (!isNaN(target)) {
                    animateCounter(stat, target);
                }
            });
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.hero-stats').forEach(stats => {
    statsObserver.observe(stats);
});

// Progress bar animation
function animateProgressBar(element, percentage) {
    element.style.width = '0%';
    setTimeout(() => {
        element.style.transition = 'width 1s ease';
        element.style.width = `${percentage}%`;
    }, 100);
}

// Skeleton loading effect
function showSkeleton(container) {
    container.innerHTML = `
        <div class="skeleton-card">
            <div class="skeleton-header"></div>
            <div class="skeleton-body">
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line short"></div>
            </div>
        </div>
    `;
}

// Add skeleton styles
const skeletonStyle = document.createElement('style');
skeletonStyle.textContent = `
    .skeleton-card {
        background: #f0f0f0;
        border-radius: 8px;
        padding: 20px;
        animation: skeletonPulse 1.5s ease-in-out infinite;
    }
    
    .skeleton-header {
        height: 20px;
        width: 60%;
        background: #e0e0e0;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    
    .skeleton-line {
        height: 12px;
        background: #e0e0e0;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    
    .skeleton-line.short {
        width: 40%;
    }
    
    @keyframes skeletonPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
`;
document.head.appendChild(skeletonStyle);

// Notification badge pulse
function pulseBadge(badge) {
    badge.style.animation = 'none';
    badge.offsetHeight; // Trigger reflow
    badge.style.animation = 'badgePulse 2s ease-in-out infinite';
}

// Call status indicator animation
function startCallStatusAnimation(element) {
    element.classList.add('call-status-active');
}

function stopCallStatusAnimation(element) {
    element.classList.remove('call-status-active');
}

// Image lazy loading
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Smooth reveal animation on scroll
window.addEventListener('scroll', throttle(() => {
    const reveals = document.querySelectorAll('.reveal');
    
    reveals.forEach(element => {
        const windowHeight = window.innerHeight;
        const elementTop = element.getBoundingClientRect().top;
        const elementVisible = 150;
        
        if (elementTop < windowHeight - elementVisible) {
            element.classList.add('active');
        }
    });
}, 100));

// Mouse parallax effect
function initMouseParallax() {
    const parallaxElements = document.querySelectorAll('.parallax');
    
    document.addEventListener('mousemove', throttle((e) => {
        const mouseX = e.clientX / window.innerWidth - 0.5;
        const mouseY = e.clientY / window.innerHeight - 0.5;
        
        parallaxElements.forEach(el => {
            const speed = el.dataset.speed || 0.1;
            const x = mouseX * speed * 100;
            const y = mouseY * speed * 100;
            
            el.style.transform = `translate(${x}px, ${y}px)`;
        });
    }, 50));
}

// Initialize mouse parallax if elements exist
if (document.querySelector('.parallax')) {
    initMouseParallax();
}

// Tab switching animation
function switchTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');
    
    tabs.forEach(tab => {
        tab.style.display = 'none';
        tab.classList.remove('active');
    });
    
    buttons.forEach(button => {
        button.classList.remove('active');
    });
    
    const targetTab = document.getElementById(tabId);
    const targetButton = document.querySelector(`[data-tab="${tabId}"]`);
    
    if (targetTab && targetButton) {
        targetTab.style.display = 'block';
        targetTab.classList.add('active');
        targetButton.classList.add('active');
        
        // Fade in animation
        targetTab.style.opacity = '0';
        targetTab.style.transform = 'translateY(10px)';
        
        requestAnimationFrame(() => {
            targetTab.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            targetTab.style.opacity = '1';
            targetTab.style.transform = 'translateY(0)';
        });
    }
}

// Accordion animation
function toggleAccordion(element) {
    const content = element.nextElementSibling;
    const isOpen = content.style.maxHeight;
    
    // Close all accordions
    document.querySelectorAll('.accordion-content').forEach(acc => {
        acc.style.maxHeight = null;
        acc.previousElementSibling.classList.remove('active');
    });
    
    // Open clicked one if it was closed
    if (!isOpen) {
        content.style.maxHeight = content.scrollHeight + 'px';
        element.classList.add('active');
    }
}
