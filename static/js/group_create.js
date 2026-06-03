// =========================
// 新規グループ作成
// =========================
$(function () {

    const $members = $("#createMembers");
    const $groupName = $("#createGroupName");

    bindGroupNameCounter();

    const input = document.getElementById("createGroupName");
    const errorBox = document.getElementById("groupNameError");
    const btn = document.getElementById("createGroupBtn");

    // =========================
    // バリデーションイベント登録
    // =========================
    if (input) {
        input.addEventListener("input", validateGroupForm);
        validateGroupForm();
    }

    // =========================
    // dirty管理
    // =========================
    $(document).on("input change", "#createGroupName, #createMembers", function () {
        if (window.AppState.initializingCreate) return;
        window.AppState.createDirty = true;
    });

    // =========================
    // グループ名バリデーション
    // =========================
    function validateGroupForm() {

        const input = document.getElementById("createGroupName");
        const errorBox = document.getElementById("groupNameError");
        const btn = document.getElementById("createGroupBtn");

        if (!input || !btn) return;

        const errors = [];
        const value = input.value.trim();

        if (!value) errors.push("グループ名を入力してください");
        if (value.length > 20) errors.push("グループ名は20文字以内にしてください");

        if (errorBox) {
            errorBox.textContent = errors.join(" / ");
        }

        input.classList.toggle("is-invalid-input", errors.length > 0);

        btn.disabled = errors.length > 0;
        btn.classList.toggle("btn-danger", errors.length > 0);
        btn.classList.toggle("btn-primary", errors.length === 0);
    }

    // =========================
    // モーダル表示
    // =========================
    $("#createGroupModal").on("shown.bs.modal", function () {

        validateGroupForm();
        window.AppState.initializingCreate = true;

        setupCreateGroupModal()
            .finally(() => {
                window.AppState.initializingCreate = false;
            });
    });

    // =========================
    // 作成処理
    // =========================
    $("#createGroupBtn").on("click", function (e) {
        e.preventDefault();

        const groupname = $groupName.val().trim();
        const members = $members.val() || [];

        window.AppState.initializingCreate = true;

        // 【修正】環境依存しないURLとCSRFトークンへ変更
        apiFetch(window.FlaskConfig.urls.api_create_group, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.FlaskConfig.csrfToken
            },
            body: JSON.stringify({ groupname, members })
        })
        .then(data => {

            const select = document.querySelector('[name="group_id"]');

            select.add(new Option(data.groupname, data.group_id));
            select.value = data.group_id;
            select.dispatchEvent(new Event("change"));

            $groupName.val("");
            $members.val(null).trigger("change");

            window.AppState.createDirty = false;

            hideModal("createGroupModal");
        })
        .catch(err => {

            console.error(err);

            const errorBox = document.getElementById("groupNameError");
            const input = document.getElementById("createGroupName");

            if (errorBox) errorBox.textContent = err.message;
            if (input) input.classList.add("is-invalid-input");
        })
        .finally(() => {
            window.AppState.initializingCreate = false;
        });
    });

    // =========================
    // モーダルリセット
    // =========================
    $("#createGroupModal").on("hidden.bs.modal", function () {
        resetCreateGroupModal();
    });

});


// ==================================================
// ■ API層
// ==================================================
async function fetchUsers() {
    // 【修正】環境依存しないURLへ変更
    const res = await fetch(window.FlaskConfig.urls.api_users);
    if (!res.ok) throw new Error("ユーザー取得に失敗しました");
    return await res.json();
}


// ==================================================
// ■ モーダル初期化（呼ぶだけ）
// ==================================================
async function setupCreateGroupModal() {

    const $members = $("#createMembers");

    const users = await fetchUsers();


    // デバッグ
    console.log(users[0]);
    console.log("users raw:", users);
    console.log("first user:", users[0]);
    // デバッグ

    initMemberSelect(
        $members,
        users,
        [],
        "#createGroupModal"
    );
}


// ==================================================
// ■ カウンタ
// ==================================================
function bindGroupNameCounter() {

    const input = document.getElementById("createGroupName");
    const counter = document.getElementById("groupNameCount");

    if (!input || !counter) return;

    const max = 20;

    const update = () => {

        const len = input.value.length;

        counter.textContent = `${len} / ${max}`;

        counter.style.color =
            len > max ? "red" :
            len > max * 0.8 ? "orange" :
            "#888";
    };

    input.addEventListener("input", update);
    update();
}


// ==================================================
// ■ リセット
// ==================================================
function resetCreateGroupModal() {

    $("#createGroupName").val("");
    $("#createMembers").val(null).trigger("change");

    const errorBox = document.getElementById("groupNameError");
    const input = document.getElementById("createGroupName");
    const counter = document.getElementById("groupNameCount");

    if (errorBox) errorBox.textContent = "";
    if (input) input.classList.remove("is-invalid-input");

    if (counter) {
        counter.textContent = "0 / 20";
        counter.style.color = "#888";
    }

    window.AppState.createDirty = false;
}