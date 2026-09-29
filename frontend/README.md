# SISTELA Assistant UI

React + TypeScript + Vite, TanStack Table, Radix Tabs ir Decimal.js.
`pnpm install --frozen-lockfile`, `pnpm dev` (backend turi veikti 8000 porte).
`pnpm build` sukuria dist, kurį aptarnauja FastAPI. CDN ir AI API nereikalingi.

`pnpm test` – Vitest/Testing Library; `pnpm lint` – TypeScript ir ESLint.
`pnpm exec playwright install chromium`, `pnpm test:e2e` – realus UI su izoliuota
SQLite baze. Backend venv turi būti repo šaknyje, o UI prieš E2E sukompiliuotas.
8000 portas turi būti laisvas. Tikro PDF E2E be privataus failo pažymimas skip.

Ekrano vaizdai docs/screenshots rodo tik sintetinius demonstracinius duomenis;
TEST-N50 yra testinis žymuo, ne tikras katalogo pasiūlymas.
