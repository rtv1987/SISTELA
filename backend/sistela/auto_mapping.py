"""Offline automatic choices, with explicit user edits retained as reusable knowledge."""
from decimal import Decimal

from rapidfuzz.fuzz import WRatio
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
    if line.line_type == 'Material':
        entries += search_catalog(session,line.project_description,'resource',limit=60)
    categories = {m.sistela_code.split('-')[0] for m in session.scalars(select(SistelaMapping).where(SistelaMapping.system_type==line.system_type))}
    normalized = normalize_text(line.project_description)
    result = []
    for entry in entries:
        score = WRatio(normalized,normalize_text(entry['description'])) / 100
        if score < .45:
            continue
        score = min(.99,score + (.04 if entry['category'] in categories else 0))
        compatible = bool(entry['unit']) and normalize_unit(target(line)[1])==normalize_unit(entry['unit'])
        result.append({'mapping_id':'catalog:'+entry['id'], 'sistela_code':entry['code'],
            'sistela_description':entry['description'], 'source_unit':entry['unit'],
            'confidence':str(round(score,2)), 'method':'exact' if normalized==normalize_text(entry['description']) else 'fuzzy',
            'origin':'catalog', 'confirmed_count':0,'last_used_at':None,'compatible':compatible,
            'priority':4 if score>=.9 else 5,'catalog_id':entry['id'],
            'evidence_eligible':True,'category':entry['category']})
    return sorted(result,key=lambda r:(not r['compatible'],-float(r['confidence'])))


def lookup_code(session, code, line_type='Work'):
    return session.scalar(select(NormEntry).join(NormativeCatalogSource).where(
        NormativeCatalogSource.active.is_(True), NormEntry.kind.in_(['rate'] if line_type=='Work' else ['material','resource']), NormEntry.code==code).limit(1))


def automatic_values(session, line):
    from .mapping import suggestions
    if line.sistela_code or line.line_type not in {'Work','Material'} or (line.review_data or {}).get('manual_code_edit'):
        return None
    candidates = suggestions(session,line)
    if not candidates:
        return None
    candidate = candidates[0]
    if Decimal(candidate['confidence']) < Decimal('.45') and not candidate.get('historical_confirmed'):
        return None
    entry = lookup_code(session,candidate['sistela_code'],line.line_type)
    description = entry.description if entry else candidate['sistela_description']
    normative_unit = entry.unit if entry else candidate['source_unit']
    candidate = {**candidate,'catalog_verified':bool(entry), 'catalog_id':entry.id if entry else None,
                 'source_unit':normative_unit}
    return {'sistela_code':candidate['sistela_code'], 'sistela_original_description':description,
            'confidence':Decimal(candidate['confidence']), 'mapping_status':'suggested',
            'review_data':{**(line.review_data or {}),'suggestion':candidate,
                           'normative_unit':normative_unit,'automatic':True}}


def populate_automatic(session, project_id):
    from .grid import active_lines, update_versioned
    from .services import get_project
    get_project(session, project_id)
    for line in active_lines(session,project_id):
        values = automatic_values(session,line)
        if values:
            update_versioned(session,line,line.version,values)


def learn_code_edit(session,line,previous_code,previous_candidate=None):
    """Called inside the grid's transaction, not a second confirmation operation."""
    entry = lookup_code(session,line.sistela_code,line.line_type)
    review = dict(line.review_data or {})
    previous_candidate = previous_candidate or review.get('suggestion')
    review.update(manual_code_edit=True,automatic=False,normative_unit=entry.unit if entry else target(line)[1],
                  code_type='normative' if entry else 'custom')
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
    if not entry or entry.kind not in ({'rate'} if line.line_type=='Work' else {'material','resource'}):
        raise ServiceError(422,'Pasirinkta ne įkainio ar resurso eilutė.')
    previous=line.sistela_code
    update_versioned(session,line,version,{'sistela_code':entry.code,'sistela_original_description':entry.description,'entered_at':None})
    learn_code_edit(session,line,previous)
    line.review_data={**line.review_data,'normative_unit':entry.unit,'catalog_id':entry.id}
    session.commit()
    session.refresh(line)
    return line
