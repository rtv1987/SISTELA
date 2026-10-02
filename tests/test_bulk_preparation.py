"""Product acceptance: whole-estimate export never depends on manual entered progress."""
import re
from decimal import Decimal

import pytest
from catalog_factory import catalog, dbf
from sqlalchemy.orm import Session
from test_workflow import client as workflow_client
from test_workflow import line, project

from sistela.db import make_engine
from sistela.models import HistoricalEstimate, HistoricalImport, HistoricalLine
from sistela.package_txt import parse_generated_txt

client = workflow_client


def test_shared_work_word_is_not_an_automatic_full_scope_match(client,tmp_path):
    folder=catalog(tmp_path/'source')
    client.post('/normative/folder',json={'path':str(folder)})
    pid=project(client)
    line(client,pid,line_type='Work',project_description='Kabelio montavimas dokumentacijos parengimas ir visos sistemos bandymai',unit='m')
    row=client.post(f'/projects/{pid}/automatic').json()[0]
    assert row['sistela_code'].startswith('W')
    assert row['review_data']['generated_code'] is True


def test_price_classification_and_clean_text_reach_export_without_source_mutation(client):
    pid=project(client)
    source='Vamzdelis D20, su tvirtinimo elementais'
    original=line(client,pid,line_type='Material',project_description=source,output_description=source,material_price='2.40')
    client.post(f'/projects/{pid}/automatic')
    client.put('/settings/sistela',json={'parameter89':0})
    report=client.get(f'/projects/{pid}/export/txt/validation').json()
    assert report['errors']==[] and report['price_cases'][0]['category']=='C'
    assert report['text_preparations'][0]['original']==source
    assert report['text_preparations'][0]['text']=='Vamzdelis D20; su tvirtinimo elementais'
    saved=client.get(f'/projects/{pid}/lines').json()[0]
    assert saved['project_description']==original['project_description']
    assert saved['output_description']==source
    assert client.post(f'/projects/{pid}/export/txt').status_code==200


@pytest.mark.parametrize('kind,prefix,mark',[('Material','A','S'),('Work','W','S'),('Equipment','I','I')])
def test_stable_custom_codes_metadata_and_bulk_export(client,kind,prefix,mark):
    pid=project(client)
    original=line(client,pid,line_type=kind,quantity='2',unit='vnt.',material_price='12.50',work_price='12.50')
    prepared=client.post(f'/projects/{pid}/automatic').json()[0]
    assert re.fullmatch(prefix+'[A-F0-9]{15}',prepared['sistela_code'])
    assert prepared['review_data']['export_options']['mark']==mark
    assert prepared['entered_at'] is None and prepared['mapping_status']!='confirmed'
    assert prepared['quantity']==original['quantity']
    assert client.post(f'/projects/{pid}/automatic').json()[0]==prepared
    model=client.get(f'/projects/{pid}/export/model').json()
    assert all(model[key]['code'] for key in ('complex','object','estimate'))
    assert model['period'] and len(model['filename'])<=8
    assert client.get(f'/projects/{pid}/export/model').json()==model
    assert client.put('/settings/sistela',json={'parameter89':0}).status_code==200
    output=client.post(f'/projects/{pid}/export/txt')
    assert output.status_code==200,output.text
    record=parse_generated_txt(output.content)[-1]
    assert record[1:3]==[prepared['sistela_code'],'2']
    assert '<'+mark+',vnt.>' in record
    assert client.get(f'/projects/{pid}/validation').json()['status']=='READY_FOR_SISTELA'


def test_prices_remain_unresolved_without_manufactured_zero_or_metadata_blockers(client):
    pid=project(client)
    line(client,pid,line_type='Material')
    client.post(f'/projects/{pid}/automatic')
    client.put('/settings/sistela',json={'parameter89':0})
    model=client.get(f'/projects/{pid}/export/model').json()
    row=model['sections'][0]['rows'][0]
    assert row['price'] is None and row['options']['ngr']==12
    report=client.get(f'/projects/{pid}/export/txt/validation').json()
    assert len(report['errors'])==1
    assert 'Trūksta kainos' in report['errors'][0]['message']
    assert client.post(f'/projects/{pid}/export/txt').status_code==422


def test_average_material_catalog_is_indexed_and_exportable_without_explicit_price(client,tmp_path):
    folder=catalog(tmp_path/'source')
    client.post('/normative/folder',json={'path':str(folder)})
    pid=project(client)
    line(client,pid,line_type='Material',project_description='Viela',output_description='Viela',unit='m')
    row=client.post(f'/projects/{pid}/automatic').json()[0]
    assert row['sistela_code']=='10'
    assert row['material_price'] is None
    client.put('/settings/sistela',json={'parameter89':0})
    output=client.post(f'/projects/{pid}/export/txt')
    assert output.status_code==200,output.text
    assert parse_generated_txt(output.content)[-1]==['6','10','12.345678']


def test_generated_code_edit_survives_reload_and_is_reused_only_for_compatible_rows(client):
    pid=project(client)
    line(client,pid,line_type='Material',project_description='Smoke model ZX12',unit='vnt.')
    row=client.post(f'/projects/{pid}/automatic').json()[0]
    edited=client.post(f'/projects/{pid}/grid',json={'edits':[{'id':row['id'],'version':row['version'],
        'values':{'sistela_code':'MYCUSTOM'}}]}).json()[0]
    assert client.post(f'/projects/{pid}/automatic').json()[0]['sistela_code']=='MYCUSTOM'
    assert edited['review_data']['correction']['previous_code']==row['sistela_code']
    other=project(client)
    for unit in ('vnt.','m'):
        line(client,other,line_type='Material',project_description='Smoke model ZX12',unit=unit)
    rows=client.post(f'/projects/{other}/automatic').json()
    assert rows[0]['sistela_code']=='MYCUSTOM' and rows[1]['sistela_code']!='MYCUSTOM'


def test_generated_codes_dont_collide_and_dont_renumber(client):
    pid=project(client)
    for _ in range(12):
        line(client,pid,line_type='Material')
    rows=client.post(f'/projects/{pid}/automatic').json()
    assert len({r['sistela_code'] for r in rows})==12
    first=rows[0]
    client.post(f'/projects/{pid}/grid',json={'deletes':[{'id':first['id'],'version':first['version']}]})
    assert [r['sistela_code'] for r in client.post(f'/projects/{pid}/automatic').json()]==[r['sistela_code'] for r in rows[1:]]


def test_twelve_rows_export_in_one_package_without_entry_or_confirmation(client):
    pid=project(client)
    for i in range(12):
        line(client,pid,line_type='Material' if i<11 else 'Work',
             project_description=f'Fixture row {i}',output_description=f'Fixture row {i}',
             material_price='1.25',work_price='2.50')  # Explicit fixture prices, never real-project defaults.
    client.post(f'/projects/{pid}/automatic')
    client.put('/settings/sistela',json={'parameter89':0})
    report=client.get(f'/projects/{pid}/validation').json()
    assert report['status']=='READY_FOR_SISTELA'
    assert report['txt']['ready_rows']==report['txt']['total_rows']==12
    output=client.post(f'/projects/{pid}/export/txt')
    assert output.status_code==200,output.text
    assert len([r for r in parse_generated_txt(output.content) if r[0]=='6'])==12
    rows=client.get(f'/projects/{pid}/lines').json()
    assert all(not r['entered_at'] and r['mapping_status']!='confirmed' for r in rows)
    plan=client.get(f'/projects/{pid}/dbf/plan').json()
    assert [r['sistela_code'] for r in plan['rows']]==[r['sistela_code'] for r in rows]
    assert any('CALCULATED_FIELDS_UNKNOWN' in e for e in plan['blockers'])


def test_row_options_are_edited_in_grid_and_version_guarded(client):
    pid=project(client)
    line(client,pid,line_type='Material')
    row=client.post(f'/projects/{pid}/automatic').json()[0]
    body={'version':row['version'],'options':{'mark':'S','ngr':5}}
    url=f"/projects/{pid}/lines/{row['id']}/export-options"
    assert client.put(url,json=body).status_code==200
    assert client.put(url,json=body).status_code==409
    assert client.get(f'/projects/{pid}/export/model').json()['sections'][0]['rows'][0]['options']['ngr']==5


def test_readiness_recomputes_after_price_edit_without_validate_action(client):
    pid=project(client)
    line(client,pid,line_type='Material')
    row=client.post(f'/projects/{pid}/automatic').json()[0]
    client.put('/settings/sistela',json={'parameter89':0})
    assert client.get(f'/projects/{pid}/validation').json()['status']=='NEEDS_REVIEW'
    client.post(f'/projects/{pid}/grid',json={'edits':[{'id':row['id'],'version':row['version'],
        'values':{'material_price':'4'}}]})
    assert client.get(f'/projects/{pid}/validation').json()['status']=='READY_FOR_SISTELA'


def test_section_defaults_persist_when_earlier_section_is_removed(client):
    pid=project(client)
    line(client,pid,line_type='Material')
    line(client,pid,line_type='Work')
    rows=client.post(f'/projects/{pid}/automatic').json()
    before=client.get(f'/projects/{pid}/export/model').json()
    work=next(s for s in before['sections'] if s['rows'][0]['row_type']=='Work')
    client.post(f'/projects/{pid}/grid',json={'deletes':[{'id':rows[0]['id'],'version':rows[0]['version']}]})
    after=client.get(f'/projects/{pid}/export/model').json()
    assert after['sections'][0]['code']==work['code']


def test_model_reference_search_is_exact_not_prefix_substitution(client,tmp_path):
    folder=catalog(tmp_path/'catalog')
    dbf(folder/'samkainw.dbf',[('KODAS','C',10),('PAVADIN','C',100),('KODMAT','N',3),
        ('MATOVNT','C',12),('MARKE','C',30)], [{'KODAS':'123','PAVADIN':'Fixture device',
        'KODMAT':3,'MATOVNT':'vnt.','MARKE':'ZX-12'}])
    client.post('/normative/folder',json={'path':str(folder)})
    assert client.get('/normative/search?q=ZX-12&kind=resource_price').json()[0]['code']=='123'
    pid=project(client)
    for model in ('ZX-12','ZX-1'):
        line(client,pid,line_type='Material',project_description='Unrelated description',
             technical_reference=model,unit='vnt.')
    rows=client.post(f'/projects/{pid}/automatic').json()
    assert rows[0]['sistela_code']=='123'
    assert rows[1]['review_data']['generated_code']


def test_material_history_is_reused_with_provenance_but_not_its_old_price(client,tmp_path):
    with Session(make_engine(tmp_path)) as session:
        archive=HistoricalImport(source_hash='fixture',source_reference='fixture',source_files=[],
            encoding='cp1257',parser_version='fixture')
        session.add(archive)
        session.flush()
        estimate=HistoricalEstimate(historical_import_id=archive.id,external_key={},name='Fixture',
            project_name='Fixture',system_type='GSS',system_evidence='fixture',source_reference={})
        session.add(estimate)
        session.flush()
        evidence=HistoricalLine(historical_estimate_id=estimate.id,external_key={},line_type='Material',
            description='Fixture material',normalized_description='fixture material',sistela_code='HMAT',
            unit='vnt.',quantity=Decimal(1),historical_price=Decimal(99),section_name='Medžiagos',
            system_type='GSS',evidence_type='DIRECT',confidence=Decimal(1),evidence={},status='NOT_APPLICABLE')
        session.add(evidence)
        session.commit()
        evidence_id=evidence.id
    pid=project(client)
    line(client,pid,line_type='Material',project_description='Fixture material',unit='vnt.')
    row=client.post(f'/projects/{pid}/automatic').json()[0]
    assert row['sistela_code']=='HMAT' and row['material_price'] is None
    assert evidence_id in row['review_data']['suggestion']['evidence_ids']
    assert not row['entered_at'] and row['mapping_status']!='confirmed'
