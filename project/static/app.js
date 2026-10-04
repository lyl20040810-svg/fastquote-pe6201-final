const requestBox = document.querySelector('#request');
const generateButton = document.querySelector('#generate');
const results = document.querySelector('#results');
const notice = document.querySelector('#notice');
let mode = 'auto';

document.querySelectorAll('.mode').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.mode').forEach((item) => item.classList.remove('active'));
    button.classList.add('active');
    mode = button.dataset.mode;
  });
});

document.querySelectorAll('[data-example]').forEach((button) => {
  button.addEventListener('click', () => { requestBox.value = button.dataset.example; });
});

generateButton.addEventListener('click', async () => {
  setNotice('', false);
  results.classList.add('hidden');
  generateButton.disabled = true;
  generateButton.textContent = 'Processing...';
  try {
    const response = await fetch('/api/quote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request: requestBox.value, mode }),
    });
    const data = await response.json();
    if (!response.ok || data.processing_status === 'error') throw new Error(data.message || 'Request failed.');
    if (data.processing_status === 'flagged') {
      setNotice(data.message || 'This request needs manual review.', true);
      return;
    }
    renderQuote(data);
    if (data.fallback_warning) setNotice(`OpenRouter was unavailable. Rules mode was used. ${data.fallback_warning}`, false);
  } catch (error) {
    setNotice(error.message, true);
  } finally {
    generateButton.disabled = false;
    generateButton.textContent = 'Generate quotation';
  }
});

document.querySelector('#copy').addEventListener('click', async () => {
  await navigator.clipboard.writeText(document.querySelector('#reply').textContent);
  document.querySelector('#copy').textContent = 'Copied';
  setTimeout(() => { document.querySelector('#copy').textContent = 'Copy'; }, 1200);
});

function setNotice(message, error) {
  notice.textContent = message;
  notice.classList.toggle('hidden', !message);
  notice.classList.toggle('error', Boolean(error));
}

function renderQuote(data) {
  const p = data.pricing;
  const row = data.catalog_match;
  const approval = data.manager_approval_required;
  setText('sku', row.sku);
  setText('pieces', p.total_pieces.toLocaleString());
  setText('discount', `${(p.discount_rate * 100).toFixed(0)}%`);
  setText('revenue', `CNY ${p.revenue_cny.toLocaleString(undefined, {minimumFractionDigits: 2})}`);
  setText('margin', `${p.gross_margin_percent.toFixed(2)}%`);
  setText('approval', approval ? 'YES' : 'NO');
  const status = document.querySelector('#status');
  status.textContent = approval ? 'NEED MANAGER APPROVAL' : 'READY FOR REVIEW';
  status.className = `status ${approval ? 'approval' : 'normal'}`;
  document.querySelector('#verified-inputs').innerHTML = rows({
    'Standard': row.standard,
    'Material': row.material,
    'Diameter and length': `${row.diameter} x ${row.length_mm} mm`,
    'Requested quantity': `${data.extraction.quantity} ${data.extraction.unit}`,
    'Required total pieces': p.total_pieces.toLocaleString(),
    'Packaging': `${p.pieces_per_box} pieces/box, ${p.boxes_per_carton} boxes/carton`,
    'Extraction': data.extraction.extraction_method,
  });
  document.querySelector('#calculation').innerHTML = rows({
    'List price': `CNY ${p.list_price_per_thousand_cny.toLocaleString()} / 1,000 pieces`,
    'Selling price before discount': `CNY ${p.base_selling_price_per_thousand_cny.toLocaleString(undefined, {minimumFractionDigits: 2})} / 1,000 pieces`,
    'Discounted selling price': `CNY ${p.discounted_price_per_thousand_cny.toLocaleString(undefined, {minimumFractionDigits: 2})} / 1,000 pieces`,
    'Goods cost': `CNY ${p.goods_cost_cny.toLocaleString(undefined, {minimumFractionDigits: 2})}`,
    'Small-order cost': `CNY ${p.small_order_surcharge_cny.toFixed(2)}`,
    'Total cost': `CNY ${p.total_cost_cny.toLocaleString(undefined, {minimumFractionDigits: 2})}`,
    'Gross profit': `CNY ${p.gross_profit_cny.toLocaleString(undefined, {minimumFractionDigits: 2})}`,
    'Gross margin': `${p.gross_margin_percent.toFixed(2)}%`,
  });
  setText('reply', data.customer_reply_draft);
  results.classList.remove('hidden');
}

function rows(values) {
  return Object.entries(values).map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(String(value))}</dd>`).join('');
}

function setText(id, value) { document.querySelector(`#${id}`).textContent = value; }
function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

