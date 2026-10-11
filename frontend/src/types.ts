export type Point = {year:number;value:number|null;status:string|null};
export type Chart = {
 title:string;unit:string;mode:'live'|'demo';cached:boolean;interpretation:string;
 plan:{dataset:string;geo:string;years:number;chart_type:'line'|'bar';time_basis:string};
 points:Point[]; warnings:string[];
 provenance:{dataset:string;filters:Record<string,string>;source_url:string|null;article_url:string;article_relationship:string;source_updated:string|null;retrieved_at:string};
 retrieval:{method:string;planner:string;context:{dataset:string;kind:string;source:string;content:string;score:number}[]};
};
