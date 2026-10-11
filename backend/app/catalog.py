"""Curated candidates. Availability is checked against live Eurostat before use."""
CATALOG = [
    {
        'code': 'nama_10_gdp', 'title': 'GDP and main components (annual)',
        'description': 'Gross domestic product GDP at current market prices, nominal economic output. Annual national accounts.',
        'article_relationship': 'direct dataset reference', 'measure': 'GDP', 'unit': 'Million euros, current prices',
        'filters': {'unit': 'CP_MEUR', 'na_item': 'B1GQ', 'freq': 'A'},
        'article': 'https://ec.europa.eu/eurostat/statistics-explained/index.php?title=National_accounts_and_GDP',
    },
    {
        'code': 'demo_gind', 'title': 'Population on 1 January',
        'description': 'Total resident population, number of people, annual demographic statistics.',
        'article_relationship': 'direct dataset reference', 'measure': 'Population', 'unit': 'Persons',
        'filters': {'indic_de': 'JAN', 'freq': 'A'},
        'article': 'https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Population_and_population_change_statistics',
    },
    {
        'code': 'une_rt_a', 'title': 'Unemployment by sex and age (annual)',
        'description': 'Unemployment rate, percentage of the labour force, ages 15 to 74, both sexes.',
        'article_relationship': 'annual companion to the article’s monthly dataset une_rt_m', 'measure': 'Unemployment', 'unit': 'Percent of labour force, ages 15–74',
        'filters': {'unit': 'PC_ACT', 'age': 'Y15-74', 'sex': 'T', 'freq': 'A'},
        'article': 'https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Unemployment_statistics',
    },
]
BY_CODE = {item['code']: item for item in CATALOG}
COUNTRIES = {'EL': 'Greece', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'ES': 'Spain', 'PT': 'Portugal', 'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria', 'IE': 'Ireland', 'PL': 'Poland', 'SE': 'Sweden', 'FI': 'Finland', 'DK': 'Denmark', 'CY': 'Cyprus'}
