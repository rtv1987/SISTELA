"""Documented package distinctions; no market-price estimation or source mutation."""
import re
from decimal import Decimal, InvalidOperation


def package_description(value):
    """Replace delimiters, retaining every word and numeric value; never truncate."""
    original = value
    value = ' '.join(value.split())
    rules = ['whitespace'] if value != original else []
    converted = re.sub(r'(?<=\d),(?=\d)', '.', value)
    if converted != value:
        rules.append('decimal_comma_to_dot')
    value = converted
    if ',' in value:
        value = value.replace(',', ';')
        rules.append('list_comma_to_semicolon')
    return {'text': value, 'original': original, 'rules': rules,
            'basis': 'Manual pp.46–48: comma-delimited records; punctuation normalization policy, not escaping.'}


def price_case(row, reference, period):
    """A/B/C/D classify syntax separately from whether a numeric price is available."""
    base = {'source': 'source_document_or_user' if row['price'] is not None else None,
            'amount': row['price'], 'catalog_evidence': None}
    if reference:
        base['catalog_evidence'] = {'filename': reference.filename,
            'record': reference.record_number, 'code': reference.code}
        if reference.kind == 'resource':
            return {**base, 'category': 'D', 'explicit_price_required': None,
                'reason': 'Gamybinis resursas: 7 tipo forma priklauso nuo pagrindinės pozicijos; savarankiška 6 tipo forma neįrodyta.'}
        # A dated column is evidence for exactly that period, not a present-day price.
        key = 'KAI' + period[2:] if re.fullmatch(r'\d{6}', period or '') else ''
        amount = reference.payload.get(key) if key else None
        try:
            known = amount is not None and Decimal(str(amount)).is_finite() and Decimal(str(amount)) >= 0
        except InvalidOperation:
            known = False
        return {**base, 'category': 'A' if known else 'B', 'explicit_price_required': False,
            'catalog_amount': str(amount) if known else None, 'catalog_period': period if known else None,
            'catalog_field': key if known else None,
            'reason': 'Esama katalogo pozicija: 6,kodas,kiekis (vadovo 47 p.). Kainą parenka SISTELA; galutinį laikotarpį būtina patikrinti.'}
    return {**base, 'category': 'C', 'explicit_price_required': True,
        'reason': 'Vartotojo pozicija: R=7,kaina,NGR arba I=kaina (vadovo 47 p.). Praleidimas neįrodytas; nulis tik atskirame priėmimo eksperimente.'}
