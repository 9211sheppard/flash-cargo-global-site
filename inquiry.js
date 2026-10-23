(() => {
  'use strict';

  const form = document.querySelector('[data-inquiry-form]');
  if (!form) return;

  const startedAt = form.elements.namedItem('form_started_at');
  const sourceFields = form.querySelector('[data-sourcing-fields]');
  const freightFields = form.querySelector('[data-freight-fields]');
  const freightNeeds = form.querySelector('textarea[name="freight_needs"]');
  const sourcingSummary = form.querySelector('[data-sourcing-summary]');
  const sourcingChoice = form.querySelector('[name="inquiry_type"][value="sourcing"]');
  const quantity = form.elements.namedItem('quantity');
  const quantityUnit = form.elements.namedItem('quantity_unit');

  const resetTimer = () => { startedAt.value = String(Date.now()); };
  const setInquiry = (type) => {
    const sourcing = type === 'sourcing';
    form.querySelector(`[name="inquiry_type"][value="${sourcing ? 'sourcing' : 'freight'}"]`).checked = true;
    sourceFields.hidden = !sourcing;
    sourceFields.disabled = !sourcing;
    freightFields.hidden = sourcing;
    freightNeeds.disabled = sourcing;
    freightNeeds.required = !sourcing;
    sourcingSummary.disabled = !sourcing;
  };
  const setQuantityUnit = () => {
    const wholeUnits = ['pieces', 'cartons'].includes(quantityUnit.value);
    quantity.min = wholeUnits ? '1' : '0.001';
    quantity.step = wholeUnits ? '1' : 'any';
  };

  resetTimer();

  form.querySelectorAll('[name="inquiry_type"]').forEach((choice) => {
    choice.addEventListener('change', () => setInquiry(choice.value));
  });
  quantityUnit.addEventListener('change', setQuantityUnit);

  const buildSourcingSummary = () => {
    const value = (name) => form.elements.namedItem(name).value.trim();
    const price = value('target_price');
    const priceBasis = value('price_basis') === 'total_order'
      ? 'total order'
      : `per unit (${value('quantity_unit')})`;
    return [
      'Inquiry: Product sourcing',
      `Product name: ${value('product_name')}`,
      `Quantity: ${value('quantity')} ${value('quantity_unit')}`,
      `Specs: ${value('product_specs')}`,
      `Photo or spec sheet: ${value('spec_link') || 'Not provided'}`,
      `Target price: ${price ? `USD ${price} ${priceBasis}` : 'Not provided (USD)'}`,
      `Delivery city: ${value('delivery_city')}`,
      `Delivery country: ${value('delivery_country')}`,
      `Postal code: ${value('delivery_postal_code') || 'Not provided'}`,
    ].join('\n');
  };

  // Preserve the existing handler's message field, including on older browsers.
  form.addEventListener('submit', () => {
    if (sourcingChoice.checked) sourcingSummary.value = buildSourcingSummary();
  });
  form.addEventListener('formdata', (event) => {
    if (sourcingChoice.checked) {
      event.formData.set('freight_needs', buildSourcingSummary());
    }
  });

  document.querySelectorAll('[data-inquiry]').forEach((link) => {
    link.addEventListener('click', () => setInquiry(link.dataset.inquiry));
  });
  form.addEventListener('reset', () => {
    queueMicrotask(() => {
      setInquiry('freight');
      setQuantityUnit();
      resetTimer();
    });
  });

  setQuantityUnit();
  setInquiry(new URLSearchParams(window.location.search).get('inquiry'));
})();
