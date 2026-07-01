# Gov Leads Monitor — Setup Guide

## 1. Install dependencies

```bash
cd ~/Desktop/gov-leads-monitor
pip3 install -r requirements.txt
```

## 2. Get your Notion token

1. Go to **https://www.notion.so/my-integrations**
2. Click **+ New integration** → name it `Gov Leads Monitor` → Submit
3. Copy the **Internal Integration Token** (starts with `secret_…`)
4. Paste it into `config.py` → `NOTION_TOKEN`

## 3. Get your database IDs

For each of the 3 databases (Marketing Leads, Past Classes, Sales CRM):

1. Open the database in Notion as a **full page** (not a sidebar panel)
2. Copy the URL — it looks like:
   ```
   https://www.notion.so/yourworkspace/abc123def456...?v=xyz
   ```
3. The long string *before* the `?` is the database ID  
   Format it with dashes: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
4. Paste each ID into the matching field in `config.py`

## 4. Share databases with your integration

For **each** database:
1. Open it in Notion
2. Click **···** (top right) → **Connections** → find `Gov Leads Monitor` → click to add

## 5. Map your Notion field names

Open `config.py` and update `LEADS_FIELDS`, `CLASSES_FIELDS`, `CRM_FIELDS`  
to match the **exact column names** in your Notion databases (case-sensitive).

## 6. Configure Gmail

1. Enable 2-Step Verification on your Google account
2. Go to **myaccount.google.com → Security → App passwords**
3. Select **Mail** + **Other (custom name)** → name it `Gov Leads Monitor`
4. Copy the 16-character app password
5. Paste it into `config.py` → `EMAIL_PASSWORD` and `EMAIL_FROM`

## 7. Test it

```bash
# Dry run — prints email preview, no PDF or email sent
python3 run.py --dry-run

# Generate PDF only (no email)
python3 run.py --pdf-only

# Full run
python3 run.py
```

## 8. Schedule it (every Monday 8 AM)

Add to crontab (`crontab -e`):

```
0 8 * * 1 cd ~/Desktop/gov-leads-monitor && /usr/bin/python3 run.py >> ~/Desktop/gov-leads-monitor/run.log 2>&1
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `notion_client.errors.APIResponseError: Could not find database` | Check the database ID in config.py and that the integration has been shared with the database |
| `SMTPAuthenticationError` | Use an App Password, not your regular Gmail password |
| `KeyError: 'Organisation Name'` | Update LEADS_FIELDS in config.py to match your exact Notion column names |
| Charts not showing | Run `pip3 install matplotlib numpy` |
