import copy

import pytest

from sistela.package_txt import SistelaPackageTxtExporter, parse_generated_txt, validate_txt_export


def model():
    return {'complex':{'code':'TEST','name':'Bandymas'},'object':{'code':'1','name':'Objektas'},
        'estimate':{'code':'1','name':'Sąmata'},'period':'202609','filename':'TESTTXT','parameter89':0,
        'sections':[{'id':'s','code':'1','name':'Darbai','rows':[{'id':'r','selected_code':'TEST-1',
            'code_type':'normative','source_quantity':'650','source_unit':'m','target_quantity':'6.5','target_unit':'100m',
            'conversion_valid':True,'output_description':'Kabelių montavimas','price':None,'options':{},
            'normative_reference':{'unit':'100m','description':'Kabelių montavimas'}}]}]}


def test_documented_hierarchy_decimal_encoding_roundtrip_no_double_conversion():
    value=model()
    data=SistelaPackageTxtExporter().export(value)
    assert b'6,TEST-1,6.5\r\n' in data
    records=parse_generated_txt(data)
    assert [r[0] for r in records]==['1','2','3','4','6']
    assert records[2]==['3','1','Sąmata','202609']
    assert records[-1][-1]=='6.5'


@pytest.mark.parametrize('setting',[None,1])
def test_unknown_or_automatic_reconversion_is_blocked(setting):
    value=model()
    value['parameter89']=setting
    assert validate_txt_export(value)['errors']
    with pytest.raises(ValueError):
        SistelaPackageTxtExporter().export(value)


def test_parameter_one_unscaled_unit_is_allowed():
    value=model()
    value['parameter89']=1
    row=value['sections'][0]['rows'][0]
    row.update(source_unit='vnt.',target_unit='vnt.',target_quantity='650')
    row['normative_reference']['unit']='vnt.'
    assert not validate_txt_export(value)['errors']


@pytest.mark.parametrize('change',[
    {'selected_code':'X'*19},{'target_quantity':'100000'},{'target_quantity':'0.0000001'},
    {'target_quantity':'NaN'},{'output_description':'a'*121},{'output_description':'a,b'},
    {'output_description':'Emoji 😀'},{'conversion_valid':False},{'selected_code':''},
    {'options':{'resources':[{'code':'unknown'}]}}, {'selected_code':'N5P-1'},
])
def test_invalid_fields_block_without_truncation(change):
    value=model()
    value['sections'][0]['rows'][0].update(change)
    assert validate_txt_export(value)['errors']


def test_custom_equipment_parameterized_coefficients_and_multiple_sections():
    value=model()
    section=value['sections'][0]
    row=section['rows'][0]
    row.update(code_type='custom',price='56.2',options={'mark':'S','ngr':8})
    data=SistelaPackageTxtExporter().export(value)
    assert '<S,100m>,P=Kabelių montavimas,R=7,56.2,8' in data.decode('cp1257')
    row['options']={'mark':'I'}
    assert 'I=56.2' in SistelaPackageTxtExporter().export(value).decode('cp1257')
    row.update(code_type='normative',selected_code='N5P-1',options={'parameters':[1,4],'coefficients':{'K1':'1.3'}})
    second=copy.deepcopy(section)
    second.update(id='s2',code='2',coefficients={'K41':'1.2'})
    value['sections'].append(second)
    text=SistelaPackageTxtExporter().export(value).decode('cp1257')
    assert 'G=1,4,,<K1=1.3>' in text and '4,2,Darbai, ,<K41=1.2>' in text


def test_missing_custom_financial_fields_and_duplicate_hierarchy():
    value=model()
    value['sections'][0]['rows'][0]['code_type']='custom'
    assert validate_txt_export(value)['errors']
    value['sections'].append(copy.deepcopy(value['sections'][0]))
    assert any('dubliuojasi' in e['message'] for e in validate_txt_export(value)['errors'])


def test_type_seven_linked_resource_adjustment():
    value=model()
    value['sections'][0]['rows'][0]['options']={'resources':[{'flag':2,'code':'489161','norm':'-0.23','verified':True}]}
    data=SistelaPackageTxtExporter().export(value)
    assert parse_generated_txt(data)[-1]==['7','2','489161','-0.23']
