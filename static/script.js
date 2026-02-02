let articles = [];
let selectedIds = new Set();
let currentEpub = null;
let sortColumn = 'created_at';
let sortDirection = 'desc';

const articlesBody = document.getElementById('articles-body');
const articlesContainer = document.getElementById('articles-container');
const loadingEl = document.getElementById('loading');
const loadingText = document.getElementById('loading-text');
const errorEl = document.getElementById('error');
const selectedCount = document.getElementById('selected-count');
const totalReadingTime = document.getElementById('total-reading-time');
const selectAllBtn = document.getElementById('select-all-btn');
const deselectAllBtn = document.getElementById('deselect-all-btn');
const refreshBtn = document.getElementById('refresh-btn');
const createSendBtn = document.getElementById('create-send-btn');
const downloadBtn = document.getElementById('download-btn');
const locationFilter = document.getElementById('location-filter');
const searchInput = document.getElementById('search-input');
const progressModal = document.getElementById('progress-modal');
const progressText = document.getElementById('progress-text');
const successModal = document.getElementById('success-modal');
const successText = document.getElementById('success-text');
const closeSuccessBtn = document.getElementById('close-success-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchArticles();
    setupEventListeners();
});

function setupEventListeners() {
    selectAllBtn.addEventListener('click', selectAll);
    deselectAllBtn.addEventListener('click', deselectAll);
    refreshBtn.addEventListener('click', () => fetchArticles());
    createSendBtn.addEventListener('click', createAndSend);
    downloadBtn.addEventListener('click', downloadEpub);
    locationFilter.addEventListener('change', () => fetchArticles());
    searchInput.addEventListener('input', debounce(filterArticles, 300));
    closeSuccessBtn.addEventListener('click', () => successModal.classList.add('hidden'));

    // Sort headers
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const column = th.dataset.sort;
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }
            updateSortIcons();
            renderArticles();
        });
    });
    updateSortIcons();
}

function updateSortIcons() {
    document.querySelectorAll('.sortable').forEach(th => {
        const icon = th.querySelector('.sort-icon');
        if (th.dataset.sort === sortColumn) {
            icon.textContent = sortDirection === 'asc' ? ' ▲' : ' ▼';
        } else {
            icon.textContent = '';
        }
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function handleUnauthorized(response) {
    if (response.status === 401) {
        window.location.href = '/login';
        return true;
    }
    return false;
}

async function fetchArticles() {
    showLoading('Loading articles...');
    hideError();
    articlesContainer.classList.add('hidden');
    selectedIds.clear();
    currentEpub = null;
    updateSelectionInfo();

    const location = locationFilter.value;
    const url = location ? `/api/articles?location=${location}` : '/api/articles';

    try {
        const response = await fetch(url);
        if (handleUnauthorized(response)) return;
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch articles');
        }

        articles = data.articles;
        renderArticles();
        hideLoading();
        articlesContainer.classList.remove('hidden');
    } catch (err) {
        hideLoading();
        showError(err.message);
    }
}

function renderArticles() {
    const searchTerm = searchInput.value.toLowerCase();
    let filtered = articles.filter(article => {
        if (!searchTerm) return true;
        return (
            article.title.toLowerCase().includes(searchTerm) ||
            (article.author && article.author.toLowerCase().includes(searchTerm)) ||
            (article.site_name && article.site_name.toLowerCase().includes(searchTerm)) ||
            (article.summary && article.summary.toLowerCase().includes(searchTerm))
        );
    });

    // Sort
    filtered.sort((a, b) => {
        let aVal = a[sortColumn] || '';
        let bVal = b[sortColumn] || '';

        // Handle numeric sorting for word_count
        if (sortColumn === 'word_count') {
            aVal = aVal || 0;
            bVal = bVal || 0;
            return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        }

        // String comparison for everything else
        aVal = String(aVal).toLowerCase();
        bVal = String(bVal).toLowerCase();

        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    articlesBody.innerHTML = '';

    if (filtered.length === 0) {
        articlesBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: #666;">
                    No articles found
                </td>
            </tr>
        `;
        return;
    }

    filtered.forEach(article => {
        const tr = document.createElement('tr');
        tr.dataset.id = article.id;

        if (selectedIds.has(article.id)) {
            tr.classList.add('selected');
        }

        const wordCount = article.word_count || 0;
        const readingMins = Math.ceil(wordCount / 200);
        const savedDate = article.created_at ?
            new Date(article.created_at).toLocaleDateString() : '';

        tr.innerHTML = `
            <td class="checkbox-col">
                <input type="checkbox" ${selectedIds.has(article.id) ? 'checked' : ''}>
            </td>
            <td>
                <div class="article-title">
                    ${article.source_url ?
                        `<a href="${article.source_url}" target="_blank" title="${article.title}">${article.title}</a>` :
                        article.title}
                </div>
                ${article.summary ? `<div class="article-summary" title="${article.summary}">${article.summary}</div>` : ''}
            </td>
            <td>${article.author || '-'}</td>
            <td>${article.site_name || '-'}</td>
            <td>${wordCount.toLocaleString()} <small>(~${readingMins}m)</small></td>
            <td>
                <span class="location-badge ${article.location}">${article.location || '-'}</span>
            </td>
            <td>${savedDate}</td>
        `;

        const checkbox = tr.querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', () => toggleSelection(article.id, checkbox.checked));
        tr.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'A') {
                checkbox.checked = !checkbox.checked;
                toggleSelection(article.id, checkbox.checked);
            }
        });

        articlesBody.appendChild(tr);
    });
}

function toggleSelection(id, selected) {
    if (selected) {
        selectedIds.add(id);
    } else {
        selectedIds.delete(id);
    }

    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (row) {
        row.classList.toggle('selected', selected);
    }

    updateSelectionInfo();
    currentEpub = null;
}

function selectAll() {
    const visibleRows = articlesBody.querySelectorAll('tr[data-id]');
    visibleRows.forEach(row => {
        const id = row.dataset.id;
        selectedIds.add(id);
        row.classList.add('selected');
        row.querySelector('input[type="checkbox"]').checked = true;
    });
    updateSelectionInfo();
    currentEpub = null;
}

function deselectAll() {
    selectedIds.clear();
    articlesBody.querySelectorAll('tr').forEach(row => {
        row.classList.remove('selected');
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (checkbox) checkbox.checked = false;
    });
    updateSelectionInfo();
    currentEpub = null;
}

function updateSelectionInfo() {
    selectedCount.textContent = selectedIds.size;

    // Calculate total reading time
    let totalWords = 0;
    articles.forEach(article => {
        if (selectedIds.has(article.id)) {
            totalWords += article.word_count || 0;
        }
    });

    if (totalWords > 0) {
        const mins = Math.ceil(totalWords / 200);
        totalReadingTime.textContent = ` (~${mins} min read, ${totalWords.toLocaleString()} words)`;
    } else {
        totalReadingTime.textContent = '';
    }

    const hasSelection = selectedIds.size > 0;
    createSendBtn.disabled = !hasSelection;
    downloadBtn.disabled = !hasSelection;
}

function filterArticles() {
    renderArticles();
}

async function createAndSend() {
    if (selectedIds.size === 0) return;

    showProgress('Fetching full article content...');

    try {
        // Create EPUB
        const createResponse = await fetch('/api/create-epub', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ article_ids: Array.from(selectedIds) })
        });

        if (handleUnauthorized(createResponse)) return;
        const createData = await createResponse.json();

        if (!createResponse.ok) {
            throw new Error(createData.error || 'Failed to create EPUB');
        }

        currentEpub = createData;
        showProgress('Creating EPUB...');

        // Small delay for UX
        await new Promise(r => setTimeout(r, 500));

        showProgress('Sending to Kindle...');

        // Send to Kindle
        const sendResponse = await fetch('/api/send-to-kindle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: createData.filepath,
                filename: createData.filename
            })
        });

        if (handleUnauthorized(sendResponse)) return;
        const sendData = await sendResponse.json();

        if (!sendResponse.ok) {
            throw new Error(sendData.error || 'Failed to send to Kindle');
        }

        hideProgress();
        showSuccess(`Sent ${createData.article_count} articles to your Kindle!`);

    } catch (err) {
        hideProgress();
        showError(err.message);
    }
}

async function downloadEpub() {
    if (selectedIds.size === 0) return;

    showProgress('Creating EPUB...');

    try {
        // Create EPUB if not already created
        if (!currentEpub) {
            const createResponse = await fetch('/api/create-epub', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ article_ids: Array.from(selectedIds) })
            });

            if (handleUnauthorized(createResponse)) return;
            const createData = await createResponse.json();

            if (!createResponse.ok) {
                throw new Error(createData.error || 'Failed to create EPUB');
            }

            currentEpub = createData;
        }

        showProgress('Preparing download...');

        // Download
        const downloadResponse = await fetch('/api/download-epub', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: currentEpub.filepath,
                filename: currentEpub.filename
            })
        });

        if (handleUnauthorized(downloadResponse)) return;
        if (!downloadResponse.ok) {
            const errData = await downloadResponse.json();
            throw new Error(errData.error || 'Failed to download EPUB');
        }

        const blob = await downloadResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = currentEpub.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        hideProgress();

    } catch (err) {
        hideProgress();
        showError(err.message);
    }
}

function showLoading(text) {
    loadingText.textContent = text;
    loadingEl.classList.remove('hidden');
}

function hideLoading() {
    loadingEl.classList.add('hidden');
}

function showError(message) {
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function hideError() {
    errorEl.classList.add('hidden');
}

function showProgress(text) {
    progressText.textContent = text;
    progressModal.classList.remove('hidden');
}

function hideProgress() {
    progressModal.classList.add('hidden');
}

function showSuccess(message) {
    successText.textContent = message;
    successModal.classList.remove('hidden');
}
