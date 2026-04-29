function loadStats() {
    const display = document.getElementById("stats-display");
    display.classList.add("active");
    display.innerHTML = '<p class="text-muted">Загрузка...</p>';

    fetch("/api/stats")
        .then((response) => response.json())
        .then((data) => {
            let html = '<div class="stats-grid">';
            html += '<div class="stat-item"><div class="stat-value">' + data.total_keywords + '</div><div class="stat-label">Ключевых слов</div></div>';
            html += '<div class="stat-item"><div class="stat-value">' + data.processed_keywords + '</div><div class="stat-label">Обработано</div></div>';
            html += '<div class="stat-item"><div class="stat-value">' + data.total_domains + '</div><div class="stat-label">Доменов</div></div>';
            html += '<div class="stat-item"><div class="stat-value">' + data.total_contacts + '</div><div class="stat-label">Контактов</div></div>';
            html += "</div>";

            html += '<div class="stats-grid mt-15">';
            for (const [type, count] of Object.entries(data.contacts_by_type)) {
                const icon = type === "email" ? "📧" : type === "telegram" ? "✈️" : type === "linkedin" ? "💼" : "📱";
                html += '<div class="stat-item"><div class="stat-value">' + icon + " " + count + '</div><div class="stat-label">' + type.charAt(0).toUpperCase() + type.slice(1) + "</div></div>";
            }
            html += "</div>";

            html += '<pre class="mt-15">' + JSON.stringify(data, null, 2) + "</pre>";
            display.innerHTML = html;
        })
        .catch((error) => {
            display.innerHTML = '<p class="text-danger">Ошибка: ' + error.message + "</p>";
        });
}

function loadKeywords() {
    const display = document.getElementById("keywords-display");
    display.classList.add("active");
    display.innerHTML = '<p class="text-muted">Загрузка...</p>';

    fetch("/api/keywords")
        .then((response) => response.json())
        .then((data) => {
            if (data.length === 0) {
                display.innerHTML = '<p class="text-muted">Нет ключевых слов в базе данных</p><pre>[]</pre>';
                return;
            }

            let html = '<p class="mb-10"><strong>Всего ключевых слов: ' + data.length + "</strong></p>";
            html += "<pre>" + JSON.stringify(data, null, 2) + "</pre>";
            display.innerHTML = html;
        })
        .catch((error) => {
            display.innerHTML = '<p class="text-danger">Ошибка: ' + error.message + "</p>";
        });
}
