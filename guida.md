1. Struttura e organizzazione
Struttura dei capitoli (pattern dominante)

Quasi tutte le tesi seguono questa macro-struttura:

Introduction

Background / State of the Art

Technologies / Theoretical Foundations

Architecture / Design

Implementation

Evaluation / Results

Conclusions and Future Work

Bibliography

Capitoli preliminari standard:

Abstract / Summary

Acknowledgements

List of Figures / Tables

Glossary / Acronyms (molto frequente)

Lunghezza approssimativa (tesi magistrale)
Sezione	% del totale	Pagine tipiche
Introduction	5–8%	5–8
Background / State of the Art	20–25%	15–25
Technologies / Theory	15–20%	15–20
Architecture & Design	15–20%	15–20
Implementation	15–20%	15–20
Evaluation / Results	10–15%	10–15
Conclusions	3–5%	3–5
Totale	100%	70–100

👉 Le tesi più recenti (2024–2025) tendono a 80–90 pagine.

Ordine e gerarchia

Capitoli molto strutturati (2–4 livelli di sottosezioni)

Ogni capitolo ha introduzione implicita e chiusura logica

Nessun capitolo “ibrido”: teoria ≠ implementazione ≠ risultati

2. Approccio metodologico
Metodologie più utilizzate

Il pattern è chiarissimo:

Applied research + design science

Schema tipico:

Analisi del problema reale

Studio dello stato dell’arte

Proposta di un’architettura / framework

Implementazione (prototype / PoC)

Valutazione (qualitativa o quantitativa)

Non è quasi mai:

Ricerca puramente teorica

Studio statistico

Survey empirico su utenti

Framework teorico

Inserito prima della proposta

Non è un capitolo astratto: è sempre collegato a tecnologie reali

Spesso coincide con:

“Background”

“Technologies”

“State of the art”

Raccolta e analisi dei dati

Benchmark

Performance evaluation

Comparative analysis

Case study reale (azienda / laboratorio / progetto EU)

Metriche comuni:

Latency

Throughput

Resource usage

Scalability

Qualitative trade-offs

3. Stile e formato
Tono accademico

Formale ma pragmatico

No retorica

No frasi “letterarie”

Linguaggio tecnico preciso

Prima o terza persona?

Pattern netto:

✔ Prima persona plurale (“we”)
✘ “I” quasi mai
✘ Terza persona impersonale rara

Esempio tipico:

In this thesis, we propose and evaluate…

Struttura dei paragrafi

Paragrafi brevi e focalizzati (5–8 righe)

Ogni paragrafo = un’idea

Uso frequente di:

Liste

Figure commentate

Tabelle di confronto

Citazioni

Frequenza alta nelle parti di background

Bassa in implementation

Standard IEEE-like (numerico)

Citazioni sempre contestualizzate, mai “a pioggia”

4. Elementi specifici chiave
Introduzione (pattern ricorrente)

Struttura tipica (quasi identica in tutte):

Contesto tecnologico

Problema concreto

Gap nello stato dell’arte

Obiettivo della tesi

Contributi principali

Struttura del documento

👉 Se manca uno di questi punti, l’introduzione risulta “debole”.

Revisione della letteratura

Integrata, non separata

Confronti espliciti

Tabelle comparative frequenti

Focus su limiti delle soluzioni esistenti

Risultati / casi di studio

Grafici sempre commentati

Mai solo “raw data”

Confronto con baseline

Discussione dei trade-off (non solo numeri)

Conclusioni

Struttura molto stabile:

Riassunto dei contributi

Limiti del lavoro

Implicazioni pratiche

Future work (quasi obbligatorio)

5. Aspetti formali
Lunghezza totale

Range osservato: 50 – 100 pagine

Target “sicuro”: 80–90

Tabelle, grafici, immagini

Moltissime figure architetturali

Tabelle di confronto molto apprezzate

Ogni figura è:

Numerata

Citata nel testo

Spiegata

Bibliografia

40–80 riferimenti

Mix di:

Paper accademici

RFC / standard

Documentazione ufficiale

Fonti industriali accettate (se autorevoli)

6. Consigli pratici (golden rules)
Errori comuni da evitare

❌ Capitoli troppo sbilanciati
❌ Introduzione vaga
❌ Implementazione senza design rationale
❌ Risultati non interpretati
❌ Conclusioni che ripetono l’abstract

Best practices evidenti

✅ Architettura spiegata prima del codice
✅ Figure come primo cittadino
✅ Obiettivi chiari e misurabili
✅ Collegamento continuo tra problema → soluzione → risultati

Come differenziare la tua tesi (senza uscire dagli standard)

Esplicita meglio i trade-off

Inserisci una Design Decisions section

Evidenzia ciò che non ha funzionato

Collega il lavoro a scenari futuri reali