// =========================
// モーダル操作
// =========================
function showModal(id) {
    const el = document.getElementById(id);
    if (!el) return;

    bootstrap.Modal.getOrCreateInstance(el).show();
}

function hideModal(id) {
    const el = document.getElementById(id);
    if (!el) return;

    const modal = bootstrap.Modal.getInstance(el);
    if (modal) modal.hide();
}

// =========================
// API
// =========================
async function apiFetch(url, options = {}) {

    const res = await fetch(url, options);

    if (!res.ok) {
        let message = `HTTP ${res.status}`;

        try {
            const data = await res.json();
            if (data.error) message = data.error;
        } catch (_) {
            const text = await res.text();
            if (text) message = text;
        }

        throw new Error(message);
    }

    const ct = res.headers.get("content-type");
    return ct?.includes("application/json")
        ? res.json()
        : res.text();
}

// =========================
// Select2初期化
// =========================
function initMemberSelect($el, users, selectedIds, modalId) {

    // 既存破棄（安全対策）
    if ($el.hasClass("select2-hidden-accessible")) {
        $el.select2('destroy');
    }

    $el.empty();

    $el.select2({
        dropdownParent: $(modalId),
        width: "100%",
        placeholder: "メンバーを選択",

        matcher: matchUser,

        data: users.map(u => ({
            id: u.id,
            text: `${u.text}（${u.department}）`,

            // matcher用
            username: u.username,
            department: u.department,
            name: u.name
        }))
    });

    $el.val(selectedIds).trigger("change");
}

// =========================
// Select2検索用matcher
// =========================
function matchUser(params, data) {

    if (!data || !data.text) return null;
    if ($.trim(params.term) === "") return data;

    const term = params.term.toLowerCase();

    const text = (data.text || "").toLowerCase();
    const name = (data.name || "").toLowerCase();
    const department = (data.department || "").toLowerCase();
    const username = (data.username || "").toLowerCase();

    if (
        text.includes(term) ||
        name.includes(term) ||
        department.includes(term) ||
        username.includes(term)
    ) {
        return data;
    }

    return null;
}