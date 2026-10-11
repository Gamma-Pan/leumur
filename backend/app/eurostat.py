import itertools
from datetime import datetime, timezone
import httpx
from .catalog import BY_CODE

API = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data'

class SourceError(Exception):
    pass

def decode_jsonstat(data: dict) -> list[dict]:
    """JSON-stat positions are row-major; absent sparse values remain missing."""
    dimensions = data['id']
    sizes = data['size']
    if len(dimensions) != len(sizes):
        raise SourceError('Malformed Eurostat dimensions.')
    categories = []
    labels = []
    for dimension, size in zip(dimensions, sizes):
        category = data['dimension'][dimension]['category']
        index = category['index']
        codes = index if isinstance(index, list) else [k for k, _ in sorted(index.items(), key=lambda item: item[1])]
        if len(codes) != size:
            raise SourceError('Eurostat dimension size mismatch.')
        categories.append(codes)
        labels.append(category.get('label', {}))
    values, statuses = data.get('value', {}), data.get('status', {})
    def lookup(container, position):
        if isinstance(container, list):
            return container[position] if position < len(container) else None
        return container.get(str(position))
    rows = []
    for position, codes in enumerate(itertools.product(*categories)):
        row = dict(zip(dimensions, codes))
        row['value'] = lookup(values, position)
        row['status'] = lookup(statuses, position)
        row['labels'] = {dimension: label.get(code, code) for dimension, code, label in zip(dimensions, codes, labels)}
        rows.append(row)
    return rows

async def fetch_observations(plan):
    item = BY_CODE[plan.dataset]
    params = dict(item['filters'], geo=plan.geo, lang='EN')
    current_year = datetime.now(timezone.utc).year
    # Fetch extra years for publication lag; truncate only after observing availability.
    params['sinceTimePeriod'] = str(current_year - plan.years - 5)
    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
            response = await client.get(f'{API}/{plan.dataset}', params=params)
            response.raise_for_status()
            data = response.json()
        rows = decode_jsonstat(data)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise SourceError('Eurostat could not be retrieved or decoded. Check network access and dataset filters.') from exc
    rows = [row for row in rows if row.get('geo') == plan.geo and str(row.get('time', '')).isdigit()]
    for row in rows:
        for dimension, expected in params.items():
            if dimension in data['id'] and row.get(dimension) != expected:
                raise SourceError(f'Eurostat returned an unexpected {dimension} filter.')
    # Reject residual dimensions rather than silently graphing incompatible observations.
    for dimension in data['id']:
        if dimension != 'time' and len({row[dimension] for row in rows}) > 1:
            raise SourceError(f'Unresolved Eurostat dimension: {dimension}.')
    if plan.time_basis == 'calendar_years':
        years = list(range(current_year - plan.years, current_year))
    else:
        available = [int(row['time']) for row in rows if row['value'] is not None]
        if not available:
            raise SourceError('No observations available for the selected filters.')
        end = max(available)
        years = list(range(end - plan.years + 1, end + 1))
    by_year = {int(row['time']): row for row in rows}
    points = [{'year': year, 'value': by_year.get(year, {}).get('value'), 'status': by_year.get(year, {}).get('status')} for year in years]
    if not any(point['value'] is not None for point in points):
        raise SourceError('No observations in the requested interval.')
    return points, str(response.url), data.get('updated')

def demo_observations(plan):
    # Deliberately synthetic, never represented as Eurostat observations.
    bases = {'nama_10_gdp': 100000, 'demo_gind': 10000000, 'une_rt_a': 12}
    base = bases[plan.dataset]
    end = datetime.now(timezone.utc).year - 1
    return [{'year': year, 'value': round(base * (1 + 0.025 * i), 2), 'status': 'synthetic'} for i, year in enumerate(range(end - plan.years + 1, end + 1))]
