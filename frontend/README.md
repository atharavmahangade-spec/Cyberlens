# CyberLens Frontend
React + TypeScript + Vite + MUI + Apache ECharts (all bundled locally, no CDN, no external calls).

    npm install      # one-time, on a machine with the npm registry / internal mirror
    npm run dev
    npm run typecheck && npm run build

## Architecture
- `src/types`     – TypeScript contracts (mirror future FastAPI/Pydantic models; Finding follows PRD §27 schema).
- `src/data/mock.ts` – ALL mock data. Components never contain analytics values.
- `src/services/api.ts` – the only data access layer. Set `VITE_API_BASE_URL` to switch from mock to FastAPI.
- `src/pages`     – one page per capability; `src/components` – shared UI.
No analytics are computed in the frontend; it renders what the backend returns (filtering/sorting for display only).
