const form = document.querySelector('#ask');
const input = document.querySelector('#prompt');
const btn   = document.querySelector('#go');
const grid  = document.querySelector('#grid');

// Keeps lightweight state so the model can avoid duplicating modules.
const modules = []; // {title, summary, html}

function appendModule(mod) {
  const card = document.createElement('article');
  card.className = 'card';

  const h = document.createElement('header');
  h.textContent = mod.title || 'Module';

  const small = document.createElement('span');
  small.className = 'muted';
  small.textContent = mod.summary || '';
  h.appendChild(small);

  const body = document.createElement('section');
  body.className = 'content';

  // Insert trusted markup returned by the model.
  // In a real app this must be sanitized to prevent XSS attacks. WARNING: another vulerability!
  body.innerHTML = mod.html;

  card.appendChild(h);
  card.appendChild(body);
  grid.prepend(card); // newest first
}

/**
 * @summary Requests a new dashboard module from the backend API.
 */
async function generate(prompt) {
  btn.disabled = true;

  const res = await fetch('/api/generate-module', {
    method: 'POST',
    headers: { 'Content-Type':'application/json' },
    body: JSON.stringify({ prompt, priorModules: modules.map(({title, summary}) => ({title, summary})) })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    alert('Error: ' + (err.error || res.statusText));
    btn.disabled = false;
    return;
  }

  const mod = await res.json();
  console.log('Generated module:', mod);

  modules.push(mod);
  appendModule(mod);
  btn.disabled = false;
}

form.addEventListener('submit', () => {
  const q = (input.value || '').trim();
  if (!q) return;
  generate(q);
  input.value = '';
});
