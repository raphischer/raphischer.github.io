async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Unable to load ${path}`);
  return await response.json();
}

function texEscape(value) {
  return value.replace(/[&%$#_{}~^\\]/g, "\\$&");
}

function parseBibTeX(content) {
  const entries = [];
  const entryRegex = /@(\w+)\s*\{\s*([^,]+),([\s\S]*?)\n\s*\}\s*(?=@|$)/g;
  let match;
  while ((match = entryRegex.exec(content)) !== null) {
    const [, type, key, body] = match;
    const fields = {};
    const fieldRegex = /([a-zA-Z]+)\s*=\s*\{([\s\S]*?)\}(?:,|\s*$)/g;
    let fieldMatch;
    while ((fieldMatch = fieldRegex.exec(body)) !== null) {
      fields[fieldMatch[1].toLowerCase()] = fieldMatch[2].trim();
    }
    entries.push({ type, key, fields });
  }
  return entries;
}

function renderPublications(entries) {
  const container = document.getElementById('publication-list');
  container.innerHTML = '';
  const sorted = entries.sort((a, b) => {
    const yearA = parseInt(a.fields.year || '0', 10);
    const yearB = parseInt(b.fields.year || '0', 10);
    return yearB - yearA;
  });

  sorted.forEach(pub => {
    const card = document.createElement('article');
    card.className = 'publication-card';
    const title = pub.fields.title || pub.key;
    const authors = pub.fields.author || 'Unknown author';
    const journal = pub.fields.journal || pub.fields.booktitle || '';
    const year = pub.fields.year || '';

    card.innerHTML = `
      <h3>${title}</h3>
      <p class="publication-meta">${authors}${journal ? ' · ' + journal : ''}${year ? ' · ' + year : ''}</p>
    `;
    container.appendChild(card);
  });
}

function renderCV(data) {
  const personal = data.personal || {};
  document.getElementById('profile-name').textContent = personal.name;
  document.getElementById('profile-title').textContent = personal.role;
  document.getElementById('summary').textContent = data.statement;

  const summaryContainer = document.getElementById('cv-summary');
  summaryContainer.innerHTML = `
    <div class="cv-card">
      <h3>Contact</h3>
      <p class="cv-meta">${personal.email || 'email@example.com'}</p>
      <p class="cv-meta">${personal.affiliation || 'Affiliation'}</p>
    </div>
    <div class="cv-card">
      <h3>Links</h3>
      <p><a href="${personal.webpage || '#'}" target="_blank">Webpage</a> · 
         <a href="${personal.linkedin || '#'}" target="_blank">LinkedIn</a></p>
      <p><a href="${personal.scholar || '#'}" target="_blank">Google Scholar</a> · 
         <a href="${personal.github || '#'}" target="_blank">GitHub</a></p>
    </div>
  `;

  const sections = document.getElementById('cv-sections');
  sections.innerHTML = '';
  (data.sections || []).forEach(section => {
    const card = document.createElement('div');
    card.className = 'cv-section';
    card.innerHTML = `<h3>${section.heading}</h3>${(section.items || []).map(item => `
      <div class="cv-item">
        <strong>${item.title}</strong>
        <p class="cv-meta">${item.period || ''} · ${item.organization || ''}</p>
        ${(item.highlights || []).map(h => `<p>${h}</p>`).join('')}
      </div>
    `).join('')}`;
    sections.appendChild(card);
  });
}

async function init() {
  try {
    const cvData = await fetchJson('data/cv.json');
    renderCV(cvData);
  } catch (error) {
    console.error('CV data load error:', error);
  }

  try {
    const bibText = await fetch('publications/references.bib').then(resp => resp.text());
    const publications = parseBibTeX(bibText);
    renderPublications(publications);
  } catch (error) {
    console.error('Publications data load error:', error);
  }
}

init();
