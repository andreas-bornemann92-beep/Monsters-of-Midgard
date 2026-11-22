# KORTEX – Integrationsbranch
Version: Engine V1.5.5, KX-120

Der Branch ist für die getrennte Übernahme der Python-Kampfengine und deren automatisierte Tests bestimmt. Der komplette getestete Engine-Quellbestand liegt vorerst im separat erzeugten Übergabearchiv MIDGARD_KORTEX_GITHUB_INTEGRATION_V1_5_5.zip.

Vor einem Testlauf müssen die Ordner `kortex/engine/` und `kortex/05_KORTEX/` aus dem Übergabepaket übernommen werden. Der Workflow prüft die Engine ausdrücklich und darf bei fehlendem Code nicht als erfolgreicher Engine-Test gelten.

Die Demo wird in einem separaten Chat entwickelt; `main`, `demos/`, `kampfoberflaeche/`, `monster-taimer/` und `index.html` bleiben unverändert.

Kanon: kein Monsterimport. Python-Engine: Referenzprototyp, keine vollständige Cartridge-Kompatibilität.
