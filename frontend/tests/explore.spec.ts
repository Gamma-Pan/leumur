import {test,expect} from '@playwright/test';

test('live Greece GDP renders, switches views and exports data', async({page})=>{
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Let your data tell the story.'})).toBeVisible();
 await page.getByRole('button',{name:'Create chart'}).click();
 await expect(page.getByRole('heading',{name:'GDP · Greece'})).toBeVisible({timeout:60000});
 await expect(page.getByRole('img',{name:/GDP · Greece, line chart/})).toBeVisible();
 await page.getByLabel('Chart type').selectOption('bar');
 await expect(page.getByRole('img',{name:/GDP · Greece, bar chart/})).toBeVisible();
 await page.getByRole('button',{name:'Table',exact:true}).click();
 await expect(page.locator('tbody tr')).toHaveCount(10);
 await expect(page.locator('tbody tr').first()).not.toContainText('Missing');
 await page.getByText('Sources & retrieval context').click();
 await expect(page.getByRole('link',{name:'Eurostat API request'})).toBeVisible();
 const downloadPromise=page.waitForEvent('download');
 await page.getByRole('button',{name:'Download CSV'}).click();
 expect((await downloadPromise).suggestedFilename()).toBe('live-nama_10_gdp-EL.csv');
 expect(errors).toEqual([]);
});

test('unsupported measure explains the limitation',async({page})=>{
 await page.goto('/');
 await page.getByLabel('What would you like to explore?').fill('Real GDP per capita in Greece');
 await page.getByRole('button',{name:'Create chart'}).click();
 await expect(page.getByRole('alert')).toContainText('not supported yet',{timeout:30000});
 await expect(page.getByRole('heading',{name:'GDP · Greece'})).toHaveCount(0);
});

test('synthetic mode is conspicuously labeled on mobile',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/');
 await page.getByLabel('Data source').selectOption('demo');
 await page.getByRole('button',{name:'Create chart'}).click();
 await expect(page.getByText('SYNTHETIC DEMO DATA — these values are not Eurostat observations.')).toBeVisible({timeout:30000});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
