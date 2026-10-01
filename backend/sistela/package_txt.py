"""Documented package subset, NAUJA_INSTR_ SAMATU_2011 pp.46–48.

Experimental until real SISTELA acceptance. Unknown grammar is rejected.
"""
import re
from decimal import Decimal, InvalidOperation

from .parsers.common import normalize_unit

PRICE_REQUIRED = 'Trūksta kainos: dokumentuotas vartotojo pozicijos formatas reikalauja kainos. Įveskite tikrą kainą darbo lentelėje; nulis automatiškai nepriskiriamas.'


def number(value, decimals=6, integers=5, positive=True):
    try:
        n = Decimal(str(value))
        if not n.is_finite() or (n <= 0 if positive else n < 0):
            raise ValueError('Kiekis / koeficientas turi būti teigiamas.')
        if n != n.quantize(Decimal(1).scaleb(-decimals)) or abs(n) >= 10**integers:
            raise ValueError(f'Skaičius netelpa į {integers}.{decimals} formatą.')
        return format(n.normalize(), 'f')
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('Netinkamas dešimtainis skaičius.') from exc


def field(value, limit=None, code=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Trūksta privalomo teksto / kodo.')
    if any(ord(c)<32 or c in ',<>=*' for c in value):
        raise ValueError('Tekste negalimi kableliai, valdymo ar paketo sintaksės ženklai.')
    if code and not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Kodas turi būti raidinis / skaitinis (leidžiama - ir _).')
    if limit is not None and len(value)>limit:
        raise ValueError(f'Tekstas viršija {limit} ženklų ribą; trumpinkite patys.')
    try:
        value.encode('cp1257')
    except UnicodeEncodeError as exc:
        raise ValueError('Tekstas netelpa į cp1257 koduotę.') from exc
    return value


def coefficients(values, allowed):
    if not isinstance(values, dict) or set(values)-set(allowed):
        raise ValueError('Nepalaikomi sąnaudų koeficientai.')
    return '<'+' '.join(k+'='+number(v) for k,v in sorted(values.items()))+'>' if values else ''


def row_record(row, parameter89):
    if row.get('row_type') == 'Other':
        raise ValueError('Pirmiausia nustatykite eilutės tipą (darbas / medžiaga).')
    if not row['conversion_valid']:
        raise ValueError('Konversija nepatvirtinta arba nebegalioja.')
    field(row['target_unit'], 10)
    ref = row.get('normative_reference')
    if ref and ref.get('kind') == 'resource':
        raise ValueError('Resurso kodas nėra vidutinių kainų pozicija. Lentelėje pasirinkite kainyno arba vartotojo kodą; resurso tiesioginio 6 tipo įrašo semantika nepatvirtinta.')
    if ref and (not ref['unit'] or normalize_unit(ref['unit']) != normalize_unit(row['target_unit'])):
        raise ValueError('Nežinomas arba nesutampantis normatyvo vienetas; patikrinkite konversiją.')
    # We export already converted target quantities. Parameter 1 may convert them again.
    if parameter89 == 1 and (normalize_unit(row['source_unit']) != normalize_unit(row['target_unit'])
            or re.match(r'^\d', normalize_unit(row['target_unit']))):
        raise ValueError('89=1: tikslinis kiekis gali būti perskaičiuotas antrą kartą. SISTELA nustatykite 89=0 ir išsaugokite nustatymą.')
    options = row.get('options', {})
    if set(options)-{'mark','ngr','parameters','coefficients','resources'}:
        raise ValueError('Neatpažinti TXT eilutės parametrai.')
    mark = options.get('mark', 'S')
    code = field(row['selected_code'],18,True)
    quantity = number(row['target_quantity'], 3 if mark=='I' else 6)
    result = ['6',code,quantity]
    if row['code_type'] == 'custom':
        if mark not in {'S','G','I'}:
            raise ValueError('Pasirinkite žymę S, G arba I.')
        # Price precision/description width are not specified in the package manual.
        # Reject unsupported text length rather than assume DBF's unrelated 240 limit.
        description = field(row['output_description'])
        if len(description)>120:
            raise ValueError('Ilgesnio kaip 120 ženklų eilutės teksto profilis dar nepatikrintas.')
        if row['price'] is None:
            raise ValueError(PRICE_REQUIRED)
        price = number(row['price'], 4, 7, positive=False)
        result += [f"<{mark},{row['target_unit']}>", 'P='+description]
        if mark == 'I':
            result += ['I='+price]
        else:
            ngr = options.get('ngr')
            if type(ngr) is not int or not 1<=ngr<=12:
                raise ValueError('Vartotojo kainai pasirinkite dokumentuotą NGR grupę (1–12).')
            result += ['R=7',price,str(ngr)]
    else:
        # Normative rows can keep the catalogue description; explicit output changes use P=.
        if row['output_description'] != ref['description']:
            description = field(row['output_description'])
            if len(description)>120:
                raise ValueError('Ilgesnio kaip 120 ženklų eilutės teksto profilis dar nepatikrintas.')
            result.append('P='+description)
        if 'P' in code.upper():
            params = options.get('parameters')
            if not isinstance(params,list) or not 1<=len(params)<=2:
                raise ValueError('Parametriniam įkainiui būtina pasirinkti G=x arba G=x,y.')
            if any(type(p) is not int or p<=0 for p in params):
                raise ValueError('Parametrinio įkainio grafos / kiekio numeris turi būti teigiamas.')
            result += ['G='+str(params[0]), *[str(p) for p in params[1:]]]
    coeff = coefficients(options.get('coefficients', {}), ['K1','K2','K3','K4'])
    if coeff:
        result += ['',coeff]
    return ','.join(result)


def resource_records(row):
    records=[]
    for item in row.get('options',{}).get('resources',[]):
        # Only the four-field existing-resource form illustrated on manual p.46.
        # Custom resource/full financial forms remain unknown and fail closed.
        if set(item)-{'flag','code','norm','verified'} or item.get('verified') is not True or item.get('flag') not in (2,3):
            raise ValueError('7 tipas leidžiamas tik kataloge susietam resursui; naujų resursų / kainų forma nepatikrinta.')
        code=field(str(item['code']),7,True)
        try:
            norm=Decimal(str(item['norm']))
        except (KeyError,InvalidOperation) as exc:
            raise ValueError('Nurodykite resurso normą.') from exc
        magnitude=number(abs(norm),6,5,positive=False)
        records.append(f"7,{item['flag']},{code},{'-' if norm<0 else ''}{magnitude}")
    return records


def validate_txt_export(model):
    errors = list(model.get('common_issues', []))
    records = []
    def attempt(context, fn):
        try:
            return fn()
        except (ValueError, KeyError, TypeError) as exc:
            error = {'context':context, 'message':str(exc)}
            if error not in errors:
                errors.append(error)
            return None
    if model.get('parameter89') not in (0,1):
        errors.append({'context':'parameter89','message':'Nurodykite tikrą SISTELA parametro 89 reikšmę (0 arba 1).'} )
    if not re.fullmatch(r'[A-Za-z0-9]{1,8}',model.get('filename','')):
        errors.append({'context':'filename','message':'Paketo failo vardas: 1–8 raidės arba skaičiai.'})
    if not re.fullmatch(r'\d{4}(0[1-9]|1[0-2])',model.get('period','')):
        errors.append({'context':'period','message':'Nurodykite skaičiavimo laikotarpį YYYYMM.'})
    for i,(name,code_limit,name_limit) in enumerate([('complex',10,120),('object',7,120),('estimate',3,60)],1):
        value=attempt(name,lambda n=name,c=code_limit,limit=name_limit:
            f"{i},{field(model[n]['code'],c,True)},{field(model[n]['name'],limit)}" + (','+model['period'] if i>1 else ''))
        if value:
            records.append(value)
    seen=set()
    if not model.get('sections'):
        errors.append({'context':'project','message':'Sąmatoje nėra eilučių.'})
    for section in model.get('sections',[]):
        def header():
            code=field(section['code'],3,True)
            if code in seen:
                raise ValueError('Skyriaus kodas dubliuojasi.')
            seen.add(code)
            coeff=coefficients(section.get('coefficients',{}),['K11','K21','K31','K41','K6'])
            return '4,'+code+','+field(section['name'],60)+(', ,'+coeff if coeff else '')
        value=attempt(section['id'],header)
        if value:
            records.append(value)
        for row in section['rows']:
            if row['code_type']=='custom' and row['price'] is None:
                errors.append({'context':row['id'],'message':PRICE_REQUIRED})
            value=attempt(row['id'],lambda r=row:row_record(r,model.get('parameter89')))
            if value:
                records.append(value)
                resources=attempt(row['id'],lambda r=row:resource_records(r))
                if resources:
                    records.extend(resources)
    return {'status':'BLOCKED' if errors else 'EXPERIMENTAL', 'production':False,
            'ready_rows':sum(r['id'] not in {e['context'] for e in errors} for s in model.get('sections',[]) for r in s['rows']),
            'total_rows':sum(len(s['rows']) for s in model.get('sections',[])),
            'errors':errors, 'records':records if not errors else [],
            'warnings':['Tik eksperimentinis perdavimas. Priėmimas tikroje SISTELA dar nepatvirtintas.',
                'cp1257 ir 120 ženklų eilutės teksto profilis turi būti patikrintas realiame teste.']}


def parse_generated_txt(data):
    """Strict reader of OUR generated subset, not a general SISTELA package parser."""
    text=data.decode('cp1257') if isinstance(data,bytes) else data
    records=[]
    types=[]
    for line in text.splitlines():
        if not line or any(ord(c)<32 for c in line):
            raise ValueError('Empty/control package record')
        tokens=[]
        start=0
        depth=0
        for i,char in enumerate(line):
            if char=='<':
                if depth:
                    raise ValueError('Nested package bracket')
                depth=1
            elif char=='>':
                if not depth:
                    raise ValueError('Unmatched package bracket')
                depth=0
            elif char==',' and not depth:
                tokens.append(line[start:i])
                start=i+1
        if depth:
            raise ValueError('Unclosed package bracket')
        tokens.append(line[start:])
        if tokens[0] not in {'1','2','3','4','6','7'} or len(tokens)<3:
            raise ValueError('Unsupported package record')
        if tokens[0]=='7' and (len(tokens)!=4 or not types or types[-1] not in {'6','7'} or tokens[1] not in {'2','3'}):
            raise ValueError('Invalid resource record')
        if tokens[0]=='1' and len(tokens)!=3 or tokens[0] in {'2','3'} and len(tokens)!=4:
            raise ValueError('Invalid hierarchy fields')
        types.append(tokens[0])
        records.append(tokens)
    if types[:3]!=['1','2','3'] or types.count('1')!=1 or types.count('2')!=1 or types.count('3')!=1 or types[3:4]!=['4']:
        raise ValueError('Package hierarchy/order invalid')
    if '6' not in types or types[-1]=='4':
        raise ValueError('Empty package section')
    return records


class SistelaPackageTxtExporter:
    def export(self, model):
        report=validate_txt_export(model)
        if report['errors']:
            raise ValueError(report)
        data=('\r\n'.join(report['records'])+'\r\n').encode('cp1257')
        parsed=parse_generated_txt(data)
        if [','.join(record) for record in parsed] != report['records']:
            raise ValueError('Package round-trip mismatch')
        rows=[r for s in model['sections'] for r in s['rows']]
        for expected,actual in zip(rows,[r for r in parsed if r[0]=='6'],strict=True):
            if actual[1]!=expected['selected_code'] or Decimal(actual[2])!=Decimal(expected['target_quantity']):
                raise ValueError('Normalized quantity/code round-trip mismatch')
        return data
