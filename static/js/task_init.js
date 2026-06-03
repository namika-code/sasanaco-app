document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // タスクUI初期化
    // =========================
    bindCharCounter("taskTitle", "taskTitleCount", 40);
    bindCharCounter("taskContent", "taskContentCount", 240);

    validateTaskForm();

    // 入力変更で再バリデーション
    document.getElementById("taskTitle")
        ?.addEventListener("input", validateTaskForm);

    document.getElementById("taskContent")
        ?.addEventListener("input", validateTaskForm);

    document.querySelector('[name="start_date"]')
        ?.addEventListener("change", validateTaskForm);

    document.querySelector('[name="due_date"]')
        ?.addEventListener("change", validateTaskForm);

    // =========================
    // グループ連動
    // =========================
    const select = document.querySelector('[name="group_id"]');

    function handler() {

        const value = select.value;
        const isPrivate = !value || value == -1;

        loadMembers(value, isPrivate);
        updateGroupButton(value, isPrivate);
    }

    select?.addEventListener("change", handler);
    handler();
});