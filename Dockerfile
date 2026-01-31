FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install discord.py pytz
CMD ["python", "bot.py"]
