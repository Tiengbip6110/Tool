#!/bin/bash

# Kịch bản giúp chạy vĩnh viễn tool Python.
# Ngay cả khi tiến trình Python bị hệ điều hành Kill, nó sẽ tự động chạy lại ngay lập tức.

echo "Đang khởi động TXMD5 AI Predictor..."

while true
do
    echo "Khởi chạy ứng dụng..."
    python3 main.py

    echo "Tiến trình Python đã dừng hoặc bị lỗi. Đang khởi động lại sau 5 giây..."
    sleep 5
done
