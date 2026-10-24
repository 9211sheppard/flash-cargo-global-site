(() => {
  'use strict';

  const menuButton = document.querySelector('.menu-toggle');
  const menu = document.querySelector('#primary-menu');
  const closeMenu = () => {
    if (!menuButton || !menu) return;
    menuButton.setAttribute('aria-expanded', 'false');
    menu.classList.remove('is-open');
  };
  if (menuButton && menu) {
    menuButton.addEventListener('click', () => {
      const opened = menuButton.getAttribute('aria-expanded') !== 'true';
      menuButton.setAttribute('aria-expanded', String(opened));
      menu.classList.toggle('is-open', opened);
    });
    menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        closeMenu();
        menuButton.focus();
      }
    });
  }

  const requestParams = new URLSearchParams(location.search);
  document.querySelectorAll('[data-request-form]').forEach((form) => {
    const started = form.elements.namedItem('form_started_at');
    const enhanced = form.elements.namedItem('javascript_enabled');
    const stamp = () => {
      started.value = String(Date.now());
      enhanced.value = 'yes';
    };
    const prefill = (name, text) => {
      const field = form.elements.namedItem(name);
      if (field && !field.value && text) field.value = text.slice(0, field.maxLength > 0 ? field.maxLength : 160);
    };
    stamp();
    if (form.dataset.audience === 'buyer_sourcing') {
      prefill('product_name', requestParams.get('product'));
      prefill('origin_preference', requestParams.get('origin'));
      prefill('delivery_country', requestParams.get('destination'));
    }
    const quantity = form.elements.namedItem('quantity');
    const unit = form.elements.namedItem('quantity_unit');
    const updateUnit = () => {
      if (!quantity || !unit) return;
      const whole = ['pieces', 'cartons'].includes(unit.value);
      quantity.min = whole ? '1' : '0.001';
      quantity.step = whole ? '1' : 'any';
    };
    unit?.addEventListener('change', updateUnit);
    updateUnit();
    form.addEventListener('reset', () => queueMicrotask(() => {
      stamp();
      updateUnit();
    }));
  });
  if (['freight', 'delivery', 'delivery_only'].includes(requestParams.get('inquiry')) && document.querySelector('#delivery-request')) {
    location.hash = 'delivery-request';
  }
  document.querySelectorAll('[data-request-verification], [data-supplier-verification]').forEach((widget) => {
    const form = widget.closest('form');
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('[data-verification-status]');
    let verified = false;
    let rendered = false;
    button.disabled = true;
    const update = (message, passed = false) => {
      verified = passed;
      button.disabled = !passed;
      status.textContent = message;
    };
    const render = () => {
      if (rendered || !window.turnstile) return;
      rendered = true;
      window.turnstile.render(widget, {
        sitekey: widget.dataset.sitekey,
        action: widget.dataset.action,
        size: 'flexible',
        theme: 'light',
        callback: () => update('Security check complete. You can submit your request.', true),
        'expired-callback': () => update('The security check expired. Complete it again before submitting.'),
        'timeout-callback': () => update('The security check timed out. Complete it again before submitting.'),
        'error-callback': (code) => {
          const reference = /^\d{6}$/.test(String(code)) ? ' Reference: ' + code + '.' : '';
          update('The security check could not complete. Try an updated browser or reload the page; your request has not been sent.' + reference);
          return true;
        },
      });
    };
    const script = document.querySelector('script[src^="https://challenges.cloudflare.com/turnstile/"]');
    script?.addEventListener('load', render, { once: true });
    script?.addEventListener('error', () => update('The security check could not load. Check your connection and reload this page.'), { once: true });
    render();
    form.addEventListener('submit', (event) => {
      if (!verified) {
        event.preventDefault();
        update('Complete the security check before submitting.');
        status.focus();
      }
    });
  });
})();
