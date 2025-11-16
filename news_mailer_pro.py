import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import openai

# ======== 環境變數 ========
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

openai.api_key = OPENAI_API_KEY

# ======== 勞工議題關鍵字 ========
labour_keywords = [
    "不法侵害","霸凌","性騷擾","主管","歧視",
    "科技業","外籍員工","調解","懷孕"
]


# ======== 抓取新聞 ========
def fetch_news(query, language="zh", page_size=10):
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={query}&language={language}&sortBy=publishedAt&pageSize={page_size}&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    return response.json().get("articles", [])


def fetch_labour_news():
    all_articles = []
    for keyword in labour_keywords:
        all_articles += fetch_news(keyword)

    # 去重複
    seen = set()
    unique = []
    for a in all_articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:8]


# ======== ChatGPT 自動摘要 ========
def ai_summary(text):
    prompt = f"請用兩行文字總結這篇新聞內容：\n{text}\n"
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message["content"].strip()


# ======== 卡片風格 HTML ========
def make_card(title, summary, url):
    return f"""
    <div style="padding:12px; margin-bottom:15px; border:1px solid #ddd; border-radius:10px;">
        <h3 style="margin:0 0 8px 0;">{title}</h3>
        <p style="color:#444;">{summary}</p>
        <a href="{url}" style="color:#1565c0;">閱讀全文</a>
    </div>
    """


# ======== 組合 Email ========
def build_html():
    html = f"<h2>📩 每日新聞摘要（{datetime.now().strftime('%Y-%m-%d')}）</h2>"

    # 天氣
    html += "<h2>🌤 天氣新聞</h2>"
    for a in fetch_news("台灣 天氣")[:5]:
        summary = ai_summary(a.get("description") or a.get("title"))
        html += make_card(a["title"], summary, a["url"])

    # 勞工議題
    html += "<h2>👷‍♂️ 勞工議題</h2>"
    for a in fetch_labour_news():
        summary = ai_summary(a.get("description") or a.get("title"))
        html += make_card(a["title"], summary, a["url"])

    # AI 工具
    html += "<h2>🤖 AI 工具 / 新技術</h2>"
    for a in fetch_news("AI 工具 OR ChatGPT OR 人工智慧")[:5]:
        summary = ai_summary(a.get("description") or a.get("title"))
        html += make_card(a["title"], summary, a["url"])

    # 股市
    html += "<h2>📈 台股 / 美股動態</h2>"
    for a in fetch_news("台股 OR 美股 OR 股市")[:6]:
        summary = ai_summary(a.get("description") or a.get("title"))
        html += make_card(a["title"], summary, a["url"])

    return html


# ======== 寄送 Email ========
def send_email():
    html_content = build_html()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "每日 7 點新聞摘要（AI 自動整理）"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(html_content, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
    server.send_message(msg)
    server.quit()

    print("✔ 已寄出每日新聞摘要！")


if __name__ == "__main__":
    send_email()
