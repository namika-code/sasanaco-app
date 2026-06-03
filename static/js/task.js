// =========================
// タスク 文字数カウンタ
// =========================
function bindCharCounter(inputId, counterId, max) {

    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);

    if (!input || !counter) return;

    const update = () => {

        const len = input.value.length;

        counter.textContent = `${len} / ${max}`;

        // 色変更
        if (len > max) {
            counter.style.color = "red";
        } else if (len > max * 0.8) {
            counter.style.color = "orange";
        } else {
            counter.style.color = "#888";
        }

        // バリデーション再実行
        validateTaskForm();
    };

    input.addEventListener("input", update);

    // 初期表示
    update();
}

// =========================
// タスク バリデーション
// =========================
function validateTaskForm() {

    const title = document.getElementById("taskTitle");
    const content = document.getElementById("taskContent");

    const startDateEl =
        document.getElementById("start_date") ||
        document.querySelector('[name="start_date"]');

    const dueDateEl =
        document.getElementById("due_date") ||
        document.querySelector('[name="due_date"]');

    // task submit専用
    const submitBtn = document.getElementById("submitBtn");

    const errorBox = document.getElementById("formError");

    if (!title || !content || !submitBtn) return;

    const errors = [];

    // =========================
    // タスク名
    // =========================
    if (!title.value.trim()) {

        errors.push("タスク名を入力してください");

        title.classList.add("is-invalid-input");

    } else if (title.value.length > 40) {

        errors.push("タスク名は40文字以内にしてください");

        title.classList.add("is-invalid-input");

    } else {

        title.classList.remove("is-invalid-input");
    }

    // =========================
    // タスク内容
    // =========================
    if (content.value.length > 240) {

        errors.push("タスク内容は240文字以内にしてください");

        content.classList.add("is-invalid-input");

    } else {

        content.classList.remove("is-invalid-input");
    }

    // =========================
    // 日付チェック
    // =========================
    if (!startDateEl.value) {

        errors.push("開始日を入力してください");

        startDateEl.classList.add("is-invalid-input");

    } else {

        startDateEl.classList.remove("is-invalid-input");
    }

    if (!dueDateEl.value) {

        errors.push("締切日を入力してください");

        dueDateEl.classList.add("is-invalid-input");

    } else {

        dueDateEl.classList.remove("is-invalid-input");
    }

    if (
        startDateEl &&
        dueDateEl &&
        startDateEl.value &&
        dueDateEl.value
    ) {

        const start = new Date(startDateEl.value);
        const due = new Date(dueDateEl.value);

        if (start > due) {

            errors.push("締切日は開始日より後にしてください");

            startDateEl.classList.add("is-invalid-input");
            dueDateEl.classList.add("is-invalid-input");

        } else {

            startDateEl.classList.remove("is-invalid-input");
            dueDateEl.classList.remove("is-invalid-input");
        }
    }

    // =========================
    // エラー表示
    // =========================
    if (errorBox) {
        errorBox.textContent = errors.join(" / ");
    }

    // =========================
    // submit制御
    // =========================
    const hasError = errors.length > 0;

    submitBtn.disabled = hasError;

    // ボタン色
    submitBtn.classList.toggle("btn-danger", hasError);
    submitBtn.classList.toggle("btn-secondary", !hasError);
}