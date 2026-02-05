# DAN Chrome Extension

Automatic study session tracking extension for DAN.

## Setup

### 1. Install Dependencies

```bash
cd extension
npm install
```

### 2. Build Extension

```bash
npm run build
```

This creates a `dist/` folder with the compiled extension.

### 3. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/dist/` folder

### 4. Connect to Web App

1. Log in to the DAN web app (http://localhost:3000 or your deployed URL)
2. The web app will automatically sync Firebase credentials to the extension
3. Check the extension popup to verify connection status

## How It Works

### Automatic Tracking

- **Detects study domains**: Automatically starts tracking when you visit study-related websites
- **Monitors activity**: Tracks active time, idle time, and tab switches
- **Calculates metrics**: Computes focus score and XP earned
- **Saves to Backend**: Sessions are saved to FastAPI backend (with Firestore fallback)

### Manual Tracking

- Click the extension icon
- Enter a topic name
- Click "Start Session"
- Click "Stop Session" when done

### Offline Support

- Sessions are cached locally if backend is unavailable
- Automatically retries failed saves every 5 minutes
- No data loss if you're offline

## Configuration

### Firebase Config

The extension gets Firebase configuration from:
1. Web app sync (automatic when logged in)
2. Chrome storage (persisted after first sync)
3. Environment variables (fallback for development)

### Study Domains

Study domains are defined in `@dan/shared` package. Common domains include:
- Educational platforms (Khan Academy, Coursera, etc.)
- Coding platforms (GitHub, Stack Overflow, etc.)
- Documentation sites

## Development

### Watch Mode

```bash
npm run watch
```

Rebuilds automatically on file changes.

### Testing

1. Build the extension: `npm run build`
2. Load in Chrome (see above)
3. Open DevTools: Right-click extension icon → "Inspect popup"
4. Check background script logs: `chrome://extensions/` → Extension details → "Service worker"

## Troubleshooting

### Extension Not Saving Sessions

1. **Check user login**: Make sure you're logged in to the web app
2. **Check backend**: Verify FastAPI backend is running on `http://localhost:8000`
3. **Check Firebase config**: Open extension popup and verify connection status
4. **Check console**: Open DevTools and look for errors

### Sessions Not Appearing in Dashboard

1. **Check backend**: Verify FastAPI backend is running and database is connected
2. **Check user ID**: Verify sessions have correct `user_id` field
3. **Check retry queue**: Extension stores failed saves and retries automatically

### Extension Not Detecting Study Domains

1. **Check domain list**: Verify domains are in `STUDY_DOMAINS` in shared package
2. **Check URL format**: Extension extracts domain from full URL
3. **Manual start**: Use manual session start if automatic detection fails

## Permissions

The extension requires:
- `tabs`: To detect active tabs and URLs
- `storage`: To cache sessions and credentials
- `idle`: To detect when computer is idle
- `host_permissions`: To access all URLs for tracking

## Security

- Firebase credentials are stored locally in Chrome storage
- Only accessible to the extension (not other extensions)
- Sessions are saved with user authentication
- Firestore security rules prevent unauthorized access

