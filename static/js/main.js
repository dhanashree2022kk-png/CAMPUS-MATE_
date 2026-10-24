(() => {
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const sidebar = document.getElementById('sidebar');
  if (menuToggle && sidebar) menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  const publicToggle = document.querySelector('[data-public-menu-toggle]');
  const publicNav = document.getElementById('public-nav');
  if (publicToggle && publicNav) publicToggle.addEventListener('click', () => publicNav.classList.toggle('public-nav-open'));
  document.querySelectorAll('[data-password-toggle]').forEach(button => button.addEventListener('click', () => {
    const input = button.parentElement.querySelector('input'); if (!input) return;
    const show = input.type === 'password'; input.type = show ? 'text' : 'password'; button.textContent = show ? 'Hide' : 'Show';
  }));
  document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
    if (!window.confirm(form.getAttribute('data-confirm') || 'Are you sure?')) event.preventDefault();
  }));
  document.querySelectorAll('.flash-close').forEach(button => button.addEventListener('click', () => button.closest('.flash')?.remove()));
})();
