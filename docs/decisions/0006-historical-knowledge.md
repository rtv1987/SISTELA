# ADR 0006 – istorinės žinios su kilme ir žmogaus peržiūra

2026-09-29. Priimta.

Istorinės sąmatos saugomos atskirai nuo einamojo projekto ir jo patvirtintų mappingų.
Kandidato būsena laikoma HistoricalLine: viena pozicija turi vieną istorinį kodą;
papildoma vieno-su-vienu candidate lentelė dubliuotų tekstą, vienetą ir provenienciją.
HistoricalReview saugo būsenų pasikeitimus ir patvirtintą sistemą.

Patvirtinus istorinį kandidatą nedidinami SistelaMapping skaitikliai: pasiūlymų variklis
skaito patvirtintą istoriją tiesiogiai. Taip atmetimas tuoj pat pašalina istorinį
pasiūlymą, nėra sunkiai atšaukiamų dubliuotų patvirtinimų. Dabartinio projekto aiškus
patvirtinimas lieka savarankišku žmogaus sprendimu ir turi prioritetą.

Proveniencija – fizinis DBF įrašo numeris (įskaitant praleistus deleted įrašus), failo
hash, išoriniai raktai ir reikalingų sd/dd/nd įrašų originalios reikšmės. Sistemos
alias ir klasifikavimas pagal skyrių yra interpretacijos; UI tai rodo.

Importo tapatybė priklauso nuo pagrindinių sd/dd/nd baitų, ne failo kelio. Failai
apdorojami laikinose upload kopijose, nes esamas dbfread adapteris priima kelią.
Joks DBF serializeris, index/memo redaktorius ar SISTELA katalogo rašymas nekuriamas.

Vienetų suderinamumas atskirtas nuo konversijos. Sąlyginai perskaičiuojamas vienetas
dar nėra suderinamas su pasiūlymo taikymu. Konversijos endpointas yra tik skaičiuoklė.
