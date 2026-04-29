(function () {
    const toggle = document.getElementById('autoRefreshToggle');
    let timer = null;
    if (!toggle) return;
    toggle.addEventListener('change', function () {
        if (toggle.checked) {
            timer = setInterval(function () { location.reload(); }, 10000);
        } else if (timer) {
            clearInterval(timer);
            timer = null;
        }
    });
})();
