# ADR 0004: integracijos galimybės pagal įrodymus

Galimybės apibrėžtos tipizuotu nekintamu modeliu: status, production,
writes_to_sistela, evidence, limitation. API klientas gauna šį modelį, bet negali
įjungti blokuoto adapterio. Manual Entry ir darbo XLSX neskelbiami tiesioginiu
SISTELA importu. Package Text turi tik leksinę analizę, nes nėra tikro pavyzdžio.
Eksperimentalūs writer adapteriai lieka už gamybinių maršrutų ribų ir fail closed.
