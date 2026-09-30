"""Read-only source ingestion; all writes go to the user's derived SQLite catalog."""
import hashlib
import json
import re
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from sqlalchemy import insert, select, text, update
from sqlalchemy.exc import IntegrityError

from .models import NormativeCatalogSource, NormEntry, NormRelation, new_id
from .parsers.common import normalize_text, normalize_unit
from .parsers.dbf import DbfReadError, read_dbf
from .services import ServiceError

PROFILES = {
    'erer': ('rate', 'IKAINIS', 'PAVADIN', 'MATO_VNT'),
    'resursai': ('resource', 'MEDZIAGA', 'PAVADIN', 'MVNT'),
    'gaminiai': ('material', 'IKAINIS', 'PAVADIN', 'MVNT'),
    'samkainw': ('resource_price', 'KODAS', 'PAVADIN', 'KODMAT'),
    'nturinys': ('section', 'IKAINIS', 'PAVADIN', ''),
    'ik_teksw': ('text', 'IKAINIS', 'SUDETIS', ''),
    'koef': ('coefficient', 'IKAINIS1', '', ''),
    'koefkoef': ('coefficient', 'IKAINIS1', 'PAVADIN', ''),
}
LIMIT_BYTES = 300 * 1024 * 1024


def scalar(value):
    return '' if value is None else str(value).strip()


def unit_label(value):
    return normalize_unit(scalar(value).casefold())


def source_manifest(folder):
    paths = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {'.dbf','.fpt'})
    if len(paths) > 100 or sum(p.stat().st_size for p in paths) > LIMIT_BYTES:
        raise ServiceError(413, 'Normatyvų bazė viršija 300 MB arba 100 failų ribą.')
    if len({p.name.casefold() for p in paths}) != len(paths):
        raise ServiceError(422, 'Dubliuoti DBF/FPT failų pavadinimai.')
    return [{'filename':p.name.casefold(), 'size':p.stat().st_size,
             'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]


def inspect_source(folder):
    before = source_manifest(folder)
    tables = {}
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.casefold() == '.dbf':
            try:
                tables[p.stem.casefold()] = read_dbf(p, encoding='cp1257')
            except DbfReadError as exc:
                raise ServiceError(422, f'{p.name}: DBF arba memo failo perskaityti nepavyko.') from exc
    if 'erer' not in tables:
        raise ServiceError(422, 'Trūksta erer.dbf normatyvų lentelės.')
    for name, (_, code, description, unit) in PROFILES.items():
        if name in tables and not {v for v in (code, description, unit) if v} <= {f.name for f in tables[name].fields}:
            raise ServiceError(422, f'{name}.dbf schema neatitinka palaikomo profilio.')
    if source_manifest(folder) != before:
        raise ServiceError(409, 'Normatyvų šaltinis pasikeitė importo metu.')
    return before, tables


def ingest_folder(session, folder: Path, label=None):
    if not folder.is_dir():
        raise ServiceError(422, 'Pasirinktas normatyvų aplankas nerastas.')
    manifest, tables = inspect_source(folder)
    fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    existing = session.scalar(select(NormativeCatalogSource).where(NormativeCatalogSource.fingerprint == fingerprint))
    if existing:
        session.execute(update(NormativeCatalogSource).values(active=False))
        existing.active = True
        session.commit()
        return source_out(existing, reused=True)
    units = defaultdict(set)
    unit_evidence = defaultdict(list)
    for table, identifier, label_field in [('samkainw','KODMAT','MATOVNT'),('orkainos','MVNT','MATOVNT'),('orkvisos','MVNT','MATOVNT')]:
        for i, row in enumerate(tables[table].records if table in tables else []):
            key, value = scalar(row.get(identifier)), unit_label(row.get(label_field))
            if key and value:
                units[key].add(value)
                if len(unit_evidence[key]) < 5:
                    unit_evidence[key].append({'filename':table+'.dbf','record':tables[table].record_numbers[i],'label':value})
    source = NormativeCatalogSource(fingerprint=fingerprint, label=label or folder.name,
        encoding='cp1257', manifest=manifest, diagnostics={})
    session.execute(update(NormativeCatalogSource).values(active=False))
    session.add(source)
    session.flush()
    entries, index = [], []
    for name, snapshot in tables.items():
        kind, code_field, description_field, unit_field = PROFILES.get(name, ('reference', 'IKAINIS', 'PAVADIN', ''))
        for row, record in zip(snapshot.records, snapshot.record_numbers):
            code = scalar(row.get(code_field))
            description = scalar(row.get(description_field))
            unit_id = scalar(row.get(unit_field))
            possibilities = units.get(unit_id, set())
            unit = next(iter(possibilities)) if len(possibilities) == 1 else ''
            payload = json.loads(json.dumps(row, default=str))
            if unit_id:
                payload['_unit_evidence'] = unit_evidence[unit_id]
                payload['_unit_candidates'] = sorted(possibilities)
            category = re.split(r'[-\s]', code)[0]
            entry = dict(id=new_id(), source_id=source.id, kind=kind, code=code,
                description=description, normalized_description=normalize_text(description), unit=unit,
                unit_id=unit_id, category=category, filename=snapshot.filename, record_number=record, payload=payload)
            entries.append(entry)
            if kind in {'rate','resource','material','section','text'}:
                index.append(dict(entry_id=entry['id'], source_id=source.id, code=normalize_text(code),
                                  description=entry['normalized_description'], category=category))
    rates = {e['code'] for e in entries if e['kind']=='rate'}
    resources = {e['code'] for e in entries if e['kind']=='resource'}
    relations = []
    for name, columns, kind in [('medznorm',[('MEDZIAGA1','NORMA1'),('MEDZIAGA2','NORMA2')],'material'),
                               ('mechnorm',[('MASINA','NORMA')],'mechanism'),
                               ('ikaimedz',[('MEDZIAGA','')],'material_reference')]:
        if name not in tables:
            continue
        for row, record in zip(tables[name].records, tables[name].record_numbers):
            for code_field, amount_field in columns:
                code = scalar(row.get(code_field))
                if not code:
                    continue
                relations.append(dict(id=new_id(), source_id=source.id, rate_code=scalar(row['IKAINIS']),
                    resource_code=code, kind=kind, amount=scalar(row.get(amount_field)) or None,
                    resolved=scalar(row['IKAINIS']) in rates and code in resources,
                    filename=tables[name].filename, record_number=record))
    source.diagnostics = {'counts':dict(Counter(e['kind'] for e in entries)),
        'tables':[{ 'filename':s.filename,'records':len(s.records),'fields':s.schema()} for s in tables.values()],
        'unit_conflicts':{k:sorted(v) for k,v in units.items() if len(v)>1},
        'unresolved_relations':sum(not r['resolved'] for r in relations),
        'relationships':len(relations), 'missing_optional':sorted(set(PROFILES)-tables.keys())}
    try:
        for start in range(0,len(entries),1000):
            session.execute(insert(NormEntry), entries[start:start+1000])
        for start in range(0,len(relations),1000):
            session.execute(insert(NormRelation), relations[start:start+1000])
        for start in range(0,len(index),1000):
            session.execute(text('INSERT INTO normative_fts(entry_id,source_id,code,description,category) VALUES (:entry_id,:source_id,:code,:description,:category)'), index[start:start+1000])
        if source_manifest(folder) != manifest:
            raise ServiceError(409, 'Normatyvų šaltinis pasikeitė importo metu.')
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ServiceError(409, 'Katalogas jau importuojamas. Atnaujinkite sąrašą.') from exc
    except Exception:
        session.rollback()
        raise
    return source_out(source)


def ingest_zip(session, path, label='ZIP'):
    try:
        with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory(prefix='sistela-catalog-') as temp:
            files = archive.infolist()
            if len(files)>500 or sum(i.file_size for i in files)>LIMIT_BYTES:
                raise ServiceError(413, 'ZIP viršija normatyvų importo ribas.')
            selected = {}
            for item in files:
                name = PurePosixPath(item.filename.replace('\\','/'))
                if name.is_absolute() or '..' in name.parts or ':' in item.filename:
                    raise ServiceError(422, 'ZIP turi nesaugų failo kelią.')
                if name.suffix.casefold() not in {'.dbf','.fpt'}:
                    continue
                key = name.name.casefold()
                if key in selected:
                    raise ServiceError(422, 'ZIP turi kelias to paties DBF/FPT kopijas.')
                selected[key] = item
            for name, item in selected.items():
                (Path(temp)/name).write_bytes(archive.read(item))
            return ingest_folder(session, Path(temp), label)
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise ServiceError(422, 'ZIP nepavyko perskaityti. Patikrinkite archyvą.') from exc


def source_out(source, reused=False):
    return {'id':source.id, 'fingerprint':source.fingerprint, 'label':source.label,
            'imported_at':source.imported_at, 'active':source.active, 'encoding':source.encoding,
            'manifest':source.manifest, 'diagnostics':source.diagnostics, 'reused':reused}


def entry_out(entry):
    return {name:getattr(entry,name) for name in ('id','source_id','kind','code','description','unit',
        'unit_id','category','filename','record_number')}


def search_catalog(session, query='', kind='rate', unit='', category='', limit=30):
    source = session.scalar(select(NormativeCatalogSource).where(NormativeCatalogSource.active.is_(True)))
    if not source:
        return []
    base = select(NormEntry).where(NormEntry.source_id==source.id, NormEntry.kind==kind)
    if unit:
        base = base.where(NormEntry.unit==unit_label(unit))
    if category:
        base = base.where(NormEntry.category==category)
    if not query.strip():
        return [entry_out(e) for e in session.scalars(base.order_by(NormEntry.code).limit(limit))]
    exact = session.scalars(base.where(NormEntry.code==query.strip().upper()).limit(limit)).all()
    tokens = normalize_text(query).split()[:12]
    if not tokens:
        return [entry_out(e) for e in exact]
    match = ' OR '.join('"'+t+'"*' for t in tokens)
    ids = [r[0] for r in session.execute(text('SELECT entry_id FROM normative_fts WHERE normative_fts MATCH :q AND source_id=:source ORDER BY rank LIMIT 300'), {'q':match,'source':source.id})]
    rows = list(session.scalars(base.where(NormEntry.id.in_(ids)))) if ids else []
    order = {id:i for i,id in enumerate(ids)}
    rows.sort(key=lambda e:order[e.id])
    combined = {e.id:e for e in [*exact,*rows]}
    return [entry_out(e) for e in list(combined.values())[:limit]]
