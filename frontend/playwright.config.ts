import { defineConfig } from '@playwright/test';
import { resolve } from 'node:path';
export default defineConfig({
  testDir: './e2e', workers: 1, timeout: 60000,
  use: { baseURL:'http://127.0.0.1:8000', viewport:{width:1600,height:1000}, trace:'retain-on-failure' },
  webServer: { command:`"${resolve('../.venv/Scripts/python.exe')}" "${resolve('../scripts/e2e_server.py')}"`, url:'http://127.0.0.1:8000/health', reuseExistingServer:false, timeout:30000 },
});
