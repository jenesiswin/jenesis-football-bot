import asyncio
import requests
import math
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CLOUD CONFIGURATION (SECURE) ---
API_KEY = os.getenv("
8d1afabb604b3cca72d6a17adae4d503
")
BOT_TOKEN = os.getenv("8043241331:AAEAlqZbcY6xaTv1r-m8gOXRXgh2sgRsBEo")

def poisson_probability(actual, mean):
    if mean <= 0: return 0
    return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)

def calculate_under_35_prob(home_exp, away_exp):
    prob_under_35 = 0
    for i in range(4):
        for j in range(4 - i):
            prob_home = poisson_probability(i, home_exp)
            prob_away = poisson_probability(j, away_exp)
            prob_under_35 += (prob_home * prob_away)
    return prob_under_35 * 100

def get_weighted_xg(team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5"
    headers = {'x-apisports-key': API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        results = response.json().get('response', [])
        if not results: return 1.10
        weights = [0.40, 0.30, 0.20, 0.05, 0.05]
        weighted_goals = 0
        for i, match in enumerate(results):
            if i >= len(weights): break
            goals = match['goals']['home'] if match['teams']['home']['id'] == team_id else match['goals']['away']
            weighted_goals += (goals or 0) * weights[i]
        return weighted_goals
    except:
        return 1.10

def get_predictions():
    today = datetime.utcnow().strftime('%Y-%m-%d')
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    headers = {'x-apisports-key': API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        if not data.get('response') or len(data['response']) < 5:
            tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"https://v3.football.api-sports.io/fixtures?date={tomorrow}"
            response = requests.get(url, headers=headers, timeout=30)
            data = response.json()

        if not data.get('response'):
            return "📭 No upcoming data found."

        predictions = []
        for item in data['response'][:150]:
            if item['fixture']['status']['short'] not in ['NS', 'TBD']:
                continue
            home_id = item['teams']['home']['id']
            away_id = item['teams']['away']['id']
            home_xg = get_weighted_xg(home_id)
            away_xg = get_weighted_xg(away_id)
            prob = calculate_under_35_prob(home_xg, away_xg)
            est_odds = round(1 / (prob / 100) + 0.12, 2)

            if prob >= 70 and 1.25 <= est_odds <= 1.30:
                predictions.append({
                    "match": f"{item['teams']['home']['name']} vs {item['teams']['away']['name']}",
                    "league": f"{item['league']['country']} - {item['league']['name']}",
                    "time": item['fixture']['date'][11:16],
                    "prob": round(prob, 2),
                    "odds": est_odds
                })

        if not predictions:
            return "📉 No games meet the 1.25-1.30 Odds criteria currently."

        header = "⚖️ **Jenesis Cloud Master (U3.5)**\n"
        header += "Range: 1.25 - 1.30 Odds | 24/7 Hosting\n"
        header += "------------------------------------\n\n"
        body = ""
        for p in predictions:
            body += f"🕒 {p['time']} GMT | {p['league']}\n⚽ {p['match']}\n📈 Prob: {p['prob']}% | 💰 Odds: {p['odds']}\n\n"
        return header + body
    except Exception as e:
        return f"❌ System Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Cloud Master Engine Live.\nRange: 1.25 - 1.30 Odds.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧬 Deep scanning weighted form for 1.25-1.30 range...")
    message = get_predictions()
    await update.message.reply_text(message, parse_mode='Markdown')

if __name__ == '__main__':
    # No tokens here - Render will handle the connection
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.run_polling()
