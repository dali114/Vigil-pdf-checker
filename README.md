# Vigil PDF Checker

Automatically checks 19 PDF URLs daily and emails you if any are broken or updated.

## Setup (one time, ~5 minutes)

### Step 1 — Create the GitHub repo

1. Go to [github.com/new](https://github.com/new)
2. Name it `vigil-pdf-checker`
3. Make it **Private**
4. Click **Create repository**

### Step 2 — Upload these files

1. On your new repo page, click **uploading an existing file**
2. Drag in `check_pdfs.py`
3. Also create the folder structure for the workflow:
   - Click **Create new file**
   - Type `.github/workflows/check-pdfs.yml` as the filename
   - Paste the contents of `check-pdfs.yml`
4. Click **Commit changes**

### Step 3 — Set up Gmail for alerts

You need a Gmail "App Password" (not your regular password):

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Make sure **2-Step Verification** is ON
3. Search for **App Passwords** at the top
4. Create one named "Vigil" — copy the 16-character password it gives you

### Step 4 — Add secrets to GitHub

1. In your repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these three:

| Name | Value |
|------|-------|
| `GMAIL_USER` | your Gmail address (e.g. you@gmail.com) |
| `GMAIL_APP_PASSWORD` | the 16-character app password from Step 3 |
| `NOTIFY_EMAIL` | email address to send alerts to |

### Step 5 — Test it

1. Go to the **Actions** tab in your repo
2. Click **Vigil PDF Checker** on the left
3. Click **Run workflow** → **Run workflow**
4. Watch it run — check your email for the report

After that it runs automatically every day at 9 AM Eastern.
