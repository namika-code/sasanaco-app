// =========================
// 性別カラー
// =========================
function genderClass(gender) {

    switch (gender) {

        case "male":
            return "text-primary";

        case "female":
            return "text-danger";

        default:
            return "text-secondary";
    }
}

// =========================
// グループメンバー表示
// =========================
async function loadMembers(groupId, isPrivate) {

    const container = document.getElementById("groupMembersContainer");
    const sizer = document.getElementById("groupMembersSizer");
    const box = document.getElementById("groupMembers");

    if (!container || !sizer || !box) return;

    // 現在の選択グループ保持
    window.AppState.currentGroupId = groupId;
    const requestId = groupId;

    // ==================================================
    // PRIVATE
    // ==================================================
    if (isPrivate) {

        // fade out
        sizer.classList.add("is-fading");

        // fade完了待ち
        await new Promise(r => setTimeout(r, 180));

        // 非表示化
        sizer.classList.add("is-hidden");

        // 中身クリア
        box.innerHTML = "";

        return;
    }

    // ==================================================
    // 表示
    // ==================================================

    // hidden解除
    sizer.classList.remove("is-hidden");

    // 【修正】環境依存しない動的URLの生成 (.replace を使用)
    const getGroupUrl = window.FlaskConfig.urls.api_get_group.replace('9999', groupId);

    // API取得
    const group = await apiFetch(getGroupUrl);

    // 古いレスポンス破棄
    if (window.AppState.currentGroupId !== requestId) return;

    const members = group.members ?? [];

    // ==================================================
    // フェード切替
    // ==================================================

    // fade out
    sizer.classList.add("is-fading");

    // アニメ待機
    await new Promise(r => setTimeout(r, 180));

    // DOM更新
    box.innerHTML = members
        .map(m => {

            const cls = genderClass(m.gender);

            return `
                <span>
                    <i class="bi bi-person-fill ${cls}"></i>
                    ${m.name}（${m.department}）
                </span>
            `;
        })
        .join("<br>");

    // 次フレームでfade in
    requestAnimationFrame(() => {
        sizer.classList.remove("is-fading");
    });
}

// =========================
// ボタン切替
// =========================
function updateGroupButton(groupId, isPrivate) {

    const btn = document.getElementById("groupActionBtn");
    if (!btn) return;

    if (isPrivate) {
        btn.innerText = "グループ作成";
        btn.onclick = () => showModal("createGroupModal");
    } else {
        btn.innerText = "グループ編集";
        btn.onclick = () => openEditModal(groupId);
    }
}

// =========================
// 初期化＆イベント
// =========================
document.addEventListener("DOMContentLoaded", function () {

    const select = document.querySelector('[name="group_id"]');
    if (!select) return;

    function handler() {

        const value = select.value;
        const isPrivate = !value || value == -1;

        loadMembers(value, isPrivate);
        updateGroupButton(value, isPrivate);
    }

    select.addEventListener("change", handler);
    $(select).on("select2:select", handler);
    $(select).on("select2:clear", handler);

    requestAnimationFrame(handler);
});