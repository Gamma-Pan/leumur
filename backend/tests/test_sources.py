import asyncio
from datetime import datetime, timezone
import httpx
import pytest
from app import eurostat, planner
from app.models import ChartPlan, Clarification


def fixture(values, statuses=None):
    return {'id':['freq','unit','na_item','geo','time'],'size':[1,1,1,1,3],
        'dimension':{name:{'category':{'index':codes}} for name,codes in {'freq':['A'],'unit':['CP_MEUR'],'na_item':['B1GQ'],'geo':['EL'],'time':['2022','2023','2024']}.items()},
        'value':values,'status':statuses or {},'updated':'2025-01-01'}


def mock_client(monkeypatch, payload):
    original=httpx.AsyncClient
    def handler(request):
        assert request.url.params['geo']=='EL'
        assert request.url.params['unit']=='CP_MEUR'
        return httpx.Response(200,json=payload)
    monkeypatch.setattr(eurostat.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler)))


def test_latest_period_retains_missing_years_and_flags(monkeypatch):
    mock_client(monkeypatch,fixture({'0':10,'2':12},{'2':'p'}))
    plan=ChartPlan(dataset='nama_10_gdp',geo='EL',years=3,chart_type='line',time_basis='latest_available')
    points,url,updated=asyncio.run(eurostat.fetch_observations(plan))
    assert [point['year'] for point in points]==[2022,2023,2024]
    assert [point['value'] for point in points]==[10,None,12]
    assert points[-1]['status']=='p'
    assert 'na_item=B1GQ' in url and updated=='2025-01-01'


def test_wrong_unit_is_rejected(monkeypatch):
    payload=fixture({'0':10})
    payload['dimension']['unit']['category']['index']=['CP_EUR_HAB']
    mock_client(monkeypatch,payload)
    plan=ChartPlan(dataset='nama_10_gdp',geo='EL',years=3,chart_type='line',time_basis='latest_available')
    with pytest.raises(eurostat.SourceError,match='unexpected unit'):
        asyncio.run(eurostat.fetch_observations(plan))


def test_llm_plan_is_structured_and_cannot_change_measure(monkeypatch):
    baseline=planner.deterministic_plan('GDP of Greece for the last 10 years')
    original=httpx.AsyncClient
    def handler(request):
        import json
        body=json.loads(request.content)
        assert body['response_format']['json_schema']['strict'] is True
        assert body['response_format']['json_schema']['schema']['additionalProperties'] is False
        proposed=baseline.model_dump();proposed['dataset']='demo_gind'
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(proposed)}}]})
    monkeypatch.setattr(planner.settings,'llm_api_key','unit-test-only')
    monkeypatch.setattr(planner.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler)))
    with pytest.raises(Clarification,match='changed the interpreted request'):
        asyncio.run(planner.plan_query('GDP of Greece for the last 10 years',[{'dataset':'nama_10_gdp','content':'untrusted context'}]))
