import { expect, test } from '@playwright/test';
import { existsSync, readFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

test('real GSS → human review → explicit conversion → ready → persisted entry → working XLSX',async({page,request})=>{
  test.setTimeout(120000);
  const source=['../2024-10-XX-TDP-GSS.pdf','../2024-10-XX-TDP-GSS(1).pdf','../samples/input/2024-10-XX-TDP-GSS.pdf'].map(p=>resolve(p)).find(existsSync);
  const files=['sd','dd','nd','pd','td','od'].map(role=>[resolve(`../${role}25-04-14.dbf`),resolve(`../samples/sistela/${role}25-04-14.dbf`)].find(existsSync));
  test.skip(!source||files.some(f=>!f),'Real private GSS and DBF fixtures required.');
  const form=new FormData();for(const file of files)form.append('files',new Blob([readFileSync(file!)]),file!.split(/[\\/]/).pop()!);form.append('encoding','cp1257');
  expect((await request.post('/history/imports',{multipart:form})).ok()).toBeTruthy();
  const project=await(await request.post('/projects',{data:{name:'PHASE 7 GSS acceptance',system_type:'GSS'}})).json();
  await page.goto('/');await page.getByRole('button',{name:/PHASE 7 GSS acceptance GSS/}).click();
  await page.getByLabel('PDF failas').setInputFiles(source!);
  await expect(page.getByText('21 eilučių',{exact:true})).toBeVisible({timeout:30000});
  const originals=await(await request.get(`/projects/${project.id}/lines`)).json();
  await page.getByRole('tab',{name:'Peržiūra',exact:true}).click();
  await expect(page.locator('.workflow')).toContainText('Blokuoja:');
  const initial=await(await request.get(`/projects/${project.id}/validation`)).json();
  expect(initial.summary).toMatchObject({total:21,materials:11,works:10});
  expect(initial.statistics.auto_suggested_mapping_count).toBeGreaterThan(0);
  const works=originals.filter((r:{line_type:string})=>r.line_type==='Work');
  for(let i=0;i<works.length;i++){
    const row=works[i];
    await page.getByRole('navigation',{name:'Peržiūros eilutės'}).getByRole('button').filter({has:page.getByText(row.project_description,{exact:true})}).click();
    if(row.unit==='m'){
      await page.getByLabel('Normatyvo vienetas',{exact:true}).fill('100m');
      await page.getByRole('button',{name:'Patvirtinti konversiją',exact:true}).click();
  await expect(page.locator('.review-layout article')).toContainText('Būsena: needs_review');
  await expect(page.getByText('Išsaugota lokaliai',{exact:true})).toBeVisible();
      await expect(page.getByLabel('Normatyvo vienetas',{exact:true})).toHaveValue('100m');
    }
    // Operator choices supplied by the test; these are not verified normative codes.
    const apply=page.locator('.suggestion button:enabled').filter({hasText:'Pasirinkti kodą'});
    if(i===0 && await apply.count()) {
      await apply.first().click();
      await expect(page.getByLabel('Patvirtinamas SISTELA kodas',{exact:true})).not.toHaveValue('');
    } else await page.getByLabel('Patvirtinamas SISTELA kodas',{exact:true}).fill(`TEST-GSS-${i}`);
    await page.getByRole('button',{name:'Išsaugoti kodą',exact:true}).click();
    await expect(page.locator('.confirmation-note')).toBeVisible();
  }
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();
  await page.getByRole('button',{name:'Patikrinti parengtį'}).click();
  await expect(page.locator('.workflow [role=status]')).toContainText('READY_FOR_SISTELA');
  const current=await(await request.get(`/projects/${project.id}/lines`)).json();
  expect(current.some((r:{review_data:{conversion?:unknown}})=>r.review_data.conversion)).toBeTruthy();
  expect(current.map((r:Record<string,unknown>)=>[r.quantity,r.unit,r.source_page,r.source_raw_text,r.source_document_id])).toEqual(originals.map((r:Record<string,unknown>)=>[r.quantity,r.unit,r.source_page,r.source_raw_text,r.source_document_id]));
  await page.getByRole('button',{name:'Atverti SISTELA Entry Mode',exact:true}).click();
  await page.locator('.entry-card h3').click();await page.keyboard.press('Enter');
  await expect(page.locator('.entry-progress strong')).toHaveText('1 / 10');
  await page.reload();await page.getByRole('tab',{name:'SISTELA Entry Mode'}).click();
  await expect(page.locator('.entry-progress strong')).toHaveText('1 / 10');
  await expect(page.locator('.entry-card h3')).toHaveText(works[1].project_description);
  await page.keyboard.press('Escape');
  const downloaded=page.waitForEvent('download');await page.getByRole('link',{name:'Eksportuoti darbinę sąmatą XLSX'}).click();
  expect((await downloaded).suggestedFilename()).toMatch(/\.xlsx$/);
});

test('review and ready screenshots with synthetic data; Entry Mode fits half a screen',async({page,request})=>{
  const project=await(await request.post('/projects',{data:{name:'SISTELA · Darbo peržiūra',system_type:'GSS'}})).json();
  const row=await(await request.post(`/projects/${project.id}/lines`,{data:{line_type:'Work',system_type:'GSS',project_description:'Kabelio montavimas',output_description:'Kabelio montavimas',quantity:'650',unit:'m'}})).json();
  await page.goto('/');await page.getByRole('button',{name:/SISTELA · Darbo peržiūra GSS/}).click();
  await page.getByRole('tab',{name:'Peržiūra',exact:true}).click();
  await expect(page.locator('.conversion-review')).toHaveCount(0);
  await page.getByLabel('Normatyvo vienetas',{exact:true}).fill('100m');
  await expect(page.getByRole('button',{name:'Patvirtinti konversiją',exact:true})).toBeVisible();
  mkdirSync(resolve('../docs/screenshots'),{recursive:true});
  await page.screenshot({path:resolve('../docs/screenshots/phase7-review.png'),fullPage:true,style:'.suggestion{display:none} .project-list button:not(.current){display:none}'});
  await page.getByRole('button',{name:'Patvirtinti konversiją',exact:true}).click();
  await expect(page.locator('.review-layout article')).toContainText('Būsena: needs_review');
  await expect(page.getByText('Išsaugota lokaliai',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Normatyvo vienetas',{exact:true})).toHaveValue('100m');
  await page.getByLabel('Patvirtinamas SISTELA kodas').fill('DEMO-N50');
  await page.getByRole('button',{name:'Išsaugoti kodą',exact:true}).click();
  await expect(page.locator('.confirmation-note')).toBeVisible();
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();
  await page.getByRole('button',{name:'Patikrinti parengtį'}).click();
  await expect(page.locator('.workflow [role=status]')).toContainText('READY_FOR_SISTELA');
  await page.getByText('Workflow statistics · vietinė darbo statistika',{exact:true}).click();
  await page.screenshot({path:resolve('../docs/screenshots/phase7-ready.png'),fullPage:true,style:'.project-list button:not(.current){display:none}'});
  await page.getByRole('button',{name:'Atverti SISTELA Entry Mode',exact:true}).click();
  await page.setViewportSize({width:800,height:1000});
  await expect(page.locator('.entry-field.quantity output')).toHaveText('6.5');
  await page.screenshot({path:resolve('../docs/screenshots/phase7-entry.png'),fullPage:true});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  const saved=await(await request.get(`/projects/${project.id}/lines`)).json();
  expect(saved[0].quantity).toBe(row.quantity);
});
