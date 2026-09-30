import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from catalog_factory import catalog
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_workflow import client as workflow_client
from test_workflow import line, project

from sistela.db import make_engine, migrate
from sistela.models import NormEntry
from sistela.normative import ingest_folder, ingest_zip, search_catalog
from sistela.services import ServiceError

client = workflow_client

def test_folder_zip_idempotence_lookup_provenance_read_only(tmp_path):
    folder=catalog(tmp_path/'source')
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    migrate(tmp_path/'db')
    with Session(make_engine(tmp_path/'db')) as session:
        result=ingest_folder(session,folder)
        assert result['diagnostics']['counts']['rate']==3
        assert result['diagnostics']['missing_optional']
        rows=search_catalog(session,'TEST-3')
        assert rows[0]['unit']=='vnt.' and rows[0]['filename']=='erer.dbf'
        assert rows[0]['record_number']==3 and rows[0]['source_id']==result['id']
        assert search_catalog(session,'irenginiu')[0]['description']=='Įrenginių montavimas'
        assert search_catalog(session,'Kabelio',unit='m')[0]['code']=='TEST-1'
        assert search_catalog(session,'Kabelio',category='TEST')
        assert ingest_folder(session,folder)['reused']
        path=tmp_path/'catalog.zip'
        with zipfile.ZipFile(path,'w') as archive:
            for p in folder.iterdir():
                archive.write(p,'nested/'+p.name)
        assert ingest_zip(session,path)['id']==result['id']
        assert session.scalar(select(func.count()).select_from(NormEntry))==6
    assert before=={p.name:p.read_bytes() for p in folder.iterdir()}


@pytest.mark.parametrize('name',['../erer.dbf','C:/erer.dbf','/erer.dbf'])
def test_unsafe_zip_rejected(tmp_path,name):
    path=tmp_path/'bad.zip'
    with zipfile.ZipFile(path,'w') as archive:
        archive.writestr(name,b'bad')
    with pytest.raises(ServiceError):
        ingest_zip(None,path)


def test_invalid_and_missing_required_catalog(client,tmp_path):
    assert client.post('/normative/zip',files={'file':('bad.zip',b'bad')}).status_code==422
    assert client.post('/normative/folder',json={'path':str(tmp_path)}).status_code==422


def test_automatic_compatible_code_correction_learning_and_reload(client,tmp_path):
    folder=catalog(tmp_path/'source')
    assert client.post('/normative/folder',json={'path':str(folder)}).status_code==200
    pid=project(client)
    initial=line(client,pid)
    rows=client.post(f'/projects/{pid}/automatic').json()
    row=rows[0]
    assert row['sistela_code']=='TEST-1' and row['mapping_status']=='suggested'
    assert row['review_data']['suggestion']['catalog_verified']
    assert client.get(f'/projects/{pid}/validation').json()['blocking']==0
    assert client.post(f'/projects/{pid}/automatic').json()[0]['version']==row['version']
    result=client.post(f'/projects/{pid}/grid',json={'edits':[{'id':row['id'],'version':row['version'],'values':{'sistela_code':'USER-9'}}]})
    assert result.status_code==200,result.text
    changed=client.get(f'/projects/{pid}/lines').json()[0]
    correction=changed['review_data']['correction']
    assert correction['previous_code']=='TEST-1' and correction['previous_candidate']['origin']=='catalog'
    assert changed['source_raw_text']==initial['source_raw_text']
    other=project(client)
    line(client,other)
    reused=client.post(f'/projects/{other}/automatic').json()[0]
    assert reused['sistela_code']=='USER-9'
    assert reused['review_data']['suggestion']['origin']=='user'
    assert client.get(f'/projects/{other}/validation').json()['blocking']==0


def test_choose_catalog_unit_mismatch_requires_explicit_conversion(client,tmp_path):
    client.post('/normative/folder',json={'path':str(catalog(tmp_path/'source'))})
    entry=client.get('/normative/search?q=TEST-2').json()[0]
    pid=project(client)
    row=line(client,pid,quantity='650')
    response=client.post(f"/projects/{pid}/lines/{row['id']}/catalog",json={'entry_id':entry['id'],'version':row['version']})
    assert response.status_code==200,response.text
    row=response.json()
    assert row['quantity']=='650' and row['unit']=='m'
    assert client.get(f'/projects/{pid}/validation').json()['blocking']>0
    converted=client.post(f"/projects/{pid}/lines/{row['id']}/review",json={'version':row['version'],'action':'convert','target_unit':'100M'})
    assert converted.status_code==200
    assert client.get(f'/projects/{pid}/validation').json()['blocking']==0


@pytest.mark.fixtures
def test_real_normative_schema_resources_memo_and_read_only(tmp_path,request):
    root=Path(__file__).resolve().parents[1]
    folder=root/'data/fixtures/normative'
    if not folder.is_dir():
        if request.config.getoption('--require-fixtures'):
            pytest.fail('Missing licensed normative source')
        pytest.skip('Licensed normative source not supplied')
    expected=json.loads((root/'samples/normative-manifest.json').read_text(encoding='utf-8'))
    migrate(tmp_path)
    with Session(make_engine(tmp_path)) as session:
        result=ingest_folder(session,folder)
        assert result['diagnostics']['counts']['rate']==35035
        assert result['diagnostics']['relationships']==88576
        entry=search_catalog(session,'N50-270')[0]
        assert entry['code']=='N50-270' and entry['unit']=='vnt.'
        assert search_catalog(session,'',kind='section')
        assert search_catalog(session,'',kind='text')
        assert result['diagnostics']['unresolved_relations']>0
    for item in expected:
        assert hashlib.sha256((folder/item['filename']).read_bytes()).hexdigest()==item['sha256']


def test_txt_api_settings_and_same_normalized_dbf_model(client,tmp_path):
    client.post('/normative/folder',json={'path':str(catalog(tmp_path/'source'))})
    pid=project(client)
    line(client,pid,quantity='2',sistela_code='TEST-1')
    profile={'complex':{'code':'TEST','name':'Test'},'object':{'code':'1','name':'Test'},
        'estimate':{'code':'1','name':'Sąmata'},'period':'202609','filename':'TESTTXT'}
    assert client.put(f'/projects/{pid}/export/profile',json=profile).status_code==200
    assert client.post(f'/projects/{pid}/export/txt').status_code==422
    assert client.put('/settings/sistela',json={'parameter89':0}).status_code==200
    assert client.get('/settings/sistela').json()=={'parameter89':0}
    response=client.post(f'/projects/{pid}/export/txt')
    assert response.status_code==200,response.text
    assert b'6,TEST-1,2' in response.content
    assert list((tmp_path/'exports').glob('*/TESTTXT.TXT'))
    normalized=client.get(f'/projects/{pid}/export/model').json()
    dbf=client.get(f'/projects/{pid}/dbf/plan').json()
    assert normalized==dbf['normalized_estimate']
    assert dbf['rows'][0]['target_quantity']==normalized['sections'][0]['rows'][0]['target_quantity']


def test_material_correction_is_reused_without_polluting_work_mappings(client):
    pid=project(client)
    row=line(client,pid,line_type='Material',project_description='Viela')
    changed=client.post(f'/projects/{pid}/grid',json={'edits':[{'id':row['id'],'version':row['version'],
        'values':{'sistela_code':'MATERIAL1'}}]}).json()[0]
    assert changed['review_data']['code_type']=='custom'
    other=project(client)
    line(client,other,line_type='Material',project_description='Viela')
    line(client,other,line_type='Work',project_description='Viela')
    rows=client.post(f'/projects/{other}/automatic').json()
    assert rows[0]['sistela_code']=='MATERIAL1'
    assert rows[1]['sistela_code']==''


def test_catalog_selection_learns_once_and_preserves_source(client,tmp_path):
    client.post('/normative/folder',json={'path':str(catalog(tmp_path/'source'))})
    pid=project(client)
    row=line(client,pid)
    choices=client.get(f"/projects/{pid}/lines/{row['id']}/suggestions").json()
    response=client.post(f"/projects/{pid}/lines/{row['id']}/mapping/select",json={
        'version':row['version'],'mapping_id':choices[0]['mapping_id']})
    assert response.status_code==200,response.text
    selected=response.json()
    assert selected['quantity']==row['quantity'] and selected['unit']==row['unit']
    assert selected['review_data']['correction']['previous_candidate']['origin']=='catalog'
    assert client.get(f'/projects/{pid}/validation').json()['blocking']==0
    assert client.post(f"/projects/{pid}/lines/{row['id']}/mapping/select",json={
        'version':row['version'],'mapping_id':choices[0]['mapping_id']}).status_code==409
