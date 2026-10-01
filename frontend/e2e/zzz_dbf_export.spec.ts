import { expect, test } from '@playwright/test';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

test('experimental six-DBF clone downloads; current project export remains blocked',async({page,request})=>{
  const files=['sd','dd','nd','pd','td','od'].map(role=>[resolve(`../${role}25-04-14.dbf`),resolve(`../samples/sistela/${role}25-04-14.dbf`)].find(existsSync));
  test.skip(files.some(f=>!f),'Private six-file golden archive required');
  const project=await(await request.post('/projects',{data:{name:'DBF export experiment',system_type:'GSS'}})).json();
  await page.goto('/');await page.getByRole('button',{name:/DBF export experiment GSS/}).click();
  await page.getByRole('tab',{name:'Paruošta SISTELA',exact:true}).click();
  await page.getByRole('button',{name:'DBF eksportas'}).click();await page.getByText('Papildomas istorinio archyvo klonavimo bandymas',{exact:true}).click();
  await expect(page.getByText('Naudokite tik bandomai SISTELA sąmatai.',{exact:true})).toBeVisible();
  await page.getByLabel('Šeši originalaus archyvo DBF failai',{exact:true}).setInputFiles(files as string[]);
  const downloaded=page.waitForEvent('download');await page.getByRole('button',{name:'Atsisiųsti bandomąjį kloną ZIP'}).click();
  const download=await downloaded;const output=resolve('../tmp/phase9-e2e-clone.zip');await download.saveAs(output);
  expect(readFileSync(output).subarray(0,2).toString()).toBe('PK');
  await expect(page.locator('.dbf-experiment [role=status]')).toContainText('Dabartinis projektas neeksportuotas');
  expect((await request.post(`/projects/${project.id}/export/dbf`)).status()).toBe(409);
  await page.getByRole('button',{name:'Tikrinti projekto DBF kliūtis'}).click();
  await expect(page.locator('.dbf-experiment [role=status]')).toContainText('DBF eksportui liko');
  mkdirSync(resolve('../docs/screenshots'),{recursive:true});
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:resolve('../docs/screenshots/phase9-dbf-experiment.png'),fullPage:true});
});
