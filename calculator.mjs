import Big from './assets/big.mjs';

export const COST_FIELDS = ['goods_cost', 'samples_inspection', 'origin_packing', 'transport_cost', 'insurance_cost', 'duty_cost', 'tax_cost', 'clearance_cost', 'final_delivery', 'other_costs'];

export function calculateCosts(values, quantity, currency) {
  if (!['USD', 'CAD'].includes(currency)) throw new Error('Choose USD or CAD.');
  const count = new Big(String(quantity));
  if (count.lte(0)) throw new Error('A positive comparison quantity is required.');
  let total = new Big(0);
  for (const name of COST_FIELDS) {
    if (values[name] === '' || values[name] == null) throw new Error('Quote required: one or more costs are unknown.');
    const amount = new Big(String(values[name]));
    if (amount.lt(0)) throw new Error('Costs cannot be negative.');
    total = total.plus(amount);
  }
  return { currency, total: total.round(2, Big.roundHalfUp).toFixed(2), unit: total.div(count).round(2, Big.roundHalfUp).toFixed(2), quantity: count.toString() };
}

if (typeof document !== 'undefined') {
  const tool = document.querySelector('[data-cost-calculator]');
  if (tool) {
    const result = tool.querySelector('[data-cost-result]');
    const input = name => tool.querySelector(`[name="${name}"]`);
    tool.querySelector('[data-calculate]').addEventListener('click', () => {
      const controls = [...tool.querySelectorAll('input,select')];
      if (!controls.every(control => control.reportValidity())) return;
      try {
        const values = Object.fromEntries(COST_FIELDS.map(name => [name, input(name).value]));
        const calculation = calculateCosts(values, input('comparison_quantity').value, input('comparison_currency').value);
        const money = value => new Intl.NumberFormat('en-CA', { style: 'currency', currency: calculation.currency, currencyDisplay: 'code' }).format(value);
        result.replaceChildren();
        const total = document.createElement('strong');
        total.textContent = money(calculation.total);
        const unit = document.createElement('span');
        unit.textContent = `${money(calculation.unit)} per comparison unit`;
        result.append(total, unit);
      } catch (error) {
        result.textContent = error.message;
      }
    });
    tool.querySelector('[data-reset-costs]').addEventListener('click', () => {
      tool.querySelectorAll('input').forEach(control => { control.value = ''; });
      result.textContent = 'Quote required';
    });
    tool.querySelectorAll('input,select').forEach(control => control.addEventListener('input', () => {
      result.textContent = 'Quote required';
    }));
  }
}
