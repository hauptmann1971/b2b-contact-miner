function escapeHtml(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function saveToken() {
    const tokenInput = document.getElementById('apiTokenInput');
    const value = (tokenInput.value || '').trim();
    if (value) {
        localStorage.setItem('llmDataApiToken', value);
        alert('Токен сохранен локально в браузере.');
    } else {
        localStorage.removeItem('llmDataApiToken');
        alert('Токен очищен.');
    }
}

function loadSavedToken() {
    const tokenInput = document.getElementById('apiTokenInput');
    const saved = localStorage.getItem('llmDataApiToken') || '';
    tokenInput.value = saved;
}

async function loadData() {
    try {
        const token = (document.getElementById('apiTokenInput').value || '').trim();
        const response = await fetch('/api/llm-data', {
            headers: token ? { 'X-API-Key': token } : {}
        });
        if (response.status === 401) {
            throw new Error('Unauthorized (401). Укажите корректный LLM_DATA_API_TOKEN.');
        }
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();

        document.getElementById('totalSearchResults').textContent = data.stats.total_search_results || 0;
        document.getElementById('totalCrawlLogs').textContent = data.stats.total_crawl_logs || 0;
        document.getElementById('llmUsedCount').textContent = data.stats.llm_used_count || 0;
        document.getElementById('domainsWithContacts').textContent = data.stats.domains_with_contacts || 0;

        const searchTable = document.getElementById('searchResultsTable');
        if (data.search_results && data.search_results.length > 0) {
            searchTable.innerHTML = data.search_results.map(sr => {
                const responseData = sr.raw_search_response || {};
                const provider = escapeHtml(responseData.provider || 'N/A');
                const safeUrl = escapeHtml(sr.url || '-');
                const safeQuery = escapeHtml(sr.raw_search_query || '-');
                const safeRawResponse = sr.raw_search_response
                    ? escapeHtml(JSON.stringify(sr.raw_search_response, null, 2))
                    : '-';
                return `
                    <tr>
                        <td>${escapeHtml(sr.id)}</td>
                        <td>${escapeHtml(sr.keyword_id)}</td>
                        <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">${safeUrl}</td>
                        <td><div class="text-display">${safeQuery}</div></td>
                        <td>
                            <div style="margin-bottom: 5px;"><strong>Provider:</strong> <span style="color: #667eea; font-weight: bold;">${provider}</span></div>
                            <div class="json-display">${safeRawResponse}</div>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            searchTable.innerHTML = '<tr><td colspan="5" class="empty-state">Нет данных</td></tr>';
        }

        const crawlTable = document.getElementById('crawlLogsTable');
        if (data.crawl_logs && data.crawl_logs.length > 0) {
            crawlTable.innerHTML = data.crawl_logs.map(log => `
                <tr>
                    <td>${escapeHtml(log.id)}</td>
                    <td>${escapeHtml(log.domain)}</td>
                    <td><span class="badge badge-${escapeHtml(log.llm_model || 'none')}">${escapeHtml(log.llm_model || 'N/A')}</span></td>
                    <td><div class="json-display">${escapeHtml(log.llm_request ? truncateText(log.llm_request, 200) : '-')}</div></td>
                    <td><div class="json-display">${escapeHtml(log.llm_response ? truncateText(log.llm_response, 200) : '-')}</div></td>
                </tr>
            `).join('');
        } else {
            crawlTable.innerHTML = '<tr><td colspan="5" class="empty-state">Нет данных об использовании LLM</td></tr>';
        }

        const contactsTable = document.getElementById('contactsJsonTable');
        if (data.contacts_json && data.contacts_json.length > 0) {
            contactsTable.innerHTML = data.contacts_json.map(dc => {
                const contacts = dc.contacts_json || {};
                const safeContacts = escapeHtml(JSON.stringify(contacts, null, 2));
                return `
                    <tr>
                        <td>${escapeHtml(dc.id)}</td>
                        <td>${escapeHtml(dc.domain)}</td>
                        <td>${escapeHtml((contacts.emails || []).length)}</td>
                        <td>${escapeHtml((contacts.telegram || []).length)}</td>
                        <td>${escapeHtml((contacts.linkedin || []).length)}</td>
                        <td><div class="json-display">${safeContacts}</div></td>
                    </tr>
                `;
            }).join('');
        } else {
            contactsTable.innerHTML = '<tr><td colspan="6" class="empty-state">Нет данных о контактах</td></tr>';
        }
    } catch (error) {
        console.error('Error loading data:', error);
        const msg = 'Ошибка загрузки данных: ' + error.message;
        document.getElementById('searchResultsTable').innerHTML = `<tr><td colspan="5" class="empty-state">${msg}</td></tr>`;
        document.getElementById('crawlLogsTable').innerHTML = `<tr><td colspan="5" class="empty-state">${msg}</td></tr>`;
        document.getElementById('contactsJsonTable').innerHTML = `<tr><td colspan="6" class="empty-state">${msg}</td></tr>`;
    }
}

function truncateText(text, maxLength) {
    if (!text) return '-';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

loadSavedToken();
loadData();
