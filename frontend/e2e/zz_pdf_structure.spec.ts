import { expect, test } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

test('ambiguous PDF → persisted previews → explicit selection → provenance', async ({ page, request }, testInfo) => {
  const file = testInfo.outputPath('ambiguous.pdf');
  execFileSync(resolve('../.venv/Scripts/python.exe'), ['-c',
    "import sys; from pathlib import Path; sys.path.insert(0, 'tests'); from pdf_factory import make_pdf, items; make_pdf(Path(sys.argv[1]), [items(), items()])", file],
    { cwd:resolve('..') });
  const project = await (await request.post('/projects', {data:{name:'PDF structure review',system_type:'GSS'}})).json();
  await page.goto('/');
  await page.getByRole('button', {name:/PDF structure review/}).click();
  await page.getByLabel('PDF failas').setInputFiles(file);
  await expect(page.getByText('Radome kelias galimas kiekių lenteles.')).toBeVisible();
  expect(await (await request.get(`/projects/${project.id}/lines`)).json()).toHaveLength(0);
  await page.reload();
  await page.getByRole('button', {name:/Importo informacija/}).click();
  await expect(page.getByText('Radome kelias galimas kiekių lenteles.')).toBeVisible();
  await page.screenshot({path:resolve('../docs/screenshots/pdf-schedule-selection.png'),fullPage:true});
  await page.getByRole('button',{name:/Pasirinkti lentelę/}).first().click();
  await expect(page.getByText('Importuota – reikia peržiūros')).toBeVisible();
  const lines = await (await request.get(`/projects/${project.id}/lines`)).json();
  expect(lines).toHaveLength(5);
  expect(JSON.parse(lines[0].source_raw_text).bounds.length).toBeGreaterThan(0);
  expect(lines.every((line:{mapping_status:string})=>line.mapping_status !== 'confirmed')).toBe(true);
});
