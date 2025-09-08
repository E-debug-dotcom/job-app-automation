let jobsData = [];

function setupCustomSelect(wrapperId, hiddenId, options, defaultLabel) {
  const hiddenSelect = document.getElementById(hiddenId);
  const wrapper = document.getElementById(wrapperId);
  const button = wrapper.querySelector('.custom-select__button');
  const menu = wrapper.querySelector('.custom-select__menu');

  hiddenSelect.innerHTML = '';
  menu.innerHTML = '';

  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = defaultLabel;
  hiddenSelect.appendChild(defaultOpt);

  const allValues = [''].concat(options);
  allValues.forEach((value, idx) => {
    if (idx > 0) {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = value;
      hiddenSelect.appendChild(opt);
    }
    const li = document.createElement('li');
    li.className = 'custom-select__option';
    li.setAttribute('role', 'option');
    li.setAttribute('data-value', value);
    li.textContent = value || defaultLabel;
    if (idx === 0) li.setAttribute('aria-selected', 'true');
    menu.appendChild(li);
  });

  button.addEventListener('click', () => {
    wrapper.classList.toggle('open');
    button.setAttribute('aria-expanded', wrapper.classList.contains('open'));
    menu.style.width = wrapper.clientWidth + 'px';
  });

  menu.addEventListener('click', (e) => {
    const item = e.target.closest('.custom-select__option');
    if (!item) return;
    const val = item.getAttribute('data-value') || '';
    menu.querySelectorAll('[aria-selected="true"]').forEach(n => n.removeAttribute('aria-selected'));
    item.setAttribute('aria-selected', 'true');
    button.firstChild.nodeValue = (val || defaultLabel) + ' ';
    hiddenSelect.value = val;
    hiddenSelect.dispatchEvent(new Event('change', { bubbles: true }));
    wrapper.classList.remove('open');
    button.setAttribute('aria-expanded', 'false');
  });
}

async function fetchData() {
  const [jobsRes, companiesRes, locationsRes] = await Promise.all([
    fetch('/jobs'),
    fetch('/companies'),
    fetch('/locations')
  ]);
  jobsData = await jobsRes.json();
  const companies = await companiesRes.json();
  const locations = await locationsRes.json();

  setupCustomSelect('companyCustom', 'companyFilter', companies, 'All Companies');
  setupCustomSelect('locationCustom', 'locationFilter', locations, 'All Locations');

  renderJobs();
}

function highlightMatch(text, searchTerm) {
  if (!searchTerm) return text;
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

function renderJobs() {
  const company = document.getElementById('companyFilter').value.toLowerCase();
  const location = document.getElementById('locationFilter').value.toLowerCase();
  const searchTerm = document.getElementById('searchInput').value.toLowerCase();
  const tbody = document.querySelector('#jobsTable tbody');
  tbody.innerHTML = '';

  const filtered = jobsData.filter(job => {
    const matchCompany = !company || (job.company && job.company.toLowerCase() === company);
    const matchLocation = !location || (job.location && job.location.toLowerCase() === location);
    const matchSearch = !searchTerm || (job.title && job.title.toLowerCase().includes(searchTerm));
    return matchCompany && matchLocation && matchSearch;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" id="noResults">No jobs match your search or filters.</td></tr>`;
    return;
  }

  filtered.forEach((job, index) => {
    const tr = document.createElement('tr');
    tr.style.opacity = 0;
    tr.innerHTML = `
      <td>${highlightMatch(job.company ?? '', searchTerm)}</td>
      <td>${highlightMatch(job.location ?? '', searchTerm)}</td>
      <td>${highlightMatch(job.title ?? '', searchTerm)}</td>
      <td><a href="${job.url ?? '#'}" target="_blank">Apply</a></td>
    `;
    tbody.appendChild(tr);
    setTimeout(() => { tr.style.opacity = 1; }, index * 50);
  });
}

// Event listeners
document.getElementById('companyFilter').addEventListener('change', renderJobs);
document.getElementById('locationFilter').addEventListener('change', renderJobs);
document.getElementById('searchInput').addEventListener('input', renderJobs);

document.getElementById('clearCompany').addEventListener('click', () => {
  const hidden = document.getElementById('companyFilter');
  hidden.value = '';
  hidden.dispatchEvent(new Event('change', { bubbles: true }));
  const wrapper = document.getElementById('companyCustom');
  wrapper.querySelector('.custom-select__button').firstChild.nodeValue = 'All Companies ';
  wrapper.querySelectorAll('[aria-selected="true"]').forEach(n => n.removeAttribute('aria-selected'));
  wrapper.querySelector('.custom-select__option').setAttribute('aria-selected', 'true');
});

document.getElementById('clearLocation').addEventListener('click', () => {
  const hidden = document.getElementById('locationFilter');
  hidden.value = '';
  hidden.dispatchEvent(new Event('change', { bubbles: true }));
  const wrapper = document.getElementById('locationCustom');
  wrapper.querySelector('.custom-select__button').firstChild.nodeValue = 'All Locations ';
  wrapper.querySelectorAll('[aria-selected="true"]').forEach(n => n.removeAttribute('aria-selected'));
  wrapper.querySelector('.custom-select__option').setAttribute('aria-selected', 'true');
});

// Initialize
fetchData();
