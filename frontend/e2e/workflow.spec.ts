import { expect, test } from '@playwright/test';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

test('real GSS PDF import through the UI keeps provenance on duplication', async ({page, request}) => {
  const source = ['../2024-10-XX-TDP-GSS.pdf', '../2024-10-XX-TDP-GSS(1).pdf', '../samples/input/2024-10-XX-TDP-GSS.pdf'].map(p => resolve(p)).find(existsSync);
  test.skip(!source, 'Private GSS fixture not supplied; synthetic data is not a substitute.');
  const p = await (await request.post('/projects', {data:{name:'PDF regression',system_type:'GSS'}})).json();
  await page.goto('/');
  await page.getByRole('button', {name:/PDF regression GSS/}).click();
  await page.getByLabel('PDF failas').setInputFiles(source!);
  await expect(page.getByText('21 eilučių', {exact:true})).toBeVisible({timeout:30000});
  await expect(page.getByText('11 medžiagų', {exact:true})).toBeVisible();
  await expect(page.getByText('10 darbų', {exact:true})).toBeVisible();
  const original = (await (await request.get(`/projects/${p.id}/lines`)).json())[0];
  await page.getByLabel('Pažymėti eilutę 1', {exact:true}).check();
  await page.getByTitle('Dubliuoti pažymėtas eilutes').click();
  await expect(page.getByText('22 eilučių', {exact:true})).toBeVisible();
  const rows = await (await request.get(`/projects/${p.id}/lines`)).json();
  expect(rows[21].source_document_id).toBe(original.source_document_id);
  expect(rows[21].source_raw_text).toBe(original.source_raw_text);
  expect(rows[21].source_page).toBe(14);
});

test('create, edit, confirm, remember, enter, export and reimport', async ({page, request}) => {
  await page.goto('/');
  await page.getByRole('button', {name:'Naujas projektas', exact:true}).first().click();
  await page.getByLabel('Projekto pavadinimas', {exact:true}).fill('GSS · Demonstracinis projektas');
  await page.getByRole('button', {name:'Sukurti projektą'}).click();
  await expect(page.getByRole('heading', {name:'GSS · Demonstracinis projektas'})).toBeVisible();
  const projects = await (await request.get('/projects')).json();
  const pid = projects[0].id;
  await request.post(`/projects/${pid}/grid`, {data:{creates:[
    {system_type:'GSS', line_type:'Material', project_description:'Signalizacijos kabelis', output_description:'Signalizacijos kabelis', unit:'m', quantity:'650'},
    {system_type:'GSS', line_type:'Work', project_description:'Kabelio montavimas', output_description:'Projekto montavimo darbai', unit:'100m', quantity:'6.5'},
  ]}});
  await page.reload();
  await page.getByLabel('Kiekis 1', {exact:true}).fill('651.123456');
  await page.getByLabel('Kiekis 1', {exact:true}).press('Tab');
  await expect(page.getByText('Išsaugota lokaliai')).toBeVisible();
  await page.getByLabel('Projekto pavadinimas 2', {exact:true}).click();
  await page.getByLabel('Patvirtinamas SISTELA kodas', {exact:true}).fill('TEST-N50');
  await page.getByLabel('Originalus normatyvo pavadinimas', {exact:true}).fill('Demonstracinis normatyvas');
  await page.getByRole('button', {name:'Išsaugoti kodą'}).click();
  await expect(page.locator('.status.confirmed')).toHaveCount(1);
  mkdirSync(resolve('../docs/screenshots'), {recursive:true});
  await page.screenshot({path:resolve('../docs/screenshots/estimate-grid.png'), fullPage:true, style:'.suggestion:has(details) { display: none; }'});
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();await page.getByText('Papildomi būdai',{exact:true}).click();await page.getByRole('button',{name:'Rankinis perkėlimas',exact:true}).click();
  await page.getByRole('checkbox', {name:'Įtraukti medžiagas'}).check();
  await page.getByRole('button', {name:'Pažymėti suvestą'}).click();
  await expect(page.locator('.entry-progress strong')).toHaveText('1 / 2');
  await page.screenshot({path:resolve('../docs/screenshots/entry-mode.png'), fullPage:true});
  await page.reload();
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();await page.getByText('Papildomi būdai',{exact:true}).click();await page.getByRole('button',{name:'Rankinis perkėlimas',exact:true}).click();
  await page.getByRole('checkbox', {name:'Įtraukti medžiagas'}).check();
  await expect(page.locator('.entry-progress strong')).toHaveText('1 / 2');
  await page.getByRole('tab', {name:'Darbo lentelė'}).click();
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('link', {name:'XLSX', exact:true}).click();
  const download = await downloadEvent;
  const file = await download.path();
  expect(file).toBeTruthy();
  await page.getByRole('button', {name:'Excel importas', exact:true}).click();
  await page.getByLabel('XLSX failas').setInputFiles(file!);
  await expect(page.getByLabel('Darbo lapas')).toHaveValue('Darbo lentelė');
  await page.getByRole('button', {name:'Importuoti pasirinktą lapą'}).click();
  await expect(page.getByText('4 eilučių', {exact:true})).toBeVisible();
  await page.getByLabel('Projekto pavadinimas 3', {exact:true}).click();
  // Select imported work (source position 3 in the XLSX).
  await expect(page.locator('.suggestion').filter({hasText:'TEST-N50'}).getByRole('button', {name:'Pasirinkti kodą'})).toBeVisible();
  const rows = await (await request.get(`/projects/${pid}/lines`)).json();
  expect(rows[0].quantity).toBe('651.123456');
});

test('500 rows remain searchable and bulk actions can be undone', async ({page, request}) => {
  const p = await (await request.post('/projects', {data:{name:'500 eilučių',system_type:'AS'}})).json();
  const response = await request.post(`/projects/${p.id}/grid`, {data:{creates:Array.from({length:500}, (_,i) => ({
    project_description:`Elementas ${i}`,output_description:`Elementas ${i}`, quantity:'1',unit:'vnt.',system_type:'AS'}))}});
  expect(response.ok()).toBeTruthy();
  await page.goto('/');
  await page.getByRole('button', {name:/500 eilučių AS/}).click();
  await expect(page.getByText('500 eilučių', {exact:true}).last()).toBeVisible();
  await page.getByLabel('Ieškoti lentelėje').fill('Elementas 499');
  await expect(page.getByText('1 eilučių', {exact:true})).toBeVisible();
  await page.getByLabel('Pažymėti matomas eilutes').check();
  await page.getByLabel('Masinio keitimo reikšmė').fill('Patikrinta');
  await page.getByRole('button', {name:'Taikyti',exact:true}).click();
  await expect(page.getByLabel('Pastabos 500')).toHaveValue('Patikrinta');
  await page.getByTitle('Atšaukti paskutinį lentelės veiksmą').click();
  await expect(page.getByLabel('Pastabos 500')).toHaveValue('');
});
