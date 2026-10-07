// Mountains rise with scroll: --rise goes 0 → 1 across the page.
const root = document.documentElement;
document.querySelectorAll('.range').forEach((el) => {
  el.style.setProperty('--depth', el.dataset.depth);
});

let ticking = false;
function updateRise() {
  const max = root.scrollHeight - innerHeight;
  const rise = max > 0 ? Math.min(scrollY / max, 1) : 1;
  root.style.setProperty('--rise', rise.toFixed(4));
  ticking = false;
}
addEventListener('scroll', () => {
  if (!ticking) { requestAnimationFrame(updateRise); ticking = true; }
}, { passive: true });
addEventListener('resize', updateRise);
updateRise();

// Panels fade in as they enter the viewport; nav highlights the current section.
const navLinks = [...document.querySelectorAll('nav a')];
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('visible');
    navLinks.forEach((a) => a.classList.toggle('active', a.hash === '#' + entry.target.id));
  });
}, { threshold: 0.25 });
document.querySelectorAll('.panel').forEach((p) => observer.observe(p));

// Mobile menu
const toggle = document.querySelector('.menu-toggle');
const nav = document.getElementById('nav');
toggle.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  toggle.setAttribute('aria-expanded', open);
});
navLinks.forEach((a) => a.addEventListener('click', () => nav.classList.remove('open')));
