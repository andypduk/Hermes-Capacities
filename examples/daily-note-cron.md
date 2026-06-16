# Daily Capacities Note — Cron Setup

This cron job fetches weather, Google Calendar, Google Tasks, and Whoop health data, then saves it all as a formatted markdown briefing to your Capacities daily note every morning at 8am.

## Prerequisites

- [Capacities MCP](https://github.com/andydennis/hermes-capacities) installed and configured
- Composio connected for Google Calendar and Google Tasks
- Whoop MCP connected for health data
- Open-Meteo (free, no API key needed) for weather

## Hermes Cron Configuration

```bash
hermes cron create \
  --schedule "0 8 * * *" \
  --name "Daily Capacities Note" \
  --deliver local \
  --model deepseek-v4-flash \
  --provider deepseek \
  --skills capacities,google-tasks,weather \
  --toolsets terminal,messaging \
  --prompt "See full prompt below"
```

## Full Cron Prompt

The cron agent:
1. Fetches weather via Open-Meteo API (`curl -s 'https://api.open-meteo.com/v1/forecast?latitude=50.55&longitude=-3.50&current=...'`)
2. Assesses hiking conditions with a traffic light (GREEN/AMBER/RED)
3. Fetches Whoop health data (recovery, HRV, RHR, sleep, strain)
4. Applies activity traffic light based on HRV (117-129 green) and RHR (60-79 green)
5. Fetches Google Calendar events for today
6. Fetches Google Tasks due today
7. Saves all data as formatted markdown via `save_to_daily_note`

## Output Template

```markdown
## ☀️ [Day, Date] — Morning Briefing

📍 **Location:** South Devon
🌤️ **Weather:** [conditions, temp, wind, humidity]
🥾 **Hiking:** [GREEN/AMBER/RED verdict] + precautions

### 💪 Health
📊 **Recovery:** [score]% | 💓 **HRV:** [value] ms | ❤️ **RHR:** [value] bpm
🏃 **Activity:** [GREEN/AMBER/RED verdict] + advice

### 📆 Calendar
- Today's events

### ✅ Tasks Due Today
- Tasks with due dates matching today
```

## Location

Weather is fetched for South Devon (lat=50.55, lon=-3.50). Change these coordinates in the `curl` URL for your location.
