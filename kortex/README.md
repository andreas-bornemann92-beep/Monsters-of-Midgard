# KORTEX – Engine-Integration V1.5.5 (KX-120)

## Verifizierter Stand (22.11.2026)

Die Python-Kampfengine wurde lokal aus `MIDGARD_KORTEX_GITHUB_INTEGRATION_V1_5_5.zip` extrahiert und überprüft:
- 203 von 203 Kampftests bestanden
- 5 von 5 Wertetests bestanden
- Master-Smoke-Test: `MASTER_IMPORT_OK`, `BATTLE_TURN_OK`, `SNAPSHOT_JSON_OK`
- ZIP-Integrität: `testzip() == None`

**GitHub-CI ist noch NICHT erfolgreich:** Im Branch fehlen weiterhin die Engine-Dateien. Workflow Run 45081908236 scheiterte am Test `Check engine availability`, bevor Python-Regressionstests ausgeführt werden konnten.

## Fehlende Dateien aus dem geprüften Archiv hochladen

Aus `MIDGARD_KORTEX_GITHUB_INTEGRATION_V1_5_5.zip` unter Beibehaltung der relativen Ordnerstruktur übernehmen:

- `kortex/engine/` (Python-Code und Tests; `__pycache__` und `*.pyc` auslassen)
- `kortex/05_KORTEX/` (JSON-Regelprofile; zwingend erforderlich)

Die übrigen Demo-Ordner, `main`, `index.html` und das Monsterlexikon nicht verändern.

## Reproduzierbare Prüfkommandos

Im Repository-Stammverzeichnis:

```bash
test -f kortex/engine/kortex_battle/master.py
test -f kortex/05_KORTEX/TYPENPROFIL_V0_6.json
cd kortex/engine
python -m unittest discover -s tests -v
python -m unittest -v test_stat_reference
python smoke_test_master.py
```

Das GitHub-Workflowfile `.github/workflows/kortex-tests.yml` ist bereits auf diesem Branch. Ein grüner GitHub-Actions-Lauf gilt erst nach dem vollständigen Upload und tatsächlicher CI-Ausführung als bestätigt.

## Projekttrennung

Dieser Branch dient ausschließlich der technischen Engine- und Testschnittstelle. Die grafische Demo wird im separaten Chat entwickelt. Monsterlexikon: unverändert, keine übernommenen Monster oder neue Kanonfreigaben.
