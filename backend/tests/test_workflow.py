import pytest
from pydantic import ValidationError
from app.eurostat import decode_jsonstat
from app.planner import deterministic_plan
from app.models import ChartPlan, Clarification
from app.ingest import chunk_text


def test_decode_sparse_row_major_and_flags():
    data = {'id': ['geo', 'time'], 'size': [2, 2], 'dimension': {
        'geo': {'category': {'index': {'EL': 0, 'FR': 1}, 'label': {'EL': 'Greece', 'FR': 'France'}}},
        'time': {'category': {'index': {'2023': 0, '2024': 1}}},
    }, 'value': {'0': 1, '2': 3, '3': 4}, 'status': {'3': 'p'}}
    rows = decode_jsonstat(data)
    assert [(r['geo'], r['time'], r['value']) for r in rows] == [('EL', '2023', 1), ('EL', '2024', None), ('FR', '2023', 3), ('FR', '2024', 4)]
    assert rows[-1]['status'] == 'p'
    assert rows[0]['labels']['geo'] == 'Greece'


def test_dense_jsonstat():
    rows = decode_jsonstat({'id':['time'], 'size':[2], 'dimension':{'time':{'category':{'index':['2023','2024']}}}, 'value':[0,None], 'status':['e',None]})
    assert rows[0]['value'] == 0
    assert rows[1]['value'] is None
    assert rows[0]['status'] == 'e'


def test_gdp_defaults_and_calendar_choice():
    plan = deterministic_plan('GDP of Greece for the last 10 years')
    assert plan.dataset == 'nama_10_gdp' and plan.geo == 'EL' and plan.years == 10
    assert plan.time_basis == 'latest_available'
    assert deterministic_plan('GDP of Greece for the last 5 calendar years').time_basis == 'calendar_years'


@pytest.mark.parametrize('question', ['real GDP of Greece', 'GDP per capita in Greece', 'GDP growth in Greece', 'GDP of Greece and France', 'GDP of Greece between 2010 and 2020', 'weather in Greece', 'GDP of Greece for the last 31 years'])
def test_unsupported_requests_do_not_silently_change_measure(question):
    with pytest.raises(Clarification):
        deterministic_plan(question)


def test_constrained_schema_rejects_invented_fields_and_code():
    with pytest.raises(ValidationError):
        ChartPlan(dataset='invented', geo='EL', years=10, chart_type='pie', time_basis='latest_available', sql='DROP TABLE')


def test_article_chunks_overlap_without_losing_text():
    text = 'x' * 4000
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert chunks[0][-200:] == chunks[1][:200]
    assert sum(map(len, chunks)) - 200 * (len(chunks) - 1) == len(text)
