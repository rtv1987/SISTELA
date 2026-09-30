"""Synthetic DBFs exclusively for catalog regressions, never production fixtures."""
import struct


def dbf(path, fields, rows):
    header=bytearray(32)
    header[0]=3
    struct.pack_into('<IHH',header,4,len(rows),33+32*len(fields),1+sum(f[2] for f in fields))
    data=header
    for name,kind,width in fields:
        descriptor=bytearray(32)
        descriptor[:len(name)]=name.encode()
        descriptor[11]=ord(kind)
        descriptor[16]=width
        data+=descriptor
    data+=b'\r'
    for row in rows:
        data+=b' '
        for name,kind,width in fields:
            value=str(row.get(name,'')).encode('cp1257')
            assert len(value)<=width
            data+=value.rjust(width,b' ') if kind=='N' else value.ljust(width,b' ')
    path.write_bytes(data+b'\x1a')


def catalog(folder):
    folder.mkdir(exist_ok=True)
    dbf(folder/'erer.dbf',[('IKAINIS','C',18),('PAVADIN','C',100),('MATO_VNT','N',3)],[
        {'IKAINIS':'TEST-1','PAVADIN':'Kabelio montavimas','MATO_VNT':1},
        {'IKAINIS':'TEST-2','PAVADIN':'Kabelio montavimas','MATO_VNT':2},
        {'IKAINIS':'TEST-3','PAVADIN':'Įrenginių montavimas','MATO_VNT':3}])
    dbf(folder/'samkainw.dbf',[('KODAS','C',10),('PAVADIN','C',100),('KODMAT','N',3),('MATOVNT','C',12)],[
        {'KODAS':'10','PAVADIN':'Viela','KODMAT':1,'MATOVNT':'m'},
        {'KODAS':'11','PAVADIN':'Viela','KODMAT':2,'MATOVNT':'100M'},
        {'KODAS':'12','PAVADIN':'Įrenginys','KODMAT':3,'MATOVNT':'vnt.'}])
    return folder
