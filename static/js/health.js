let autoRefreshInterval = null;

function safeNumber(value, fallback = 0) {
    const num = Number(value);
    return Number.isFinite(num) ? num : fallback;
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString("ru-RU");
}

function getStatusBadge(status) {
    if (status === "healthy" || status === "alive" || status === "ready") {
        return '<span class="service-status badge-success">✓ ' + status + "</span>";
    }
    if (status === "unhealthy" || status === "not_ready") {
        return '<span class="service-status badge-danger">✗ ' + status + "</span>";
    }
    if (status === "not_configured") {
        return '<span class="service-status badge-warning">⚙ не настроено</span>';
    }
    if (status === "not_running") {
        return '<span class="service-status badge-warning">⏸ не запущено</span>';
    }
    return '<span class="service-status badge-warning">⏳ ' + status + "</span>";
}

function loadFullHealth() {
    const btn = document.getElementById("btn-full-health");
    if (btn) {
        btn.classList.add("loading");
        btn.textContent = "⏳ Загрузка...";
    }

    fetch("/health", { cache: "no-cache" })
        .then((response) => {
            if (!response.ok) {
                throw new Error("HTTP error! status: " + response.status);
            }
            return response.json();
        })
        .then((data) => {
            const overallStatus = document.getElementById("overall-status");
            if (data.status === "healthy") {
                overallStatus.className = "overall-status overall-healthy";
                overallStatus.innerHTML = '<span class="status-indicator status-healthy"></span> Система работает нормально';
            } else {
                overallStatus.className = "overall-status overall-unhealthy";
                overallStatus.innerHTML = '<span class="status-indicator status-unhealthy"></span> Обнаружены проблемы';
            }

            let html = '<div class="timestamp">Последняя проверка: ' + formatTimestamp(data.timestamp) + "</div>";

            if (data.database) {
                const dbStatus = data.database === "healthy" ? "healthy" : "unhealthy";
                html += `
                    <div class="service-card">
                        <div class="service-header">
                            <span class="service-name">Database</span>
                            ${getStatusBadge(dbStatus)}
                        </div>
                        <p class="text-muted mt-10">${data.database}</p>
                    </div>
                `;
            }

            if (data.web_server) {
                html += `
                    <div class="service-card">
                        <div class="service-header">
                            <span class="service-name">Web Server</span>
                            ${getStatusBadge("healthy")}
                        </div>
                        <p class="text-muted mt-10">${data.web_server}</p>
                    </div>
                `;
            }

            if (data.monitoring_service) {
                const monStatus = data.monitoring_service === "running" ? "healthy" : "warning";
                html += `
                    <div class="service-card">
                        <div class="service-header">
                            <span class="service-name">Monitoring Service</span>
                            ${getStatusBadge(monStatus)}
                        </div>
                        <p class="text-muted mt-10">${data.monitoring_service}</p>
                    </div>
                `;
            }

            document.getElementById("full-health").innerHTML = html;
        })
        .catch((error) => {
            document.getElementById("full-health").innerHTML =
                '<p class="text-danger">Ошибка загрузки: ' + error.message + "</p>";
        })
        .finally(() => {
            if (btn) {
                btn.classList.remove("loading");
                btn.textContent = "🔄 Обновить";
            }
        });
}

function loadLiveness() {
    fetch("/health/live", { cache: "no-cache" })
        .then((response) => response.json())
        .then((data) => {
            let html = '<div class="timestamp">Время: ' + formatTimestamp(data.timestamp) + "</div>";
            html +=
                '<div class="service-card"><div class="service-header"><span class="service-name">Статус приложения</span>' +
                getStatusBadge(data.status) +
                "</div></div>";
            document.getElementById("liveness").innerHTML = html;
        })
        .catch((error) => {
            document.getElementById("liveness").innerHTML =
                '<p class="text-danger">Ошибка загрузки: ' + error.message + "</p>";
        });
}

function loadReadiness() {
    fetch("/health/ready", { cache: "no-cache" })
        .then((response) => response.json())
        .then((data) => {
            let html = '<div class="timestamp">Время: ' + formatTimestamp(data.timestamp) + "</div>";
            html +=
                '<div class="service-card"><div class="service-header"><span class="service-name">Готовность к работе</span>' +
                getStatusBadge(data.status) +
                "</div></div>";
            if (data.error) {
                html += '<p class="text-danger mt-10">Ошибка: ' + data.error + "</p>";
            }
            document.getElementById("readiness").innerHTML = html;
        })
        .catch((error) => {
            document.getElementById("readiness").innerHTML =
                '<p class="text-danger">Ошибка загрузки: ' + error.message + "</p>";
        });
}

function toggleAutoRefresh() {
    const checkbox = document.getElementById("auto-refresh");
    if (checkbox.checked) {
        autoRefreshInterval = setInterval(() => {
            loadFullHealth();
            loadLiveness();
            loadReadiness();
        }, 10000);
    } else {
        clearInterval(autoRefreshInterval);
    }
}

async function loadCrawlerSettings() {
    try {
        const response = await fetch("/api/crawler-settings");
        const data = await response.json();

        const container = document.getElementById("crawlerSettings");
        if (!container) {
            return;
        }
        const domainCrawlTimeout = safeNumber(data.domain_crawl_timeout);
        const requestTimeout = safeNumber(data.request_timeout);
        const maxPagesPerDomain = safeNumber(data.max_pages_per_domain);
        const searchResultsPerKeyword = safeNumber(data.search_results_per_keyword);
        const concurrentBrowsers = safeNumber(data.concurrent_browsers);
        const delayBetweenRequests = safeNumber(data.delay_between_requests);
        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Domain Crawl Timeout</span>
                    </div>
                    <p style="font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;">${domainCrawlTimeout}s</p>
                    <p class="text-muted" style="font-size: 0.9em;">Максимальное время на crawling одного домена</p>
                </div>
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Request Timeout</span>
                    </div>
                    <p style="font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;">${requestTimeout}s</p>
                    <p class="text-muted" style="font-size: 0.9em;">Timeout на одну страницу</p>
                </div>
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Max Pages per Domain</span>
                    </div>
                    <p style="font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;">${maxPagesPerDomain}</p>
                    <p class="text-muted" style="font-size: 0.9em;">Максимум страниц на домен</p>
                </div>
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Search Results per Keyword</span>
                    </div>
                    <p style="font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;">${searchResultsPerKeyword}</p>
                    <p class="text-muted" style="font-size: 0.9em;">Количество сайтов для обработки</p>
                </div>
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Concurrent Browsers</span>
                    </div>
                    <p style="font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;">${concurrentBrowsers}</p>
                    <p class="text-muted" style="font-size: 0.9em;">Параллельных браузеров</p>
                </div>
                <div class="service-card">
                    <div class="service-header">
                        <span class="service-name">Delay Between Requests</span>
                    </div>
                    <p style="font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;">${delayBetweenRequests}s</p>
                    <p class="text-muted" style="font-size: 0.9em;">Задержка между запросами</p>
                </div>
            </div>
        `;
    } catch (error) {
        document.getElementById("crawlerSettings").innerHTML =
            '<p class="text-danger">Ошибка загрузки настроек</p>';
    }
}

loadFullHealth();
loadLiveness();
loadReadiness();
loadCrawlerSettings();
