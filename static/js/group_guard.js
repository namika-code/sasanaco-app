// =========================
// モーダル破棄ガード
// =========================

function attachModalGuard(modalId, dirtyKey) {

    const modalEl = document.getElementById(modalId);

    if (!modalEl) return;

    modalEl.addEventListener("hide.bs.modal", function (e) {

        if (!window.AppState[dirtyKey]) return;

        const ok = confirm("入力内容が破棄されますがよろしいですか？");

        if (!ok) {
            e.preventDefault();
            return;
        }

        window.AppState[dirtyKey] = false;
    });
}

// =========================
// 初期化
// =========================
document.addEventListener("DOMContentLoaded", function () {

    attachModalGuard(
        "createGroupModal",
        "createDirty"
    );

    attachModalGuard(
        "editGroupModal",
        "editDirty"
    );
});