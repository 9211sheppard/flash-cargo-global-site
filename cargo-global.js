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

  const form = document.querySelector('[data-inquiry-form]');
  if (!form) return;
  const sourceFields = form.querySelector('[data-sourcing-fields]');
  const freightFields = form.querySelector('[data-freight-fields]');
  const freightNeeds = form.querySelector('textarea[name="freight_needs"]');
  const summary = form.querySelector('[data-sourcing-summary]');
  const started = form.elements.namedItem('form_started_at');
  const quantity = form.elements.namedItem('quantity');
  const unit = form.elements.namedItem('quantity_unit');
  const value = (name) => form.elements.namedItem(name)?.value.trim() || '';

  const setInquiry = (type) => {
    const sourcing = type !== 'freight';
    const selected = sourcing ? 'sourcing' : 'freight';
    form.querySelector(`[name="inquiry_type"][value="${selected}"]`).checked = true;
    sourceFields.hidden = !sourcing;
    sourceFields.disabled = !sourcing;
    freightFields.hidden = sourcing;
    freightNeeds.disabled = sourcing;
    freightNeeds.required = !sourcing;
    summary.disabled = !sourcing;
  };
  const updateUnit = () => {
    const whole = ['pieces', 'cartons'].includes(unit.value);
    quantity.min = whole ? '1' : '0.001';
    quantity.step = whole ? '1' : 'any';
  };
  const buildSummary = () => {
    const price = value('target_price');
    const currency = value('target_price_currency');
    const basis = value('price_basis') === 'total_order' ? 'total order' : `per unit (${unit.value})`;
    return [
      'Inquiry: Product sourcing',
      `Product: ${value('product_name')}`,
      `Quantity: ${value('quantity')} ${unit.value}`,
      `Specs: ${value('product_specs')}`,
      `Photo or spec reference: ${value('spec_link') || 'Not provided'}`,
      `Target price: ${price ? `${currency} ${price} ${basis}` : `Not provided (${currency})`}`,
      `Delivery city: ${value('delivery_city')}`,
      `Province or state: ${value('delivery_region')}`,
      `Country: ${value('delivery_country')}`,
      `Postal code: ${value('delivery_postal_code') || 'Not provided'}`,
    ].join('\n');
  };

  started.value = String(Date.now());
  form.querySelectorAll('[name="inquiry_type"]').forEach((input) => input.addEventListener('change', () => setInquiry(input.value)));
  unit.addEventListener('change', updateUnit);
  document.querySelectorAll('[data-inquiry]').forEach((link) => link.addEventListener('click', () => setInquiry(link.dataset.inquiry)));
  form.addEventListener('submit', () => {
    if (value('inquiry_type') !== 'freight') summary.value = buildSummary();
  });
  form.addEventListener('formdata', (event) => {
    if (form.querySelector('[name="inquiry_type"][value="sourcing"]').checked) event.formData.set('freight_needs', buildSummary());
  });
  form.addEventListener('reset', () => queueMicrotask(() => {
    setInquiry('sourcing');
    updateUnit();
    started.value = String(Date.now());
  }));
  setInquiry(new URLSearchParams(location.search).get('inquiry'));
  updateUnit();
})();
