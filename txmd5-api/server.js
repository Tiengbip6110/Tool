const express = require('express');
const cors = require('cors');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

// --- CẤU HÌNH GAME ---
const SESSION_DURATION = 500; // Thời gian mỗi phiên là 500 giây

// --- TRẠNG THÁI HIỆN TẠI (STATE) ---
let currentSessionId = 6721880; // Giá trị khởi tạo cho ID phiên
let currentTick = SESSION_DURATION; // Đếm ngược từ 500 -> 0

// Lưu trữ dữ liệu của phiên trước (để trả về kết quả)
let lastResult = {
  phien: currentSessionId.toString(),
  ket_qua: "Tài",
  xuc_xac_1: 5,
  xuc_xac_2: 3,
  xuc_xac_3: 3,
  tong: 11,
  md5_raw: `${currentSessionId}:aM8wXuhfZpzWTm{5-3-3}B7IK`
};

// --- HÀM TIỆN ÍCH ---

// Hàm sinh chuỗi ngẫu nhiên (chữ và số)
function generateRandomString(length) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Hàm format tiền tệ (thêm dấu chấm phân cách hàng nghìn)
function formatCurrency(number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Hàm lấy thời gian hiện tại theo định dạng YYYY-MM-DD HH:mm:ss
function getCurrentTimeFormatted() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// --- VÒNG LẶP GAME (GAME LOOP) ---

// Khởi tạo thông tin đặt cược cho phiên mới
let currentBettingInfo = {
  taiPlayers: Math.floor(Math.random() * 50) + 10,
  xiuPlayers: Math.floor(Math.random() * 50) + 10,
  taiAmount: Math.floor(Math.random() * 10000000) + 1000000,
  xiuAmount: Math.floor(Math.random() * 10000000) + 1000000,
};

// Cập nhật trạng thái game mỗi giây
setInterval(() => {
  currentTick--;

  // Mô phỏng người chơi tiếp tục đặt cược trong quá trình phiên diễn ra
  currentBettingInfo.taiPlayers += Math.floor(Math.random() * 3);
  currentBettingInfo.xiuPlayers += Math.floor(Math.random() * 3);
  currentBettingInfo.taiAmount += Math.floor(Math.random() * 500000);
  currentBettingInfo.xiuAmount += Math.floor(Math.random() * 500000);

  // Khi hết thời gian phiên (đếm ngược về 0)
  if (currentTick <= 0) {
    // 1. Chốt kết quả của phiên hiện tại (vừa hết giờ)
    const xx1 = Math.floor(Math.random() * 6) + 1;
    const xx2 = Math.floor(Math.random() * 6) + 1;
    const xx3 = Math.floor(Math.random() * 6) + 1;
    const tong = xx1 + xx2 + xx3;
    const ket_qua = (tong >= 11 && tong <= 17) ? "Tài" : "Xỉu";

    // Tăng ID phiên
    currentSessionId++;

    // Tạo chuỗi MD5 raw (giả lập)
    const prefix = generateRandomString(14);
    const suffix = generateRandomString(4);
    const md5_raw = `${currentSessionId}:${prefix}{${xx1}-${xx2}-${xx3}}${suffix}`;

    // Lưu lại kết quả để API trả về
    lastResult = {
      phien: currentSessionId.toString(),
      ket_qua: ket_qua,
      xuc_xac_1: xx1,
      xuc_xac_2: xx2,
      xuc_xac_3: xx3,
      tong: tong,
      md5_raw: md5_raw
    };

    // 2. Reset lại phiên mới ngay lập tức
    currentTick = SESSION_DURATION;

    // Reset thông tin đặt cược cho phiên tiếp theo
    currentBettingInfo = {
      taiPlayers: Math.floor(Math.random() * 50) + 10,
      xiuPlayers: Math.floor(Math.random() * 50) + 10,
      taiAmount: Math.floor(Math.random() * 10000000) + 1000000,
      xiuAmount: Math.floor(Math.random() * 10000000) + 1000000,
    };
  }
}, 1000); // Chạy mỗi 1 giây (1000ms)


// --- API ENDPOINT ---
app.get('/api/txmd5', (req, res) => {
  // Tính toán dữ liệu trả về dựa trên state hiện tại

  const totalPlayers = currentBettingInfo.taiPlayers + currentBettingInfo.xiuPlayers;
  const totalAmount = currentBettingInfo.taiAmount + currentBettingInfo.xiuAmount;

  const now = getCurrentTimeFormatted();

  const responseData = {
    "phien": lastResult.phien,
    "ket_qua": lastResult.ket_qua,
    "xuc_xac_1": lastResult.xuc_xac_1,
    "xuc_xac_2": lastResult.xuc_xac_2,
    "xuc_xac_3": lastResult.xuc_xac_3,
    "tong": lastResult.tong,
    "md5_raw": lastResult.md5_raw,
    "betting_info": {
      "phien_cuoc": currentSessionId + 1,
      "tick": currentTick,
      "sub_tick": Math.floor(Math.random() * 30), // Giả lập tick phụ
      "trang_thai": "BETTING",
      "tong_nguoi_cuoc": totalPlayers,
      "tong_tien_cuoc": formatCurrency(totalAmount),
      "nguoi_cuoc": {
        "tai": currentBettingInfo.taiPlayers,
        "xiu": currentBettingInfo.xiuPlayers
      },
      "tien_cuoc": {
        "tai": formatCurrency(currentBettingInfo.taiAmount),
        "xiu": formatCurrency(currentBettingInfo.xiuAmount)
      }
    },
    "update_at": now,
    "tick_update_at": now
  };

  // Trả về JSON với các header CORS giống ví dụ
  res.set('Content-Type', 'application/json');
  res.json(responseData);
});

// --- START SERVER ---
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Test API at: http://localhost:${PORT}/api/txmd5`);
});
