"""Create a minimal, isolated acceptance package from a locally verified rate."""
import argparse
import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from sistela.auto_mapping import lookup_code
from sistela.db import make_engine
from sistela.package_txt import SistelaPackageTxtExporter


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=Path('data'))
    parser.add_argument('--code',required=True)
    parser.add_argument('--period',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise SystemExit('Acceptance destination already exists; preserve it.')
    with Session(make_engine(args.data)) as session:
        entry=lookup_code(session,args.code)
        if not entry or not entry.unit:
            raise SystemExit('Rate and unambiguous unit must exist in active catalog.')
        model={'complex':{'code':'TESTTXT','name':'TXT bandymas'},'object':{'code':'1','name':'TXT bandymas'},
            'estimate':{'code':'1','name':'TXT bandymas'},'period':args.period,'filename':'TESTTXT','parameter89':0,
            'sections':[{'id':'test','code':'1','name':'Darbai','rows':[{
                'id':'test','row_type':'Work','selected_code':entry.code,'code_type':'normative',
                'source_quantity':'1','source_unit':entry.unit,'target_quantity':'1','target_unit':entry.unit,
                'conversion_valid':True,'output_description':entry.description,'price':None,'options':{},
                'normative_reference':{'unit':entry.unit,'description':entry.description}}]}]}
        payload=SistelaPackageTxtExporter().export(model)
        manifest={'status':'EXPERIMENTAL','real_sistela':'UNVERIFIED','code':entry.code,'quantity':'1',
            'unit':entry.unit,'parameter89_required':0,'period':args.period,'source_id':entry.source_id,
            'source_file':entry.filename,'source_record':entry.record_number,
            'sha256':hashlib.sha256(payload).hexdigest(),'encoding':'cp1257','newline':'CRLF'}
    args.output.mkdir(parents=True)
    (args.output/'TESTTXT.TXT').write_bytes(payload)
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'README.txt').write_text(
        'EXPERIMENTAL. Tik atskiram bandomam kompleksui TESTTXT.\n'
        'SISTELA nustatykite parametrą 89=0. Paketo redaktoriuje naudokite vardą TESTTXT.\n'
        'Informacijos įvedimas → Informacija pakete → įklijuoti TESTTXT.TXT tekstą\n'
        '→ Tikrinti informaciją → Formuoti sąmatinę informaciją.\n'
        f"Patikrinkite: {args.code}, kiekis 1, vienetas {manifest['unit']}.\n"
        'Užrašykite diagnostiką, SISTELA versiją ir rezultatą. Nekeiskite esamų sąmatų.\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=True))


if __name__=='__main__':
    main()
