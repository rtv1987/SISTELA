"""Offline automatic choices, with explicit user edits retained as reusable knowledge."""
from decimal import Decimal

from rapidfuzz.fuzz import WRatio, ratio
from sqlalchemy import select

from .handoff import target
from .models import MappingConfirmation, NormativeCatalogSource, NormEntry, SistelaMapping, utc_now
from .normative import search_catalog
from .parsers.common import normalize_text, normalize_unit
from .services import ServiceError


def catalog_candidates(session, line):
    source = session.scalar(select(NormativeCatalogSource).where(NormativeCatalogSource.active.is_(True)))
    if not source:
        return []
    kind = 'rate' if line.line_type == 'Work' else 'material'
    entries = search_catalog(session,line.project_description,kind,limit=60)
    if line.line_type in {'Material', 'Equipment'}:
        entries += search_catalog(session,line.project_description,'resource',limit=60)
        entries += search_catalog(session,line.project_description,'resource_price',limit=60)
        if line.technical_reference:
            for kind in ('material', 'resource', 'resource_price'):
                entries += search_catalog(session,line.technical_reference,kind,limit=30)
    categories = {m.sistela_code.split('-')[0] for m in session.scalars(select(SistelaMapping).where(SistelaMapping.system_type==line.system_type))}
    normalized = normalize_text(line.project_description)
    result = []
    for entry in entries:
        score = (WRatio if line.line_type=='Work' else ratio)(normalized,normalize_text(entry['description'])) / 100
        model = normalize_text(line.technical_reference)
        reference_text = normalize_text(entry['description']+' '+entry.get('model_reference',''))
        model_match = bool(len(model.replace(' ',''))>=3 and any(c.isalpha() for c in model)
                           and any(c.isdigit() for c in model) and f' {model} ' in f' {reference_text} ')
        if model_match:
            score = max(score, .95)
        if score < .45:
            continue
        score = min(.99,score + (.04 if entry['category'] in categories else 0))
        compatible = bool(entry['unit']) and normalize_unit(target(line)[1])==normalize_unit(entry['unit'])
        result.append({'mapping_id':'catalog:'+entry['id'], 'sistela_code':entry['code'],
            'sistela_description':entry['description'], 'source_unit':entry['unit'],
            'confidence':str(round(score,2)), 'method':'exact' if normalized==normalize_text(entry['description']) else 'fuzzy',
            'origin':'catalog', 'confirmed_count':0,'last_used_at':None,'compatible':compatible,
            'automatic_eligible': model_match or ratio(normalized,normalize_text(entry['description'])) >= 85,
            'priority':4 if score>=.9 else 5,'catalog_id':entry['id'],
            'evidence_eligible':True,'category':entry['category']})
    return sorted({r['mapping_id']:r for r in result}.values(),key=lambda r:(not r['compatible'],-float(r['confidence'])))


def lookup_code(session, code, line_type='Work'):
    return session.scalar(select(NormEntry).join(NormativeCatalogSource).where(
        NormativeCatalogSource.active.is_(True), NormEntry.kind.in_(['rate'] if line_type=='Work' else ['material','resource','resource_price']), NormEntry.code==code).order_by(NormEntry.kind).limit(1))


def automatic_values(session, line):
    from .mapping import suggestions
    if line.sistela_code or line.line_type not in {'Work','Material','Equipment'} or (line.review_data or {}).get('manual_code_edit'):
        return None
    candidates = suggestions(session,line)
    # Weak material resemblance is not enough to substitute a different device.
    candidate = next((c for c in candidates if c['compatible'] and (
        c['origin']=='user' and c['method'] in {'exact','normalized'}
        or c.get('historical_confirmed')
        or c.get('automatic_eligible', c['origin']!='catalog') and Decimal(c['confidence']) >= (Decimal('.85') if line.line_type!='Work' else Decimal('.70')))), None)
    if candidate is None:
        from .preparation import custom_code
        return {'sistela_code':custom_code(session,line), 'mapping_status':'suggested',
                'review_data':{**(line.review_data or {}),'automatic':True,'generated_code':True,
                               'code_type':'custom','normative_unit':target(line)[1]}}
    entry = lookup_code(session,candidate['sistela_code'],line.line_type)
    if entry and entry.kind == 'resource':
        # Resource-norm codes belong to type 7, not the documented standalone
        # average-price type 6. Retain the match, prepare a valid custom position.
        from .preparation import custom_code
        return {'sistela_code':custom_code(session,line),'mapping_status':'suggested',
                'review_data':{**(line.review_data or {}),'automatic':True,'generated_code':True,
                    'code_type':'custom','normative_unit':target(line)[1],
                    'matched_resource':{'id':entry.id,'code':entry.code,'filename':entry.filename,
                                        'record_number':entry.record_number}}}
    description = entry.description if entry else candidate['sistela_description']
    normative_unit = entry.unit if entry else candidate['source_unit']
    candidate = {**candidate,'catalog_verified':bool(entry), 'catalog_id':entry.id if entry else None,
                 'source_unit':normative_unit}
    return {'sistela_code':candidate['sistela_code'], 'sistela_original_description':description,
            'confidence':Decimal(candidate['confidence']), 'mapping_status':'suggested',
            'review_data':{**(line.review_data or {}),'suggestion':candidate,
                           'code_type':'normative' if entry else 'custom',
                           'normative_unit':normative_unit,'automatic':True}}


def populate_automatic(session, project_id):
    from .grid import active_lines, update_versioned
    from .preparation import ensure_profile, row_options
    from .services import get_project
    ensure_profile(session, get_project(session, project_id))
    for line in active_lines(session,project_id):
        values = automatic_values(session,line)
        if values:
            update_versioned(session,line,line.version,values)
        if line.line_type in {'Work','Material','Equipment'}:
            options, evidence = row_options(line, lookup_code(session,line.sistela_code,line.line_type))
            review = dict(line.review_data or {})
            if 'export_options' not in review:
                update_versioned(session,line,line.version,{'review_data':{**review,
                    'export_options':options,'ngr_evidence':evidence}})


def learn_code_edit(session,line,previous_code,previous_candidate=None):
    """Called inside the grid's transaction, not a second confirmation operation."""
    entry = lookup_code(session,line.sistela_code,line.line_type)
    review = dict(line.review_data or {})
    previous_candidate = previous_candidate or review.get('suggestion')
    review.update(manual_code_edit=True,automatic=False,normative_unit=entry.unit if entry else target(line)[1],
                  code_type='normative' if entry else 'custom')
    review.pop('generated_code',None)
    review.pop('suggestion',None)
    line.review_data = review
    if entry:
        line.sistela_original_description = entry.description
    elif previous_code != line.sistela_code:
        line.sistela_original_description = ''
    if not line.sistela_code:
        return
    normalized = normalize_text(line.project_description)
    unit = normalize_unit(review['normative_unit'])
    item = session.scalar(select(SistelaMapping).where(SistelaMapping.system_type==line.system_type,
        SistelaMapping.line_type==line.line_type,
        SistelaMapping.normalized_source_text==normalized,SistelaMapping.source_unit==unit,
        SistelaMapping.sistela_code==line.sistela_code))
    if not item:
        item=SistelaMapping(system_type=line.system_type,line_type=line.line_type,source_text=line.project_description,
            normalized_source_text=normalized,source_unit=unit,sistela_code=line.sistela_code,
            sistela_description=line.sistela_original_description)
        session.add(item)
        session.flush()
    item.confirmed_count += 1
    item.usage_count += 1
    item.last_used_at = utc_now()
    session.add(MappingConfirmation(mapping_id=item.id,project_id=line.project_id,line_id=line.id,
        previous_code=previous_code,selected_code=line.sistela_code,source_text=line.project_description))
    line.review_data={**review,'correction':{'previous_code':previous_code,'previous_candidate':previous_candidate,
        'target_unit':review['normative_unit'],'source_unit':line.unit,'at':utc_now()}}


def choose_catalog(session, project_id, line_id, entry_id, version):
    from .grid import owned_line, update_versioned
    line=owned_line(session,project_id,line_id)
    entry=session.get(NormEntry,entry_id)
    if not entry or entry.kind not in ({'rate'} if line.line_type=='Work' else {'material','resource','resource_price'}):
        raise ServiceError(422,'Pasirinkta ne įkainio ar resurso eilutė.')
    previous=line.sistela_code
    update_versioned(session,line,version,{'sistela_code':entry.code,'sistela_original_description':entry.description,'entered_at':None})
    learn_code_edit(session,line,previous)
    line.review_data={**line.review_data,'normative_unit':entry.unit,'catalog_id':entry.id}
    session.commit()
    session.refresh(line)
    return line
