let jobsData = [];

function deriveExperience(job) {
  const explicit = job.experience_level || job.experience || '';
  if (explicit) return explicit;

  const title = (job.title || '').toLowerCase();
  if (/\b(intern|junior|jr|entry)\b/.test(title)) return 'Entry';
  if (/\b(staff|principal|architect|director|head|vp|executive|chief)\b/.test(title)) return 'Executive';
  if (/\b(senior|sr|lead)\b/.test(title)) return 'Senior';
  if (title) return 'Mid';
  return '';
}

function deriveWorkType(job) {
  const explicit = job.work_type || '';
  if (explicit) return explicit;

  const location = (job.location || '').toLowerCase();
  const title = (job.title || '').toLowerCase();
  const combined = `${location} ${title}`;

  if (combined.includes('hybrid')) return 'Hybrid';
  if (combined.includes('remote')) return 'Remote';
  if (combined.includes('on-site') || combined.includes('onsite')) return 'On-Site';

  return '';
}

function uniqSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
}

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
    menu.style.width = `${wrapper.clientWidth}px`;
  });

  menu.addEventListener('click', (e) => {
    const item = e.target.closest('.custom-select__option');
    if (!item) return;

    const val = item.getAttribute('data-value') || '';
    menu.querySelectorAll('[aria-selected="true"]').forEach((n) => n.removeAttribute('aria-selected'));
    item.setAttribute('aria-selected', 'true');
    button.firstChild.nodeValue = `${val || defaultLabel} `;
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

  const experienceLevels = uniqSorted(jobsData.map(deriveExperience));
  const workTypes = uniqSorted(jobsData.map(deriveWorkType));

  setupCustomSelect('companyCustom', 'companyFilter', companies, 'All Companies');
  setupCustomSelect('locationCustom', 'locationFilter', locations, 'All Locations');
  setupCustomSelect('experienceCustom', 'experienceFilter', experienceLevels, 'All Experience Levels');
  setupCustomSelect('workTypeCustom', 'workTypeFilter', workTypes, 'All Work Types');

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
  const experience = document.getElementById('experienceFilter').value.toLowerCase();
  const workType = document.getElementById('workTypeFilter').value.toLowerCase();
  const tbody = document.querySelector('#jobsTable tbody');
  tbody.innerHTML = '';

  const filtered = jobsData.filter((job) => {
    const companyText = (job.company || '').toLowerCase();
    const locationText = (job.location || '').toLowerCase();
    const titleText = (job.title || '').toLowerCase();
    const experienceText = deriveExperience(job).toLowerCase();
    const workTypeText = deriveWorkType(job).toLowerCase();

    const matchCompany = !company || companyText === company;
    const matchLocation = !location || locationText === location;
    const matchExperience = !experience || experienceText === experience;
    const matchWorkType = !workType || workTypeText === workType;
    const matchSearch = !searchTerm
      || titleText.includes(searchTerm)
      || companyText.includes(searchTerm)
      || locationText.includes(searchTerm);

    return matchCompany && matchLocation && matchExperience && matchWorkType && matchSearch;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" id="noResults">No jobs match your search or filters.</td></tr>';
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

function clearCustomSelect(hiddenId, wrapperId, defaultLabel) {
  const hidden = document.getElementById(hiddenId);
  hidden.value = '';
  hidden.dispatchEvent(new Event('change', { bubbles: true }));

  const wrapper = document.getElementById(wrapperId);
  wrapper.querySelector('.custom-select__button').firstChild.nodeValue = `${defaultLabel} `;
  wrapper.querySelectorAll('[aria-selected="true"]').forEach((n) => n.removeAttribute('aria-selected'));
  wrapper.querySelector('.custom-select__option').setAttribute('aria-selected', 'true');
}

// Event listeners
document.getElementById('companyFilter').addEventListener('change', renderJobs);
document.getElementById('locationFilter').addEventListener('change', renderJobs);
document.getElementById('experienceFilter').addEventListener('change', renderJobs);
document.getElementById('workTypeFilter').addEventListener('change', renderJobs);
document.getElementById('searchInput').addEventListener('input', renderJobs);

document.getElementById('clearCompany').addEventListener('click', () => {
  clearCustomSelect('companyFilter', 'companyCustom', 'All Companies');
});

document.getElementById('clearLocation').addEventListener('click', () => {
  clearCustomSelect('locationFilter', 'locationCustom', 'All Locations');
});

document.getElementById('clearExperience').addEventListener('click', () => {
  clearCustomSelect('experienceFilter', 'experienceCustom', 'All Experience Levels');
});

document.getElementById('clearWorkType').addEventListener('click', () => {
  clearCustomSelect('workTypeFilter', 'workTypeCustom', 'All Work Types');
});

// Initialize
fetchData();
