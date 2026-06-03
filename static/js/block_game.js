/* ========================================
   Canvas
======================================== */

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

canvas.width = 530;
canvas.height = 640;

/* ========================================
   画像
======================================== */

const gameOverImage = new Image();
gameOverImage.src = "/static/picture/gameover.jpg";

const clearImage = new Image();
clearImage.src = "/static/picture/clear.jpg";

/* ========================================
   状態
======================================== */

const STATE_TITLE = "title";
const STATE_STAGE_SELECT = "stage_select";
const STATE_GAME = "game";
const STATE_PAUSE = "pause";
const STATE_CLEAR = "clear";
const STATE_GAMEOVER = "gameover";

let gameState = STATE_TITLE;
/* 現在ステージ */
let currentStage = 0;

/* ========================================
   入力
======================================== */

const keys = {};

let mouseX = 0;
let mouseY = 0;

document.addEventListener("keydown", (e) => {

    keys[e.key] = true;

    /* ESC → ポーズ */

    if (
        e.key === "Escape" &&
        gameState === STATE_GAME
    ) {
        gameState = STATE_PAUSE;
    }

    else if (
        e.key === "Escape" &&
        gameState === STATE_PAUSE
    ) {
        gameState = STATE_GAME;
    }

});

document.addEventListener("keyup", (e) => {
    keys[e.key] = false;
});

canvas.addEventListener("mousemove", (e) => {

    const rect = canvas.getBoundingClientRect();

    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
});

/* ========================================
   Button
======================================== */

class Button {

    constructor(text, x, y, w, h) {

        this.text = text;

        this.x = x;
        this.y = y;

        this.width = w;
        this.height = h;

        this.radius = 15;
    }

    draw() {

        const hovered = this.isHovered();

        const gradient = ctx.createLinearGradient(
            0,
            this.y,
            0,
            this.y + this.height
        );

        gradient.addColorStop(
            0,
            hovered ? "#66aaff" : "#4488ff"
        );

        gradient.addColorStop(1, "#2255aa");

        ctx.fillStyle = gradient;

        this.roundRect(
            this.x,
            this.y,
            this.width,
            this.height,
            this.radius
        );

        ctx.fill();

        ctx.strokeStyle = "white";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = "white";

        ctx.font = "bold 24px sans-serif";

        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        ctx.fillText(
            this.text,
            this.x + this.width / 2,
            this.y + this.height / 2
        );
    }

    isHovered() {

        return (
            mouseX >= this.x &&
            mouseX <= this.x + this.width &&
            mouseY >= this.y &&
            mouseY <= this.y + this.height
        );
    }

    clicked() {
        return this.isHovered();
    }

    roundRect(x, y, width, height, radius) {

        ctx.beginPath();

        ctx.moveTo(x + radius, y);

        ctx.lineTo(x + width - radius, y);

        ctx.quadraticCurveTo(
            x + width,
            y,
            x + width,
            y + radius
        );

        ctx.lineTo(
            x + width,
            y + height - radius
        );

        ctx.quadraticCurveTo(
            x + width,
            y + height,
            x + width - radius,
            y + height
        );

        ctx.lineTo(x + radius, y + height);

        ctx.quadraticCurveTo(
            x,
            y + height,
            x,
            y + height - radius
        );

        ctx.lineTo(x, y + radius);

        ctx.quadraticCurveTo(
            x,
            y,
            x + radius,
            y
        );

        ctx.closePath();
    }
}

/* ========================================
   Paddle
======================================== */

class Paddle {

    constructor() {

        this.width = 100;
        this.height = 15;

        this.x = canvas.width / 2 - this.width / 2;
        this.y = canvas.height - 50;

        this.speed = 7;
    }

    update() {

        if (keys["ArrowLeft"]) {
            this.x -= this.speed;
        }

        if (keys["ArrowRight"]) {
            this.x += this.speed;
        }

        if (this.x < 0) {
            this.x = 0;
        }

        if (this.x + this.width > canvas.width) {
            this.x = canvas.width - this.width;
        }
    }

    draw() {

        ctx.fillStyle = "#00ccff";

        ctx.fillRect(
            this.x,
            this.y,
            this.width,
            this.height
        );
    }
}

/* ========================================
   Ball
======================================== */

class Ball {

    constructor() {

        this.size = 15;

        this.reset();
    }

    reset() {

        this.x = canvas.width / 2;
        this.y = canvas.height / 2;

        const speed = 4;

        this.dx =
            Math.random() < 0.5
                ? speed
                : -speed;

        this.dy = -speed;
    }

    update(paddle, blocks) {

        this.x += this.dx;
        this.y += this.dy;

        /* 壁 */

        if (this.x <= 0) {
            this.x = 0;
            this.dx *= -1;
        }

        if (this.x + this.size >= canvas.width) {
            this.x = canvas.width - this.size;
            this.dx *= -1;
        }

        if (this.y <= 0) {
            this.y = 0;
            this.dy *= -1;
        }

        /* 落下 */

        if (this.y > canvas.height) {

            gameState = STATE_GAMEOVER;

            return;
        }

        /* Paddle */

        if (
            this.x < paddle.x + paddle.width &&
            this.x + this.size > paddle.x &&
            this.y < paddle.y + paddle.height &&
            this.y + this.size > paddle.y
        ) {

            this.dy *= -1;

            this.y = paddle.y - this.size;
        }

        /* Block */

        for (let block of blocks) {

            if (block.destroyed) {
                continue;
            }

            if (
                this.x < block.x + block.width &&
                this.x + this.size > block.x &&
                this.y < block.y + block.height &&
                this.y + this.size > block.y
            ) {

            /* 上下どちらから当たったか */
            if (this.dy > 0) {

                /* 上から落ちてきた */
                this.y = block.y - this.size;

            } else {

                /* 下から当たった */
                this.y = block.y + block.height;
            }

            this.dy *= -1;

            if (!block.unbreakable) {

                block.hp--;

                if (block.hp <= 0) {
                    block.destroyed = true;
                }
            }

                break;
            }
        }
    }

    draw() {

        ctx.fillStyle = "white";

        ctx.beginPath();

        ctx.arc(
            this.x + this.size / 2,
            this.y + this.size / 2,
            this.size / 2,
            0,
            Math.PI * 2
        );

        ctx.fill();
    }
}

/* ========================================
   Block
======================================== */

class Block {

    constructor(x, y, hp = 3, unbreakable = false) {

        this.x = x;
        this.y = y;

        this.width = 60;
        this.height = 20;

        this.hp = hp;

        this.unbreakable = unbreakable;

        this.destroyed = false;
    }

    getColor() {

        if (this.unbreakable) {
            return "gray";
        }

        if (this.hp === 3) {
            return "red";
        }

        if (this.hp === 2) {
            return "yellow";
        }

        return "deepskyblue";
    }

    draw() {

        if (this.destroyed) {
            return;
        }

        ctx.fillStyle = this.getColor();

        ctx.fillRect(
            this.x,
            this.y,
            this.width,
            this.height
        );

        ctx.strokeStyle = "black";

        ctx.strokeRect(
            this.x,
            this.y,
            this.width,
            this.height
        );
    }
}

/* ========================================
   Stage Data
======================================== */

const STAGES = [

    /* Stage 1 */
    [
        "0000000",
        "0000000",
        "0009190",
        "0000000",
        "0000000",
    ],

    /* Stage 2 */
    [
        "1000001",
        "0199910",
        "0033300",
        "0111110",
        "0000000",
    ],


    /* Stage 3 */
    [
        "9999999",
        "1111111",
        "2200022",
        "3333333",
        "1111111",
    ],
];

/* ========================================
   Game
======================================== */

class Game {

    constructor(stageIndex) {

        this.stageIndex = stageIndex;

        this.paddle = new Paddle();

        this.ball = new Ball();

        this.blocks = [];

        this.clear = false;

        this.createBlocks();
    }

    createBlocks() {

        const map = STAGES[this.stageIndex];

        for (let row = 0; row < map.length; row++) {

            for (let col = 0; col < map[row].length; col++) {

                const value = map[row][col];

                if (value === "0") {
                    continue;
                }

                const x = 40 + col * 65;
                const y = 60 + row * 30;

                if (value === "9") {

                    this.blocks.push(
                        new Block(x, y, 999, true)
                    );
                }

                else {

                    this.blocks.push(
                        new Block(
                            x,
                            y,
                            Number(value)
                        )
                    );
                }
            }
        }
    }

    update() {

        this.paddle.update();

        this.ball.update(
            this.paddle,
            this.blocks
        );

        this.checkClear();
    }

    checkClear() {

        this.clear = this.blocks.every(
            block =>
                block.destroyed ||
                block.unbreakable
        );

        if (this.clear) {
            gameState = STATE_CLEAR;
        }
    }

    draw() {

        ctx.clearRect(
            0,
            0,
            canvas.width,
            canvas.height
        );

        this.paddle.draw();

        this.ball.draw();

        for (let block of this.blocks) {
            block.draw();
        }
    }
}

/* ========================================
   Buttons
======================================== */

const startButton = new Button(
    "START",
    165,
    320,
    200,
    70
);

const stageButtons = [
    new Button("STAGE 1", 140, 180, 250, 60),
    new Button("STAGE 2", 140, 280, 250, 60),
    new Button("STAGE 3", 140, 380, 250, 60),
];

const resumeButton = new Button(
    "再開",
    165,
    220,
    200,
    60
);

const stageSelectButton = new Button(
    "ステージ選択",
    165,
    320,
    200,
    60
);

const retryButton = new Button(
    "もう一回",
    10,
    550,
    200,
    60
);

const gameOverStageButton = new Button(
    "ステージ選択",
    320,
    550,
    200,
    60
);

/* ========================================
   Click
======================================== */

canvas.addEventListener("click", () => {

    if (gameState === STATE_TITLE) {

        if (startButton.clicked()) {
            gameState = STATE_STAGE_SELECT;
        }
    }

    else if (gameState === STATE_STAGE_SELECT) {

        for (let i = 0; i < stageButtons.length; i++) {

            if (stageButtons[i].clicked()) {

                currentStage = i;

                game = new Game(i);

                gameState = STATE_GAME;
            }
        }
    }

    else if (gameState === STATE_PAUSE) {

        if (resumeButton.clicked()) {
            gameState = STATE_GAME;
        }

        else if (stageSelectButton.clicked()) {
            gameState = STATE_STAGE_SELECT;
        }
    }

    else if (gameState === STATE_CLEAR) {

        gameState = STATE_STAGE_SELECT;
    }

    else if (gameState === STATE_GAMEOVER) {

        if (retryButton.clicked()) {

            game = new Game(currentStage);

            gameState = STATE_GAME;
        }

        else if (gameOverStageButton.clicked()) {

            gameState = STATE_STAGE_SELECT;
        }
    }

});

/* ========================================
   Draw
======================================== */

function drawTitle() {

    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "white";

    ctx.font = "bold 56px sans-serif";

    ctx.textAlign = "center";

    ctx.fillText(
        "ブロック崩し",
        canvas.width / 2,
        200
    );

    startButton.draw();
}

function drawStageSelect() {

    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "white";

    ctx.font = "bold 48px sans-serif";

    ctx.textAlign = "center";

    ctx.fillText(
        "SELECT STAGE",
        canvas.width / 2,
        100
    );

    for (let button of stageButtons) {
        button.draw();
    }
}

function drawPause() {

    game.draw();

    ctx.fillStyle = "rgba(0,0,0,0.7)";

    ctx.fillRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    ctx.fillStyle = "white";

    ctx.font = "bold 48px sans-serif";

    ctx.fillText(
        "PAUSE",
        canvas.width / 2,
        120
    );

    resumeButton.draw();

    stageSelectButton.draw();
}

function drawClear() {

    ctx.drawImage(
        clearImage,
        0,
        0,
        canvas.width,
        canvas.height
    );

    ctx.fillStyle = "gold";

    ctx.font = "bold 60px sans-serif";

    ctx.textAlign = "center";

    ctx.fillText(
        "CLEAR!",
        canvas.width / 2,
        canvas.height / 2 + 150
    );

    ctx.font = "24px sans-serif";

    ctx.fillStyle = "white";

    ctx.fillText(
        "クリックでステージ選択へ",
        canvas.width / 2,
        canvas.height / 2 + 200
    );
}

function drawGameOver() {

    ctx.drawImage(
        gameOverImage,
        0,
        0,
        canvas.width,
        canvas.height
    );

    ctx.fillStyle = "white";

    ctx.font = "bold 50px sans-serif";

    ctx.textAlign = "center";

    ctx.fillText(
        "GAME OVER",
        canvas.width / 2,
        50
    );

    retryButton.draw();

    gameOverStageButton.draw();
}

/* ========================================
   実行
======================================== */

let game = new Game(0);

function loop() {

    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    if (gameState === STATE_TITLE) {
        drawTitle();
    }

    else if (gameState === STATE_STAGE_SELECT) {
        drawStageSelect();
    }

    else if (gameState === STATE_GAME) {

        game.update();

        game.draw();
    }

    else if (gameState === STATE_PAUSE) {
        drawPause();
    }

    else if (gameState === STATE_CLEAR) {
        drawClear();
    }

    else if (gameState === STATE_GAMEOVER) {
        drawGameOver();
    }

    requestAnimationFrame(loop);
}

loop();