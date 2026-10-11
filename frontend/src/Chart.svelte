<script lang="ts">
 import * as d3 from 'd3';
 import type {Point} from './types';
 let {points, type, title, unit}: {points:Point[];type:'line'|'bar';title:string;unit:string} = $props();
 const width=880,height=340,margin={top:25,right:30,bottom:45,left:85};
 let valid = $derived(points.filter((p):p is Point & {value:number}=>p.value!==null));
 let x = $derived(d3.scaleLinear().domain(d3.extent(points,p=>p.year) as [number,number]).range([margin.left,width-margin.right]));
 let y = $derived(d3.scaleLinear().domain([Math.min(0,d3.min(valid,p=>p.value)??0),Math.max(1,d3.max(valid,p=>p.value)??1)]).nice().range([height-margin.bottom,margin.top]));
 let line = $derived(d3.line<Point>().defined(p=>p.value!==null).x(p=>x(p.year)).y(p=>y(p.value??0))(points));
 let barWidth = $derived(Math.min(44,(width-margin.left-margin.right)/Math.max(points.length,1)*0.65));
 let selected:Point|null = $state(null);
</script>
<div class="plot-wrap">
 <svg viewBox="0 0 {width} {height}" role="img" aria-label="{title}, {type} chart in {unit}">
  <title>{title}</title>
  <desc>Annual observations. Missing values appear as gaps. Exact values are available in the data table.</desc>
  {#each y.ticks(5) as tick}
   <line x1={margin.left} x2={width-margin.right} y1={y(tick)} y2={y(tick)} stroke="#e5e8e3"/>
   <text x={margin.left-14} y={y(tick)+4} text-anchor="end" class="axis-label">{d3.format('~s')(tick)}</text>
  {/each}
  {#each points.filter((_,i)=>points.length<16||i%2===0) as point}
   <text x={x(point.year)} y={height-16} text-anchor="middle" class="axis-label">{point.year}</text>
  {/each}
  {#if type==='line'}
   <path d={line??''} fill="none" stroke="#267666" stroke-width="3"/>
  {/if}
  {#each valid as point}
   {#if type==='bar'}
    <rect role="img" aria-label={`${point.year}: ${point.value} ${unit}`} x={x(point.year)-barWidth/2} y={y(Math.max(0,point.value))} width={barWidth} height={Math.abs(y(point.value)-y(0))} rx="3" fill="#267666" onpointerenter={()=>selected=point} onpointerleave={()=>selected=null}><title>{point.year}: {point.value.toLocaleString()} {unit}</title></rect>
   {:else}
    <circle role="img" aria-label={`${point.year}: ${point.value} ${unit}`} cx={x(point.year)} cy={y(point.value)} r={selected?.year===point.year?6:4} fill="#267666" stroke="#fff" stroke-width="2" onpointerenter={()=>selected=point} onpointerleave={()=>selected=null}><title>{point.year}: {point.value.toLocaleString()} {unit}</title></circle>
   {/if}
  {/each}
 </svg>
 <div class="plot-hint">{#if selected}{selected.year} · {selected.value?.toLocaleString()} {unit}{:else}Hover over an observation to inspect its value{/if}</div>
</div>
