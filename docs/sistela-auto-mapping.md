# Automatic code selection and corrections

PDF/XLSX import and project opening fill blank work/material codes using local
knowledge. Existing nonempty codes and explicitly cleared user choices remain
untouched. No network, LLM or external AI is involved.

Compatible units rank ahead of incompatible ones. Within compatibility tiers:
user exact/normalized choices, other relevant user choices, confirmed historical
evidence, other historical evidence, strong catalog matches and fuzzy catalog
matches. History is constrained by the project system; catalog group prefixes
previously used in that system provide an additional relevance signal. A catalog
match verifies existence and supplies the original description and target unit.
Text confidence is an informational score, not a probability or acceptance gate.

Selections retain their evidence. Low-confidence selections are warnings. A
different normative unit blocks handoff until a supported conversion is explicitly
reviewed; the application never silently converts m to 100M. Changing the source
quantity invalidates any confirmed conversion.

Grid and direct-line code edits, catalog selections and the single "Pasirinkti
kodą" action learn reusable choices. Source text/system, source and normative
units, prior code/candidate, time and project/line context remain available in the
review record and mapping events. Latest compatible user choices outrank generic
catalog matches. Work and material knowledge are partitioned by row type.

Legacy unmapped/suggested/confirmed states and confirmation endpoints remain for
old data and compatibility. They no longer block READY or Entry Mode merely for
lacking CONFIRMED. The UI offers an editable code and save action; no Apply+Confirm
sequence is required. Required code, quantity, unit and conversion checks remain.
Exporters additionally validate their own format and hierarchy requirements.

Undo restores the project row, but does not erase reusable user knowledge. A user
can make a new correction to supersede an earlier choice. Historical renamed text
does not become a normative original unless the active catalog verifies the code.
