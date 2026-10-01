"""Persisted, deterministic preparation; never manufacture prices or conversions."""
from copy import deepcopy
from datetime import date
from hashlib import sha256

from sqlalchemy import select

from .models import EstimateLine, EstimateSection, ExportSettings, NormEntry


def custom_code(session, line):
    prefix = {'Material': 'A', 'Work': 'W', 'Equipment': 'I'}[line.line_type]
    # Row identity, not row order: insertion/deletion/reload cannot renumber codes.
    for salt in range(100):
        code = prefix + sha256(f'{line.project_id}:{line.id}:{salt}'.encode()).hexdigest()[:15].upper()
        used = session.scalar(select(EstimateLine.id).where(
            EstimateLine.sistela_code == code, EstimateLine.id != line.id))
        if not used and not session.scalar(select(NormEntry.id).where(NormEntry.code == code).limit(1)):
            return code
    raise ValueError('Nepavyko rezervuoti unikalaus vartotojo kodo.')


def row_options(line, reference=None):
    """NGR 12 is documented 'other materials'; keep the inference visible."""
    review = line.review_data or {}
    options = {'mark': 'I' if line.line_type == 'Equipment' else 'S'}
    evidence = 'row_type'
    if line.line_type != 'Equipment':
        value = (reference.payload if reference else {}).get('NGR')
        try:
            group = int(str(value))
        except (TypeError, ValueError):
            group = 0
        if 1 <= group <= 12:
            options['ngr'] = group
            evidence = 'catalog:NGR'
        else:
            options['ngr'] = 12
            evidence = 'documented_generic_material_group'
    return {**options, **review.get('export_options', {})}, review.get('ngr_evidence', evidence)


def ensure_profile(session, project):
    key = 'project:' + project.id
    stored = session.get(ExportSettings, key)
    old = deepcopy(stored.value) if stored else {}
    token = sha256(project.id.encode()).hexdigest().upper()
    # Hierarchy labels are defaults, not replacements for source descriptions.
    name = ''.join(c if c not in ',<>=*' and ord(c) >= 32 else ' ' for c in project.name)
    name = ' '.join(name.encode('cp1257', errors='replace').decode('cp1257').split()) or 'Projektas'
    defaults = {'complex': {'code': 'A' + token[:9], 'name': name[:120]},
                'object': {'code': '1', 'name': name[:120]},
                'estimate': {'code': '1', 'name': name[:60]},
                'period': date.today().strftime('%Y%m'), 'filename': 'A' + token[:7],
                'sections': {}, 'rows': {}}
    value = {**defaults, **old}
    for key_part in ('complex', 'object', 'estimate'):
        value[key_part] = {k: old.get(key_part, {}).get(k) or v for k, v in defaults[key_part].items()}
    for key_part in ('period', 'filename'):
        value[key_part] = old.get(key_part) or defaults[key_part]
    value['sections'] = deepcopy(value.get('sections',{}))
    sections = {s.id:s.name for s in session.scalars(select(EstimateSection).where(
        EstimateSection.project_id==project.id))}
    used = {s.get('code') for s in value['sections'].values()}
    for line in session.scalars(select(EstimateLine).where(EstimateLine.project_id==project.id,
            EstimateLine.deleted_at.is_(None)).order_by(EstimateLine.sort_order,EstimateLine.id)):
        section_id = line.section_id or 'manual-'+line.line_type
        if section_id in value['sections']:
            continue
        code = next((str(i) for i in range(1,1000) if str(i) not in used), '')
        used.add(code)
        value['sections'][section_id] = {'code':code,'name':sections.get(line.section_id,
            {'Work':'Darbai','Material':'Medžiagos','Equipment':'Įrenginiai','Other':'Kita'}.get(line.line_type,'')),
            'coefficients':{}}
    if not stored:
        stored = ExportSettings(key=key, value=value)
        session.add(stored)
    elif value != old:
        stored.value = value
    session.flush()
    return stored
