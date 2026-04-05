/* ══════════════════════════════════════════════════════════
   Ministry of Failures — main.js
   ══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Mobile nav toggle ───────────────────────────────────
  const toggle = document.querySelector('.nav-toggle');
  const nav    = document.querySelector('.main-nav');
  toggle?.addEventListener('click', () => nav?.classList.toggle('open'));
  // Close on nav link click
  nav?.querySelectorAll('.nav-link').forEach(l => {
    l.addEventListener('click', () => nav.classList.remove('open'));
  });


  // ── Animated counters ────────────────────────────────────
  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    const duration = 1600;
    const step = Math.ceil(duration / target);
    let current = 0;
    const timer = setInterval(() => {
      current += Math.ceil(target / 60);
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = current.toLocaleString();
    }, step);
  }

  const counters = document.querySelectorAll('.counter-num[data-target]');
  if (counters.length) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { animateCounter(e.target); obs.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    counters.forEach(c => obs.observe(c));
  }


  // ── Hero ticker duplication ──────────────────────────────
  const tape = document.querySelector('.hero-tape');
  if (tape) tape.innerHTML = tape.textContent.repeat(6);


  // ── Stagger reveal on scroll ─────────────────────────────
  const revealEls = document.querySelectorAll(
    '.index-header, .file-card, .doc-row, .gallery-item, .qa-card'
  );
  if (revealEls.length) {
    revealEls.forEach(el => { el.style.opacity = '0'; el.style.transform = 'translateY(16px)'; });
    const revObs = new IntersectionObserver(entries => {
      entries.forEach((e, i) => {
        if (e.isIntersecting) {
          setTimeout(() => {
            e.target.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            e.target.style.opacity   = '1';
            e.target.style.transform = 'none';
          }, i * 30);
          revObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => revObs.observe(el));
  }


  // ── Active nav highlight based on URL ────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && path === href) link.classList.add('active');
  });


  // ── Keyboard shortcut: / to focus search ─────────────────
  document.addEventListener('keydown', e => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      const si = document.querySelector('.search-input');
      si?.focus();
    }
  });

});
