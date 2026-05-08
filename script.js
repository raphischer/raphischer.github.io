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

function parseAuthors(authorStr) {
  if (!authorStr) return 'Unknown author';
  const authors = authorStr.split(' and ').map(a => {
    const parts = a.trim().split(', ');
    if (parts.length === 2) {
      return parts[1] + ' ' + parts[0];
    } else {
      return a.trim();
    }
  });
  return authors.join(', ');
}

function getSortDate(pub) {
  const dateStr = pub.fields.date || pub.fields.year || '0';
  if (dateStr.includes('-')) {
    return new Date(dateStr);
  } else {
    return new Date(dateStr + '-01-01');
  }
}

function renderPublications(entries) {
  const container = document.getElementById('publication-list');
  container.innerHTML = '';
  const sorted = entries.sort((a, b) => getSortDate(b) - getSortDate(a));

  sorted.forEach(pub => {
    const card = document.createElement('article');
    card.className = 'publication-card';
    let title = pub.fields.title || pub.key;
    title = title.replace(/\{/g, '').replace(/\}/g, '');
    const authors = parseAuthors(pub.fields.author);
    let journal = pub.fields.journal || pub.fields.journaltitle || pub.fields.booktitle || '';
    journal = journal.replace(/\{/g, '').replace(/\}/g, '');
    let year = pub.fields.year || pub.fields.date || '';
    let doi = (pub.fields.doi || '').replace(/\{/g, '').replace(/\}/g, '');
    let url = (pub.fields.url || '').replace(/\{/g, '').replace(/\}/g, '');

    card.innerHTML = `
      <h3>${title}</h3>
      <p class="publication-meta">${authors}${journal ? ' · ' + journal : ''}${year ? ' · ' + year : ''}</p>
      ${doi ? `<p><a href="https://doi.org/${doi}" target="_blank">DOI: ${doi}</a></p>` : url ? `<p><a href="${url}" target="_blank">Link</a></p>` : ''}
    `;
    container.appendChild(card);
  });
}

function renderCV(data) {
  const personal = data.personal || {};
  document.getElementById('profile-name').textContent = personal.name;
  document.getElementById('profile-title').textContent = personal.description;
  document.getElementById('summary').textContent = data.statement;

  // Set links in hero
  document.getElementById('webpage-link').href = personal.webpage || '#';
  document.getElementById('linkedin-link').href = personal.linkedin || '#';
  document.getElementById('scholar-link').href = personal.scholar || '#';
  document.getElementById('github-link').href = personal.github || '#';
  document.getElementById('contact-link').href = 'mailto:' + (personal.email || '');

  const sections = document.getElementById('cv-sections');
  sections.innerHTML = '';
  (data.sections || []).forEach(section => {
    const card = document.createElement('div');
    card.className = 'cv-section';
    card.innerHTML = `<h3>${section.heading}</h3>${(section.items || []).map(item => {
      if (section.heading === 'Awards & Scholarships' || section.heading === 'Volunteering & Activities') {
        return `
          <div class="cv-item">
            <strong>${item.title} (${item.organization || ''})</strong>
            <p class="cv-meta">${(item.highlights || []).map(h => '' + h + '').join('')} ${item.period ? '(' + item.period + ')' : ''}</p>
          </div>
        `;
      } else {
        return `
          <div class="cv-item">
            <strong>${item.title}</strong>
            <p class="cv-meta">${item.period || ''} · ${item.organization || ''}</p>
            ${(item.highlights || []).map(h => `<p>${h}</p>`).join('')}
          </div>
        `;
      }
    }).join('')}`;
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
