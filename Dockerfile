# 使用官方 Python 3.9 映像檔
FROM python:3.9-slim

# 設定 Container 入面嘅工作目錄
WORKDIR /app

# 1. 先複製 requirements.txt 並安裝 (咁樣做 Build 會快好多)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. 複製剩低嘅所有 Code
COPY . .

# 3. 話畀 AWS 聽我哋用 8080 port
EXPOSE 8080

# 4. 啟動 Streamlit
# 注意：一定要加 --server.address 0.0.0.0，否則外網入唔到
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
