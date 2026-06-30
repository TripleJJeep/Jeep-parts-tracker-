# Jeep Parts Competitor Tracker — Deployment Guide

This is a small web app that searches eBay live for competitor pricing on Jeep parts.
Follow these steps to put it online for free using Render.

## Step 1 — Create a Render account
1. Go to https://render.com
2. Click "Get Started" and sign up (you can use your email or GitHub account — no credit card required for the free tier)

## Step 2 — Get this code onto GitHub
Render deploys from a GitHub repository, so you need to put this folder there first.

1. Go to https://github.com and create a free account if you don't have one
2. Click the "+" icon top right → "New repository"
3. Name it something like `jeep-parts-tracker`, keep it Public, click "Create repository"
4. On the new repo page, click "uploading an existing file"
5. Drag in all 3 files/folders from this download: `app.py`, `requirements.txt`, and the `static` folder (with `index.html` inside it)
6. Click "Commit changes"

## Step 3 — Connect Render to your GitHub repo
1. Back in Render, click "New +" → "Web Service"
2. Choose "Build and deploy from a Git repository"
3. Connect your GitHub account if prompted, then select the `jeep-parts-tracker` repo
4. Fill in these settings:
   - **Name**: jeep-parts-tracker (or anything you like)
   - **Region**: choose the one closest to you
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

## Step 4 — Add your eBay App ID (important — keeps it private)
1. Still on the setup page, scroll to "Environment Variables"
2. Click "Add Environment Variable"
3. Key: `EBAY_APP_ID`
4. Value: your App ID, e.g. `AngryAar-producti-PRD-c0ac9b6db-35478808`
5. Click "Create Web Service"

## Step 5 — Wait for deploy
Render will install everything and start the app — takes about 2-3 minutes.
When it says "Live" at the top, click the URL it gives you (something like
`https://jeep-parts-tracker.onrender.com`) — that's your permanent link.

## Using it going forward
Just visit that URL any time — bookmark it. No need to redeploy or touch the code again
unless you want changes. Type a part name and hit Search.

## Notes
- The free Render tier "sleeps" after 15 minutes of no use — the first search after
  a break may take 10-20 seconds to wake up. Totally normal, no fix needed.
- Your eBay App ID is stored securely in Render's environment settings, never in the
  code itself, and never visible to website visitors.
