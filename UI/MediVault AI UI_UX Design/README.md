
  # MediVault AI UI/UX Design

  This is a code bundle for MediVault AI UI/UX Design. The original project is available at https://www.figma.com/design/BCLTwpAXo2pQTGiGrROR2Y/MediVault-AI-UI-UX-Design.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.

### Exposing the UI to a remote friend

This frontend listens on `0.0.0.0:5173` and can be shared via a tunnel.

1. Ensure `UI/MediVault AI UI_UX Design/.env` contains the backend tunnel URL:

```env
VITE_API_BASE_URL=https://unclip-bonehead-growl.ngrok-free.dev
NEXT_PUBLIC_API_BASE_URL=https://unclip-bonehead-growl.ngrok-free.dev
```

2. Start the frontend dev server:

```bash
cd "UI/MediVault AI UI_UX Design"
npm run dev
```

3. In a separate terminal, start the frontend tunnel from the repository root:

```bash
./scripts/start_frontend_tunnel.sh
```

4. Copy the public URL printed by the script and share it with your friend.

> The remote friend can use that public URL to open the app in their browser. The frontend will still call the backend via the configured tunnel URL.

 `NEXT_PUBLIC_API_BASE_URL=https://<your-tunnel>.ngrok-free.dev` (Next.js)

  Example (using the current tunnel URL used by the backend operator):

  ```bash
VITE_API_BASE_URL=https://unclip-bonehead-growl.ngrok-free.dev
  ```

  After updating the env file, restart the dev server. All network calls originate from the centralized `src/lib/apiConfig.ts` module which adds the required `ngrok-skip-browser-warning` header.
  