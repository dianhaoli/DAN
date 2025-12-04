# DAN - Strava for Studying


## Overview

Branch is a gamified productivity tracker that measures and improves how people study — combining Strava's social model with AI insights and a browser extension for passive tracking.

Built a data-driven productivity web app (React, Firebase, Node.js) to collect behavioral data for analysis;
Implemented Firebase authentication and Firestore pipelines for event logging (to-dos, timers, tab activity).
∗ Developed a Chrome extension for real-time attention tracking; integrated a DistilBERT classifier to label browser
activity and generate supervised learning signals.
∗ Implemented XGBoost regression for modeling user focus patterns from behavioral data, calculating a productivity
score for adaptive feedback and leaderboards.

## Tech Stack

- **Frontend**: Next.js 14, TailwindCSS, React Query
- **Extension**: Chrome Manifest v3
- **Backend**: Firebase (Firestore, Functions, Auth)
- **AI**: DistilBERT, XGBoost 
- **Hosting**: Vercel (web), Firebase (backend)


