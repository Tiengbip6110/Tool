const express = require('express');
const md5 = require('md5');
const cors = require('cors');
const moment = require('moment-timezone');

const app = express();
app.use(cors());

// --- CẤU HÌNH THỜI GIAN VÀ GAME ---
const PORT = 3000;
const BETTING_TIME = 500; // Thời gian đặt cược (giây)
const WAITING_TIME = 60;  // Độ trễ chờ giữa các phiên (giây)
const TOTAL_CYCLE = BETTING_TIME + WAITING_TIME; // Tổng 1 chu kỳ 560 giây

// Thời điểm gốc (epoch) để tính toán phiên hiện tại
// Giả sử mốc thời gian bằng 0 là một thời điểm cụ thể trong quá khứ
// Ở đây chúng ta dùng một thời điểm cố định để các giá trị luôn nhất quán
const START_EPOCH = new Date("2024-01-01T00:00:00Z").getTime() / 1000;

// --- CÁC HÀM TIỆN ÍCH ---

// Hàm sinh chuỗi ngẫu nhiên (dùng để làm hash/seed)
function generateRandomString(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// Hàm tính toán thông tin phiên hiện tại dựa trên thời gian thực tế
function getCurrentSessionInfo() {
    const nowSecs = Math.floor(Date.now() / 1000);
    const elapsedSecs = nowSecs - START_EPOCH;

    // Tính số phiên đã trôi qua kể từ START_EPOCH
    const currentSessionNumber = Math.floor(elapsedSecs / TOTAL_CYCLE) + 1000000; // Cầm base 1000000 cho giống ID phiên

    // Tính số giây đã trôi qua trong phiên hiện tại (từ 0 đến 559)
    const secondsInCurrentCycle = elapsedSecs % TOTAL_CYCLE;

    let state = "BETTING";
    let tick = 0; // Số giây còn lại của trạng thái (ngược lại với thời gian đã qua)

    if (secondsInCurrentCycle < BETTING_TIME) {
        state = "BETTING";
        tick = BETTING_TIME - secondsInCurrentCycle;
    } else {
        state = "WAITING";
        tick = TOTAL_CYCLE - secondsInCurrentCycle;
    }

    return {
        sessionNumber: currentSessionNumber,
        state: state,
        tick: tick,
        secondsInCurrentCycle: secondsInCurrentCycle
    };
}

// --- LOGIC SINH DỮ LIỆU ĐỘNG ---

// Seed tĩnh dựa trên ID phiên (để kết quả xúc xắc của 1 phiên không thay đổi mỗi lần load)
function getDiceResultForSession(sessionNumber) {
    // Dùng md5 của sessionNumber làm seed để kết quả luôn cố định cho mỗi session
    const hash = md5(sessionNumber.toString() + "secret_salt_txmd5");

    // Lấy 3 chữ số đầu tiên từ hash để tạo kết quả xúc xắc (1-6)
    const char1 = hash.charCodeAt(0) % 6 + 1;
    const char2 = hash.charCodeAt(1) % 6 + 1;
    const char3 = hash.charCodeAt(2) % 6 + 1;

    return [char1, char2, char3];
}

// --- API ENDPOINT ---
app.get('/api/txmd5', (req, res) => {
    const sessionInfo = getCurrentSessionInfo();
    const phienCuoc = sessionInfo.sessionNumber;

    // Nếu đang trong thời gian đặt cược (BETTING), kết quả xúc xắc là của PHIÊN TRƯỚC ĐÓ.
    // Thông tin đặt cược sẽ tăng lên liên tục.
    let displayPhien = phienCuoc - 1; // Mặc định hiển thị kết quả phiên cũ
    let showResult = true;

    // Tính toán lượng người chơi và tiền ảo tăng dần theo thời gian trong 500s đặt cược
    let taiUsers = 10;
    let xiuUsers = 10;
    let taiMoney = 5000000;
    let xiuMoney = 4000000;

    if (sessionInfo.state === "BETTING") {
        // Mô phỏng số người và số tiền tăng tuyến tính (có thể thêm random nhỏ)
        // Cứ mỗi giây trôi qua (secondsInCurrentCycle), số tiền/người tăng thêm
        const progress = sessionInfo.secondsInCurrentCycle;

        // Random nhẹ để trông tự nhiên
        const randTaiUsers = progress * 2 + Math.floor(Math.random() * 10);
        const randXiuUsers = progress * 2 + Math.floor(Math.random() * 10);
        const randTaiMoney = progress * 150000 + Math.floor(Math.random() * 1000000);
        const randXiuMoney = progress * 140000 + Math.floor(Math.random() * 1000000);

        taiUsers += randTaiUsers;
        xiuUsers += randXiuUsers;
        taiMoney += randTaiMoney;
        xiuMoney += randXiuMoney;
    } else {
        // Đang trong 60 giây chờ kết quả (WAITING / PREPARING).
        // Hiển thị kết quả của phiên vừa mới kết thúc đặt cược (phienCuoc).
        displayPhien = phienCuoc;
        // Tiền cược giữ nguyên (chốt sổ)
        const progress = BETTING_TIME;
        taiUsers += progress * 2 + 50;
        xiuUsers += progress * 2 + 45;
        taiMoney += progress * 150000 + 500000;
        xiuMoney += progress * 140000 + 400000;
    }

    const diceResult = getDiceResultForSession(displayPhien);
    const x1 = diceResult[0], x2 = diceResult[1], x3 = diceResult[2];
    const tong = x1 + x2 + x3;
    const ketQua = tong >= 11 ? "Tài" : "Xỉu";

    // Chuỗi mã hóa raw để băm MD5
    // Thông thường gồm: ID_Phiên:ChuỗiNgẫuNhiênĐầu{x1-x2-x3}ChuỗiNgẫuNhiênCuối
    const prefix = generateRandomString(8);
    const suffix = generateRandomString(12);
    const md5Raw = `${displayPhien}:${prefix}{${x1}-${x2}-${x3}}${suffix}`;

    const now = moment().tz("Asia/Ho_Chi_Minh");

    // Định dạng số tiền kiểu VN (vd: 31.459.000)
    const formatMoney = (money) => money.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");

    const responseData = {
        phien: displayPhien.toString(),
        ket_qua: ketQua,
        xuc_xac_1: x1,
        xuc_xac_2: x2,
        xuc_xac_3: x3,
        tong: tong,
        md5_raw: md5Raw,
        betting_info: {
            phien_cuoc: phienCuoc,
            tick: sessionInfo.tick, // Đếm ngược số giây còn lại (500->0 hoặc 60->0)
            sub_tick: 0, // Tick phụ (millisecond/frame) có thể tự sinh nếu cần thiết (không bắt buộc)
            trang_thai: sessionInfo.state,
            tong_nguoi_cuoc: taiUsers + xiuUsers,
            tong_tien_cuoc: formatMoney(taiMoney + xiuMoney),
            nguoi_cuoc: {
                tai: taiUsers,
                xiu: xiuUsers
            },
            tien_cuoc: {
                tai: formatMoney(taiMoney),
                xiu: formatMoney(xiuMoney)
            }
        },
        update_at: now.format("YYYY-MM-DD HH:mm:ss"),
        tick_update_at: now.format("YYYY-MM-DD HH:mm:ss")
    };

    res.json(responseData);
});

app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
    console.log(`API Endpoint: http://localhost:${PORT}/api/txmd5`);
});
