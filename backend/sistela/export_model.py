"""Single immutable-by-convention projection consumed by both SISTELA exporters."""
from decimal import Decimal

from sqlalchemy import select

from .grid import active_lines
from .handoff import target
from .models import EstimateSection, ExportSettings, NormativeCatalogSource, NormEntry, NormRelation
from .services import get_project


def settings(session, key):
    stored = session.get(ExportSettings, key)
    return dict(stored.value) if stored else {}


def save_settings(session, key, value):
    stored = session.get(ExportSettings, key)
    if stored:
        stored.value = value
    else:
        session.add(ExportSettings(key=key, value=value))
    session.commit()
    return value


def normalized_estimate(session, project_id):
    from .workflow import validate_project_for_sistela
    project = get_project(session, project_id)
    common = validate_project_for_sistela(session, project_id)
    profile = settings(session, 'project:' + project_id)
    sections = {s.id: s for s in session.scalars(select(EstimateSection).where(
        EstimateSection.project_id == project_id))}
    grouped = {}
    for line in active_lines(session, project_id):
        quantity, unit, valid = target(line)
        section_id = line.section_id or 'manual-' + line.line_type
        name = sections[line.section_id].name if line.section_id in sections else {
            'Work': 'Darbai', 'Material': 'Medžiagos'}.get(line.line_type, '')
        section = grouped.setdefault(section_id, {'id': section_id, 'code': str(len(grouped)+1),
            'name': name, 'coefficients': {}, 'rows': []})
        reference = session.scalar(select(NormEntry).join(NormativeCatalogSource).where(
            NormativeCatalogSource.active.is_(True), NormEntry.code == line.sistela_code,
            NormEntry.kind.in_(['rate'] if line.line_type == 'Work' else ['material', 'resource'])).limit(1))
        review = line.review_data or {}
        extra = dict(profile.get('rows', {}).get(line.id, {}))
        if extra.get('resources'):
            resources=[]
            for resource in extra['resources']:
                resource=dict(resource)
                resource['verified']=bool(reference and session.scalar(select(NormRelation.id).where(
                    NormRelation.source_id==reference.source_id, NormRelation.rate_code==reference.code,
                    NormRelation.resource_code==str(resource.get('code','')),
                    NormRelation.kind==('mechanism' if resource.get('flag')==2 else 'material'),
                    NormRelation.resolved.is_(True)).limit(1)))
                resources.append(resource)
            extra['resources']=resources
        section['rows'].append({
            'id': line.id, 'section_id': section_id, 'row_type': line.line_type,
            'source_description': line.project_description, 'output_description': line.output_description,
            'selected_code': line.sistela_code, 'code_type': 'normative' if reference else 'custom',
            'mapping_status': line.mapping_status,
            'source_quantity': str(line.quantity), 'source_unit': line.unit,
            'target_quantity': str(quantity), 'target_unit': unit, 'conversion_valid': valid,
            'price': str(line.material_price if line.line_type == 'Material' else line.work_price)
                if (line.material_price if line.line_type == 'Material' else line.work_price) is not None else None,
            'material_price': str(line.material_price) if line.material_price is not None else None,
            'work_price': str(line.work_price) if line.work_price is not None else None,
            'normative_reference': {'id': reference.id, 'source_id': reference.source_id,
                'filename': reference.filename, 'record_number': reference.record_number,
                'unit': reference.unit, 'description': reference.description} if reference else None,
            'provenance': {'document_id': line.source_document_id, 'page': line.source_page,
                'raw_text': line.source_raw_text, 'review': review},
            'warnings': ['LOW_CONFIDENCE'] if line.confidence is not None and line.confidence < Decimal('.7') else [],
            'options': extra,
        })
    for section in grouped.values():
        overrides = profile.get('sections', {}).get(section['id'], {})
        section.update({k: overrides[k] for k in ('code', 'name', 'coefficients') if k in overrides})
    return {'project_id': project_id,
        'common_issues': [{'context':row['id'],'message':issue['message']} for row in common['rows']
            for issue in row['issues'] if issue['severity']=='BLOCKING'],
        'complex': profile.get('complex', {'code': '', 'name': project.name}),
        'object': profile.get('object', {'code': '', 'name': project.name}),
        'estimate': profile.get('estimate', {'code': '', 'name': project.name}),
        'period': profile.get('period', ''), 'filename': profile.get('filename', 'TESTTXT'),
        'parameter89': settings(session, 'sistela').get('parameter89'),
        'sections': list(grouped.values())}
