import { expect, test } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

test('create → trash → absent from projects → restore',async({page,request})=>{
  await page.goto('/');
  await page.getByLabel('Naujas projektas',{exact:true}).click();
  await page.getByLabel('Projekto pavadinimas',{exact:true}).fill('PHASE 8 lifecycle');
  await page.getByRole('button',{name:'Sukurti projektą',exact:true}).click();
  await expect(page.getByRole('heading',{name:'PHASE 8 lifecycle'})).toBeVisible();
  await page.getByRole('button',{name:'Į šiukšlinę',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button',{name:'Perkelti į šiukšlinę',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Šiukšlinė'})).toBeVisible();
  expect((await(await request.get('/projects')).json()).some((p:{name:string})=>p.name==='PHASE 8 lifecycle')).toBeFalsy();
  await page.reload();await page.getByRole('button',{name:'Šiukšlinė',exact:true}).click();
  const card=page.locator('.trash-screen article').filter({hasText:'PHASE 8 lifecycle'});
  const screenshots=resolve('../docs/screenshots');mkdirSync(screenshots,{recursive:true});
  await expect(card).toBeVisible();await page.screenshot({path:resolve(screenshots,'phase8-trash.png'),fullPage:true});
  await card.getByRole('button',{name:'Atkurti',exact:true}).click();
  await expect(page.getByText('Projektas atkurtas.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:/PHASE 8 lifecycle GSS/}).click();
  await expect(page.getByRole('heading',{name:'PHASE 8 lifecycle'})).toBeVisible();
});

test('permanent deletion preserves imported and confirmed historical knowledge',async({page,request})=>{
  const before=await(await request.get('/history/lines?status=CONFIRMED')).json();
  expect(before.total).toBeGreaterThan(0);
  const imports=await(await request.get('/history/imports')).json();
  const project=await(await request.post('/projects',{data:{name:'Disposable project',system_type:'GSS'}})).json();
  await page.goto('/');await page.getByRole('button',{name:/Disposable project GSS/}).click();
  await page.getByRole('button',{name:'Į šiukšlinę',exact:true}).click();
  await page.getByRole('button',{name:'Perkelti į šiukšlinę',exact:true}).click();
  const card=page.locator('.trash-screen article').filter({hasText:'Disposable project'});
  await card.getByRole('button',{name:'Ištrinti visam laikui',exact:true}).click();
  const remove=page.getByRole('button',{name:'Patvirtinti galutinį ištrynimą'});
  await expect(remove).toBeDisabled();
  await page.getByLabel('Trinamo projekto pavadinimas').fill('Disposable project');
  await page.screenshot({path:resolve('../docs/screenshots/phase8-delete-confirmation.png'),fullPage:true});
  await remove.click();await expect(card).toHaveCount(0);
  expect((await request.get(`/projects/${project.id}`)).status()).toBe(404);
  expect(await(await request.get('/history/lines?status=CONFIRMED')).json()).toEqual(before);
  expect(await(await request.get('/history/imports')).json()).toEqual(imports);
});
