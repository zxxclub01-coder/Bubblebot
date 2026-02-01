import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os
import pytz
from flask import Flask
from threading import Thread

# ==========================================
# [1. 가짜 웹 서버 설정] Koyeb이 8000번 포트를 두드리면 대답하는 역할
app = Flask('')

@app.route('/')
def home():
    return "I am alive! (Bot Running)"

def run():
    # Koyeb은 보통 8000번 포트를 사용함
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ==========================================

# [2. 봇 설정]
try:
    TOKEN = os.environ["TOKEN"]
except KeyError:
    print("에러: 환경 변수 'TOKEN'이 설정되지 않았습니다.")
    TOKEN = "설정필요"

# 채널 ID 수정 필요
CHANNEL_ID = 1466739477941850174
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
DATA_FILE = "attendance_data.json"

def get_korea_time():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def load_data():
    default_data = {"last_date": None, "life": 15, "last_penalty_date": None}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, value in default_data.items():
                if key not in data:
                    data[key] = value
            return data
    return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 로그인했습니다!')
    if not daily_check.is_running(): daily_check.start()
    if not check_reminder.is_running(): check_reminder.start()

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.channel.id != CHANNEL_ID: return
    
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    now_kor = get_korea_time()
    today_str = now_kor.strftime("%Y-%m-%d")
    data = load_data()

    if data['life'] <= 0:
        desc = "**Life가 0입니다.**\n아이템이 소멸되어 더 이상 사용할 수 없습니다."
        embed = discord.Embed(title="☠️ 사용 불가", description=desc, color=0x000000)
        embed.set_footer(text="다시 충전하려면 '!라이프 15' 입력")
        await message.channel.send(embed=embed)
        return

    if data.get("last_date") == today_str:
        embed = discord.Embed(description=f"✅ **오늘({today_str}) 이미 출석했습니다.**", color=0x00ff00)
        embed.set_footer(text=f"현재 Life: {data['life']}개 ❤️")
        await message.channel.send(embed=embed)
    else:
        data["last_date"] = today_str
        save_data(data)
        time_str = now_kor.strftime("%H:%M:%S")
        embed = discord.Embed(title="🔫 버블파이터 출석 완료!", description=f"**{today_str} {time_str}**\nLife가 안전하게 유지됩니다. 🛡️", color=0x0000ff)
        embed.add_field(name="현재 Life", value=f"**{data['life']}개** ❤️", inline=False)
        await message.channel.send(embed=embed)

@tasks.loop(minutes=1)
async def daily_check():
    now = get_korea_time()
    data = load_data()
    today_str = now.strftime("%Y-%m-%d")
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    if data.get("last_penalty_date") != today_str:
        if data.get("last_date") != yesterday_str and data.get("last_date") != today_str:
            if data['life'] > 0:
                data['life'] -= 1
                data['last_penalty_date'] = today_str
                save_data(data)
                ch = bot.get_channel(CHANNEL_ID)
                if ch:
                    if data['life'] == 0:
                        embed = discord.Embed(title="☠️ LIFE 소멸 ☠️", description="어제 미접속! Life 0.", color=0x000000)
                        await ch.send(content="@everyone", embed=embed)
                    else:
                        embed = discord.Embed(title="💔 Life 차감", description=f"어제 미접속! **Life 1 감소**\n남은 Life: {data['life']}개", color=0xff0000)
                        await ch.send(embed=embed)
        else:
            data['last_penalty_date'] = today_str
            save_data(data)

@bot.command()
async def 라이프(ctx, count: int):
    if ctx.channel.id != CHANNEL_ID: return
    data = load_data()
    data["life"] = count
    save_data(data)
    await ctx.send(f"❤️ **Life {count}개로 설정.**")

@bot.command()
async def 취소(ctx):
    if ctx.channel.id != CHANNEL_ID: return
    data = load_data()
    data["last_date"] = None
    save_data(data)
    await ctx.send("🔄 **기록 취소 완료.**")

@tasks.loop(minutes=30)
async def check_reminder():
    now = get_korea_time()
    if 22 <= now.hour <= 23: 
        data = load_data()
        if data.get("last_date") != now.strftime("%Y-%m-%d") and data['life'] > 0:
            ch = bot.get_channel(CHANNEL_ID)
            if ch: 
                msg = f"오늘 접속 안 했어!\n내일 되면 **Life({data['life']}개)** 깎인다! 😱"
                embed = discord.Embed(title="🚨 경고", description=msg, color=0xff0000)
                await ch.send(content="@everyone", embed=embed)

# 봇 실행 전 가짜 서버 켜기
keep_alive()
bot.run(TOKEN)
