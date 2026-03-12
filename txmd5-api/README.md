# Hướng Dẫn Chi Tiết Tạo Dynamic JSON API (Tài Xỉu MD5)

## 1. Dynamic JSON API là gì?

JSON API (Application Programming Interface) là một phương thức giao tiếp giữa các hệ thống phần mềm, sử dụng định dạng JSON (JavaScript Object Notation) để truyền tải dữ liệu.

**Dynamic JSON API** (API JSON động) có nghĩa là dữ liệu trả về không phải là tĩnh (ví dụ không phải là một file text đứng yên), mà nó thay đổi liên tục theo thời gian thực hoặc theo logic nghiệp vụ bên dưới.

Trong trường hợp của API Game Tài Xỉu MD5 này:
- Máy chủ (Backend) duy trì một trạng thái liên tục (vòng lặp 500 giây).
- Mỗi giây trôi qua, các chỉ số như `tick` (thời gian đếm ngược), tổng người chơi, tổng tiền cược sẽ thay đổi.
- Khi người dùng (client) gọi vào đường dẫn API (ví dụ: `/api/txmd5`), máy chủ sẽ tính toán trạng thái hiện tại ngay lúc đó và trả về chuỗi JSON mới nhất.
- Khi hết 500 giây, hệ thống tự động chốt kết quả xúc xắc, tạo mã MD5, đổi phiên (session) mới và lặp lại vòng lặp.

## 2. Cách thức hoạt động của mã nguồn (`server.js`)

Chúng ta sử dụng **Node.js** kết hợp với thư viện **Express** (để tạo Web Server dễ dàng).

### Các phần chính trong Code:
1. **Quản lý State (Trạng thái):**
   - Có các biến toàn cục (global variables) để lưu trữ `currentSessionId` (ID phiên hiện tại), `currentTick` (thời gian đếm ngược từ 500 về 0), và kết quả của phiên trước `lastResult`.
2. **Vòng lặp Game (Game Loop):**
   - Sử dụng hàm `setInterval` của JavaScript, hàm này sẽ chạy chính xác mỗi 1000ms (1 giây).
   - Mỗi giây, `currentTick` bị trừ đi 1. Đồng thời, số lượng người chơi và tiền cược (`taiPlayers`, `xiuPlayers`, `taiAmount`, `xiuAmount`) được cộng thêm các giá trị ngẫu nhiên để mô phỏng việc người chơi đang liên tục đặt cược.
   - Khi `currentTick` về 0:
     - Hệ thống quay ngẫu nhiên 3 xúc xắc (1 đến 6).
     - Tạo một chuỗi MD5 giả lập theo định dạng `<phien>:<random>{x-y-z}<random>`.
     - Tăng số phiên (`currentSessionId++`) và reset lại bộ đếm (`currentTick = 500`), khởi tạo lại các thông số cược về mặc định để bắt đầu phiên mới ngay lập tức.
3. **API Endpoint (`app.get('/api/txmd5')`):**
   - Khi có ai đó truy cập vào URL này, server không thay đổi trạng thái game, mà nó chỉ đọc trạng thái hiện tại (số người chơi, tiền cược, thời gian còn lại) và đóng gói lại thành định dạng JSON giống tỷ lệ 1:1 với ví dụ bạn đã đưa ra.

---

## 3. Hướng dẫn chạy API trên máy tính cá nhân (Localhost)

Để chạy được đoạn mã này, bạn cần cài đặt **Node.js**.

**Bước 1:** Tải và cài đặt Node.js từ trang chủ: [https://nodejs.org](https://nodejs.org) (chọn bản LTS).
**Bước 2:** Mở Terminal (Command Prompt hoặc PowerShell trên Windows).
**Bước 3:** Tạo một thư mục và chuyển vào thư mục đó.
**Bước 4:** Copy file `server.js` và `package.json` vào thư mục này.
**Bước 5:** Cài đặt thư viện bằng lệnh:
```bash
npm install
```
**Bước 6:** Chạy server bằng lệnh:
```bash
node server.js
```
Nếu màn hình hiện:
```
Server is running on port 3000
Test API at: http://localhost:3000/api/txmd5
```
Là bạn đã thành công. Mở trình duyệt và truy cập vào link trên để xem kết quả. Nhấn F5 để thấy dữ liệu thay đổi mỗi giây.

---

## 4. Hướng dẫn đưa API lên mạng miễn phí (Deploy lên Render)

Để mọi người trên Internet có thể truy cập được API của bạn (giống như link Cloudflare của bạn), bạn cần đưa code lên một nền tảng Cloud. **Render.com** là một lựa chọn miễn phí và tốt nhất.

**Bước 1:** Đăng ký tài khoản GitHub (https://github.com) và Render (https://render.com).
**Bước 2:** Đưa mã nguồn của bạn lên GitHub.
   - Tạo một Repository mới trên GitHub.
   - Upload 2 file `server.js` và `package.json` lên repository đó.
**Bước 3:** Đăng nhập vào Render.com, chọn **"New Web Service"**.
**Bước 4:** Chọn **"Build and deploy from a Git repository"** và kết nối với tài khoản GitHub của bạn.
**Bước 5:** Chọn Repository bạn vừa tạo ở Bước 2.
**Bước 6:** Cấu hình thông số (có thể để mặc định):
   - Name: Tên tùy ý (ví dụ: `txmd5-api-demo`)
   - Region: Singapore (cho gần VN) hoặc bất kỳ.
   - Runtime: `Node`
   - Build Command: `npm install`
   - Start Command: `node server.js`
**Bước 7:** Kéo xuống dưới cùng chọn **"Free"** plan, và bấm **"Create Web Service"**.

Chờ khoảng 1-2 phút, Render sẽ cấp cho bạn một đường link có dạng `https://txmd5-api-demo.onrender.com`.
Khi đó, bạn truy cập `https://txmd5-api-demo.onrender.com/api/txmd5` là bạn đã có một API y hệt ví dụ của mình!