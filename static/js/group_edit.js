// =========================
// 既存グループ メンバー編集
// =========================


// ==================================================
// ■ dirty管理
// ==================================================
$(document).on("change", "#editMembers", function () {

    if (window.AppState.initializingEdit) return;

    window.AppState.editDirty = true;

    validateEditGroupForm();
});


// ==================================================
// ■ 編集モーダルを開く
// ==================================================
function openEditModal(groupId) {

    window.AppState.editingGroupId = groupId;
    window.AppState.editDirty = false;
    window.AppState.initializingEdit = true;

    setupEditGroupModal(groupId)
        .then(() => {
            showModal("editGroupModal");
        })
        .finally(() => {
            setTimeout(() => {
                window.AppState.initializingEdit = false;
            }, 200);
        });
}


// ==================================================
// ■ モーダル初期化
// ==================================================
async function setupEditGroupModal(groupId) {

    const $editMembers = $("#editMembers");

    // 【修正】環境依存しない動的URLの生成 (.replace を使用)
    const getGroupUrl = window.FlaskConfig.urls.api_get_group.replace('9999', groupId);

    const [users, group] = await Promise.all([
        fetchUsers(),
        apiFetch(getGroupUrl)
    ]);

    const memberIds = (group.members ?? []).map(m => m.id);

    document.getElementById("editGroupNameLabel").innerText =
        group.groupname ?? "（名称未設定）";

    initMemberSelect(
        $editMembers,
        users,
        memberIds,
        "#editGroupModal"
    );

    validateEditGroupForm();
}


// ==================================================
// ■ メンバーバリデーション
// ==================================================
function validateEditGroupForm() {

    const members = $("#editMembers").val() || [];

    const btn = document.getElementById("saveGroupMembers");
    const errorBox = document.getElementById("editGroupError");

    const errors = [];

    if (members.length === 0) {
        errors.push("メンバーを1人以上選択してください");
    }

    if (errorBox) {
        errorBox.textContent = errors.join(" / ");
    }

    const hasError = errors.length > 0;

    btn.disabled = hasError;

    btn.classList.toggle("btn-danger", hasError);
    btn.classList.toggle("btn-primary", !hasError);

    return !hasError;
}


// ==================================================
// ■ 保存処理
// ==================================================
document.addEventListener("DOMContentLoaded", function () {

    document.getElementById("saveGroupMembers")?.addEventListener("click", async () => {

        if (!validateEditGroupForm()) return;

        const id = window.AppState.editingGroupId;

        const selected = ($("#editMembers").val() || []).map(Number);

        // 【修正】環境依存しない動的URLの生成とCSRFトークンの紐付け
        const syncMembersUrl = window.FlaskConfig.urls.api_sync_members.replace('9999', id);

        try {

            await apiFetch(syncMembersUrl, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": window.FlaskConfig.csrfToken
                },
                body: JSON.stringify({ members: selected })
            });

            window.AppState.editDirty = false;

            loadMembers(id, false);

            hideModal("editGroupModal");

        } catch (err) {

            console.error(err);

            document.getElementById("editGroupError").textContent = err.message;
        }
    });
});