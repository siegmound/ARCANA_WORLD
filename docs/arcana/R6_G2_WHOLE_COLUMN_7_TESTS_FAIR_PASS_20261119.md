# R6 G2 integratore whole-column — test FAIR ricevuto 2026-11-19

Commit checkout FAIR confermato: `1d2138a46b32622988635a16f515d0e312548c5e`.

Output terminale fornito dall'operatore:
```text
python -m pytest -q tests/test_r6_g2_whole_column_provider.py
....... [100%]
7 passed in 0.11s
```

**Adjudicazione:** il nucleo `full_column.py` e i test numerici sintetici del runner 25 colonne hanno superato i sette test. Non è stata invocata una legge G2 su 25 colonne PRE reali e non è stata qualificata alcuna conversione a SHELLS. Le specifiche dei materiali, water fugacity, P efficace, adattamento di attrito e coefficienti LR rimangono non autorizzati; solve meccanico 0, T1 nullo.

Questa evidenza è l'output del terminale riportato dall'operatore: NON è stata eseguita un'ispezione diretta di artefatti FAIR. Il pass autorizza a lavorare sulla traduzione dei parametri, non a eseguire una deformazione.
