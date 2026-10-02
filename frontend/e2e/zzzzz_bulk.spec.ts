import { expect, test } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

test('Darius: import 11 materials and 1 work → edit one code → bulk TXT, without manual transfer',async({page,request},info)=>{
  test.setTimeout(120000);
  const folder=info.outputPath('catalog');mkdirSync(folder,{recursive:true});
  const workbook=info.outputPath('priced-fixture.xlsx');
  execFileSync(resolve('../.venv/Scripts/python.exe'),['-c',
    "import sys;from pathlib import Path;sys.path.insert(0,'tests');from catalog_factory import catalog;from openpyxl import Workbook;catalog(Path(sys.argv[1]));w=Workbook();s=w.active;s.append(['Pavadinimas','Vnt.','Kiekis','Tipas','Medziagos kaina','Darbo kaina']);[s.append(['Model ZX'+str(i),'vnt.',str(i+1),'Material','12.50',None]) for i in range(11)];s.append(['Kabelio montavimas','m','28','Work',None,'2.50']);w.save(sys.argv[2])",folder,workbook],{cwd:resolve('..')});
  expect((await request.post('/normative/folder',{data:{path:folder}})).ok()).toBeTruthy();
  const p=await(await request.post('/projects',{data:{name:'12 eilučių · žinomos testinės kainos',system_type:'BULK'}})).json();
  let manualRequests=0;
  page.on('request',r=>{if(/\/entry$|\/mapping\/confirm$/.test(r.url()))manualRequests++;});
  await page.goto('/');await page.getByRole('button',{name:/12 eilučių · žinomos testinės kainos BULK/}).click();
  await page.getByRole('button',{name:'Excel importas',exact:true}).click();
  await page.getByLabel('XLSX failas',{exact:true}).setInputFiles(workbook);
  await page.getByRole('button',{name:'Importuoti pasirinktą lapą'}).click();
  await expect(page.getByText('12 eilučių',{exact:true})).toBeVisible();
  const before=await(await request.get(`/projects/${p.id}/lines`)).json();
  expect(before.filter((r:{line_type:string})=>r.line_type==='Material')).toHaveLength(11);
  expect(before.every((r:{sistela_code:string})=>r.sistela_code)).toBeTruthy();
  const codeLabel=`SISTELA kodas ${before[0].source_position}`;
  await page.getByLabel(codeLabel,{exact:true}).fill('MYCUSTOM21');
  await page.getByLabel(codeLabel,{exact:true}).press('Tab');
  await expect(page.getByText('Išsaugota lokaliai',{exact:true})).toBeVisible();
  await page.reload();await expect(page.getByLabel(codeLabel,{exact:true})).toHaveValue('MYCUSTOM21');
  await page.getByRole('button',{name:'Nustatymai · SISTELA',exact:true}).click();
  await page.getByLabel('Parametras 89').selectOption('0');
  await expect(page.getByText('SISTELA nustatymas išsaugotas visiems projektams.')).toBeVisible();
  await page.getByRole('button',{name:/12 eilučių · žinomos testinės kainos BULK/}).click();
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();
  await expect(page.getByText('12 iš 12 eilučių paruošta')).toBeVisible();
  await expect(page.getByRole('tab',{name:/Entry|Rankinis/})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Rankinis perkėlimas',exact:true})).not.toBeVisible();
  await expect(page.getByRole('button',{name:'Patikrinti parengtį'})).toHaveCount(0);
  await expect(page.getByLabel('Parametras 89')).toHaveCount(0);
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'TXT eksportas',exact:true}).click();
  const file=await download;await file.saveAs(info.outputPath('complete.TXT'));
  const data=readFileSync(info.outputPath('complete.TXT')).toString('latin1');
  expect(data.split('\r\n').filter(r=>r.startsWith('6,'))).toHaveLength(12);
  expect(data).toContain('6,MYCUSTOM21,1,');
  expect(manualRequests).toBe(0);
  await page.getByText('Techninės detalės / TXT peržiūra',{exact:true}).click();
  await page.screenshot({path:resolve('../docs/screenshots/022-txt-result.png'),fullPage:true,style:'.project-list button:not(.current){display:none}'});
  const next=await(await request.post('/projects',{data:{name:'Learned bulk correction',system_type:'BULK'}})).json();
  await request.post(`/projects/${next.id}/lines`,{data:{line_type:'Material',project_description:'Model ZX0',output_description:'Model ZX0',unit:'vnt.',quantity:'1',system_type:'BULK'}});
  const learned=await(await request.post(`/projects/${next.id}/automatic`)).json();
  expect(learned[0].sistela_code).toBe('MYCUSTOM21');
  const final=await(await request.get(`/projects/${p.id}/lines`)).json();
  expect(final.every((r:{entered_at:string|null;mapping_status:string})=>!r.entered_at&&r.mapping_status!=='confirmed')).toBeTruthy();
});

test('actual 12-row PDF and licensed catalogue: automatic preparation and precise remaining exceptions',async({page,request})=>{
  test.setTimeout(240000);
  const source=resolve('../data/documents/2024.07-616SR-BCB-AG.pdf'),catalog=resolve('../data/fixtures/normative');
  test.skip(!existsSync(source)||!existsSync(catalog),'Real private PDF and licensed catalogue required.');
  expect((await request.post('/normative/folder',{data:{path:catalog},timeout:120000})).ok()).toBeTruthy();
  const p=await(await request.post('/projects',{data:{name:'2024.07-616SR-BCB-AG · GSS',system_type:'GSS'}})).json();
  await page.goto('/');await page.getByRole('button',{name:/2024.07-616SR-BCB-AG · GSS GSS/}).click();
  await page.getByLabel('PDF failas',{exact:true}).setInputFiles(source);
  await expect(page.getByText('12 eilučių',{exact:true})).toBeVisible({timeout:120000});
  const rows=await(await request.get(`/projects/${p.id}/lines`)).json();
  expect(rows.filter((r:{line_type:string})=>r.line_type==='Material')).toHaveLength(11);
  expect(rows.every((r:{sistela_code:string})=>r.sistela_code)).toBeTruthy();
  expect(rows.every((r:{material_price:string|null})=>r.material_price===null)).toBeTruthy();
  await page.screenshot({path:resolve('../docs/screenshots/022-real-grid.png'),fullPage:true,style:'.project-list button:not(.current){display:none}.detail-panel{display:none}.editing-layout{grid-template-columns:1fr}.table-scroll{max-height:none;height:auto}'});
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();
  await expect(page.getByRole('button',{name:'TXT eksportas',exact:true})).toBeVisible();
  await expect(page.locator('.export-panel')).toContainText(/ iš 12 eilučių paruošta/);
  await expect(page.locator('.workflow-summary strong')).toHaveCount(3);
  await expect(page.getByText('Trūksta kodo',{exact:true})).toHaveCount(0);
  await expect(page.getByText('NGR grupė',{exact:true})).toHaveCount(0);
  await page.screenshot({path:resolve('../docs/screenshots/022-real-export.png'),fullPage:true,style:'.project-list button:not(.current){display:none}'});
  await page.getByRole('button',{name:'DBF eksportas',exact:true}).click();
  await expect(page.getByText(/CALCULATED_FIELDS_UNKNOWN/).first()).toBeVisible();
  await page.screenshot({path:resolve('../docs/screenshots/022-real-dbf.png'),fullPage:true,style:'.project-list button:not(.current){display:none}'});
  const model=await(await request.get(`/projects/${p.id}/export/model`)).json();
  expect(model.complex.code).toBeTruthy();expect(model.object.code).toBeTruthy();expect(model.estimate.code).toBeTruthy();
  const validation=await(await request.get(`/projects/${p.id}/export/txt/validation`)).json();
  expect(validation.errors.length).toBeGreaterThan(0); // Source has no prices; never manufacture them.
  expect(validation.text_preparations).toHaveLength(3);
  expect(validation.price_cases).toHaveLength(12);
  expect(validation.errors.some((e:{message:string})=>e.message.includes('kableliai'))).toBeFalsy();
  expect(validation.errors.every((e:{message:string})=>!e.message.includes('Trūksta privalomo teksto / kodo'))).toBeTruthy();
});

test('custom priced text is normalized automatically while catalog price is not required',async({page,request},info)=>{
  const folder=info.outputPath('catalog');mkdirSync(folder,{recursive:true});
  execFileSync(resolve('../.venv/Scripts/python.exe'),['-c',"import sys;from pathlib import Path;sys.path.insert(0,'tests');from catalog_factory import catalog;catalog(Path(sys.argv[1]))",folder],{cwd:resolve('..')});
  expect((await request.post('/normative/folder',{data:{path:folder}})).ok()).toBeTruthy();
  const project=await(await request.post('/projects',{data:{name:'022 price and punctuation',system_type:'TEST'}})).json();
  for(const row of [{project_description:'Viela',output_description:'Viela',unit:'m'}, {project_description:'Fixture D20, fittings',output_description:'Fixture D20, fittings',unit:'vnt.',material_price:'2.40'}]){
    expect((await request.post(`/projects/${project.id}/lines`,{data:{...row,quantity:'1',line_type:'Material',system_type:'TEST'}})).ok()).toBeTruthy();
  }
  await request.post(`/projects/${project.id}/automatic`);await request.put('/settings/sistela',{data:{parameter89:0}});
  await page.goto('/');await page.getByRole('button',{name:/022 price and punctuation TEST/}).click();
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();
  await expect(page.getByText('2 iš 2 eilučių paruošta')).toBeVisible();
  await expect(page.getByText(/TXT skyryba sutvarkyta automatiškai: 1/)).toBeVisible();
  const pending=page.waitForEvent('download');await page.getByRole('button',{name:'TXT eksportas',exact:true}).click();
  const file=await pending;await file.saveAs(info.outputPath('022.TXT'));
  const text=readFileSync(info.outputPath('022.TXT')).toString('latin1');
  expect(text).toContain('6,10,1');expect(text).toContain('Fixture D20; fittings');expect(text).toContain('R=7,2.4,12');
});
