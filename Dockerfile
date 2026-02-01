FROM python:3.9-slim

# 작업 폴더 설정
WORKDIR /app

# 파일 복사
COPY . /app

# 필요한 라이브러리 설치 (여기에 flask가 꼭 있어야 해!)
RUN pip install --no-cache-dir discord.py pytz flask

# 실행
CMD ["python", "bot.py"]
