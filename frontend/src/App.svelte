<script lang="ts">
 import {onMount} from 'svelte';
 import ChartView from './Chart.svelte';
 import type {Chart} from './types';
 let question=$state('GDP of Greece for the last 10 years');
 let mode=$state<'live'|'demo'>('live');
 let chart=$state<Chart|null>(null);
 let loading=$state(false);
 let error=$state('');
 let service=$state('Checking services');
 let table=$state(false);
 let chartType=$state<'line'|'bar'>('line');
 const examples=['GDP of Greece for the last 10 years','Population of France for the last 10 years','Unemployment in Spain for the last 10 years'];
 onMount(async()=>{try{const r=await fetch('/api/health');if(!r.ok)throw Error();const h=await r.json();service=h.ready?`${h.retrieval} retrieval · ${h.article_chunks} article chunks`:'Services need setup';}catch{service='Backend unavailable';}});
 async function submit(value=question){
  question=value;loading=true;error='';chart=null;
  try{const r=await fetch('/api/chart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:value,mode})});const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'Please check the question and try again.');chart=data;chartType=data.plan.chart_type;}
  catch(e){error=e instanceof Error?e.message:'Request failed.';}finally{loading=false;}
 }
 function download(){if(!chart)return;const csv='year,value,status\n'+chart.points.map(p=>`${p.year},${p.value??''},${p.status??''}`).join('\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));const a=document.createElement('a');a.href=url;a.download=`${chart.mode}-${chart.plan.dataset}-${chart.plan.geo}.csv`;a.click();URL.revokeObjectURL(url);}
</script>
<svelte:head><meta name="description" content="Explore European statistics with traceable, validated charts."/></svelte:head>
<div class="shell">
 <aside>
  <a class="brand" href="/" aria-label="Leumur home"><span class="brand-icon">▥</span> leumur<span class="brand-dot">.</span></a>
  <div class="workspace-label">YOUR WORKSPACE</div>
  <div class="nav-active"><span>↗</span> Explore data <span class="nav-badge">01</span></div>
  <div class="aside-note"><span class="tiny-dot"></span> EUROSTAT PROTOTYPE<br/><p>Three measures.<br/>One question at a time.<br/>Every number traceable.</p></div>
  <div class="aside-bottom">DATA, WITH CONTEXT.<br/><small>Built for curious minds.</small></div>
 </aside>
 <main>
  <header><span>Workspace <span class="slash">/</span> Explore</span><span class="status"><i></i>{service}</span></header>
  <section class="intro"><div class="eyebrow">FROM QUESTION TO UNDERSTANDING</div><h1>Let your data<br/><em>tell the story.</em></h1><p>Ask about Europe. Explore the numbers.<br/>Turn a question into a chart you can trust.</p></section>
  <section class="query-card" aria-label="Ask a data question">
   <div class="query-top"><label for="question">What would you like to explore?</label><span>ANNUAL STATISTICS</span></div>
   <form onsubmit={(e)=>{e.preventDefault();submit();}}>
    <textarea id="question" bind:value={question} rows="2" maxlength="1000" placeholder="e.g. GDP of Greece for the last 10 years"></textarea>
    <div class="query-footer"><label class="mode-label">Data source <select bind:value={mode} disabled={loading}><option value="live">Live Eurostat</option><option value="demo">Synthetic demo</option></select></label><button class="primary" disabled={loading||question.trim().length<3}>{loading?'Exploring…':'Create chart'} <span>↗</span></button></div>
   </form>
  </section>
  <div class="examples"><span>TRY A QUESTION</span>{#each examples as example}<button disabled={loading} onclick={()=>submit(example)}>{example.split(' for ')[0]} <span>↗</span></button>{/each}</div>
  {#if mode==='demo'}<p class="notice">Demo mode uses invented sample values to demonstrate the interface. It is not Eurostat data.</p>{/if}
  {#if error}<div class="error" role="alert"><strong>We couldn’t create this chart.</strong><p>{error}</p></div>{/if}
  {#if loading}<div class="loading" role="status"><span class="spinner"></span> Retrieving context and validating the dataset…</div>{/if}
  {#if chart}
   <section class="result">
    <div class="result-top"><div><div class="eyebrow">{chart.mode==='demo'?'SYNTHETIC DEMONSTRATION':'EUROSTAT OBSERVATIONS'}</div><h2>{chart.title}</h2><p>{chart.unit} · {chart.points[0].year}–{chart.points.at(-1)?.year}</p></div><div class="view-controls"><button class:active={!table} onclick={()=>table=false}>Chart</button><button class:active={table} onclick={()=>table=true}>Table</button><button onclick={download} aria-label="Download CSV">↓ CSV</button></div></div>
    {#each chart.warnings as warning}<p class="notice">{warning}</p>{/each}
    {#if table}<div class="table-wrap"><table><caption>{chart.title} · {chart.unit}</caption><thead><tr><th>Year</th><th>Value</th><th>Observation flag</th></tr></thead><tbody>{#each chart.points as point}<tr><td>{point.year}</td><td>{point.value?.toLocaleString()??'Missing'}</td><td>{point.status??'—'}</td></tr>{/each}</tbody></table></div>
    {:else}<div class="chart-options"><label>Chart type <select bind:value={chartType}><option value="line">Line</option><option value="bar">Bar</option></select></label></div><ChartView points={chart.points} type={chartType} title={chart.title} unit={chart.unit}/>{/if}
    <div class="interpretation"><span>↳</span><p>{chart.interpretation}</p></div>
    <details><summary>Sources & retrieval context <span>{chart.provenance.dataset}</span></summary><div class="sources"><p>Filters: <code>{JSON.stringify(chart.provenance.filters)}</code></p><p>Retrieved: {new Date(chart.provenance.retrieved_at).toLocaleString()} {chart.cached?'· cached response':''}</p><p>Source update: {chart.provenance.source_updated??'Unavailable'}</p>{#if chart.provenance.source_url}<a href={chart.provenance.source_url} target="_blank" rel="noreferrer">Eurostat API request ↗</a>{/if}<a href={chart.provenance.article_url} target="_blank" rel="noreferrer">Statistics Explained article ↗</a><p>Article mapping: {chart.provenance.article_relationship}</p><p>Retrieval: {chart.retrieval.method} · Planner: {chart.retrieval.planner}</p>{#each chart.retrieval.context as context}<div class="context"><strong>{context.kind} · {context.dataset}</strong><p>{context.content}</p><a href={context.source} target="_blank" rel="noreferrer">Source ↗</a></div>{/each}</div></details>
   </section>
  {:else if !loading}
   <section class="empty-state"><div class="mini-chart"><span></span><span></span><span></span><span></span><span></span><span></span></div><div><h3>A little curiosity goes a long way.</h3><p>Your chart will appear here, along with the data<br/>and the context behind it.</p></div><span class="empty-number">01 — 03</span></section>
  {/if}
  <footer><span>GDP <i>·</i> Population <i>·</i> Unemployment</span><span>European statistics. Clearer perspectives.</span></footer>
 </main>
</div>
