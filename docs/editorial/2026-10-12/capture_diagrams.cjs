const fs = require('fs');
const path = require('path');
const puppeteer = require('/Users/danielwahnich/.nvm/versions/node/v20.18.3/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer');
(async () => {
 const dir=process.argv[2];
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 try {
  const page=await browser.newPage();
  await page.setViewport({width:1100,height:1200,deviceScaleFactor:1.5});
  const checks=[];
  for (const f of fs.readdirSync(dir).filter(f=>f.endsWith('.svg')).sort()) {
   const svg=fs.readFileSync(path.join(dir,f),'utf8');
   await page.setContent(`<html><body style="margin:0;background:${f.includes('-dark')?'#0d1117':'#ffffff'}">${svg}</body></html>`);
   const el=await page.$('svg');
   await el.screenshot({path:path.join(dir,f.replace('.svg','.png'))});
   const check=await page.evaluate(()=>{
    const svg=document.querySelector('svg');const box=svg.getBoundingClientRect();
    const labels=Array.from(svg.querySelectorAll('.nodeLabel,.edgeLabel')).map(n=>{const r=n.getBoundingClientRect();return {text:n.textContent.trim(),clipped:r.left<box.left-1||r.top<box.top-1||r.right>box.right+1||r.bottom>box.bottom+1}});
    return {width:box.width,height:box.height,labels:labels.length,clipped:labels.filter(l=>l.clipped)};
   });
   checks.push({file:f,...check});
  }
  fs.writeFileSync(path.join(dir,'layout_check.json'),JSON.stringify(checks,null,2)+'\n');
  console.log(JSON.stringify({rendered:checks.length,clipped:checks.filter(c=>c.clipped.length)}));
 } finally { await browser.close(); }
})();
