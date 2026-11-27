# Baixa visió en xarxa — web del projecte

Web trilingüe (català, castellà, anglès) del projecte **Baixa visió en xarxa** (CUV · FOOT · UPC), basada en la memòria presentada a la convocatòria IMPACTE 2025 de l'AGAUR.

## Com veure-la

La carpeta `dist/` conté la web ja generada. És HTML estàtic: no necessita servidor ni base de dades.

- Obrir directament: `dist/index.html` al navegador.
- O amb un servidor local: `python3 -m http.server -d dist 8000` i anar a <http://localhost:8000>.

Per publicar-la, només cal copiar el contingut de `dist/` a qualsevol allotjament estàtic (servidor de la UPC, GitHub Pages, Netlify…).

## Com regenerar-la

Cal Python 3.8 o superior, sense cap dependència addicional:

```bash
python3 build.py
# Amb el domini definitiu (URL canòniques, hreflang absoluts, sitemap.xml i codis QR que apunten al domini):
BASE_URL=https://domini-definitiu.cat python3 build.py
# Entorn de proves per a la validació participativa (REQ-12): avís visible, noindex i robots.txt que bloqueja cercadors
STAGING=1 BASE_URL=https://proves.domini.cat python3 build.py
# Opcional: on s'envia el formulari de validació (POST) o correu alternatiu
FEEDBACK_ENDPOINT=https://... FEEDBACK_EMAIL=adreca@upc.edu python3 build.py
```

El script comprova automàticament: enllaços interns i ancoratges, identificadors duplicats, imatges sense `alt`, jerarquia d'encapçalaments dins de `<main>` (un sol h1, sense salts, fins a h3) i que cap `<video>` es publiqui sense subtítols ni transcripció. També genera l'índex de l'assistent de recursos (`dist/assets/js/index-<idioma>.js`).

## On és cada cosa

| Fitxer | Què conté |
| --- | --- |
| `src/pages/ca/*.html` | Contingut de cada pàgina en català (llengua font). Igual per a `es/` i `en/`. |
| `src/data/team.json` | Fitxes de l'equip (noms, rols, biografies i enllaços en els tres idiomes). |
| `src/data/glossary.json` | Termes del glossari en els tres idiomes (s'ordenen sols). |
| `src/data/resources.json` | Fitxes del generador de recursos per a la consulta (PDF + QR). L'`id` curt viatja a l'URL del QR. |
| `src/data/assistant.json` | Regles de l'assistent: perfils, necessitats, paraules clau, sinònims, rutes per defecte i totes les frases de resposta. |
| `src/data/simulator.json` | Modes del simulador de visió i la seva descripció escrita a mà (text alternatiu). |
| `src/data/testimonials.json` | Repositori de testimonis en vídeo (buit fins que hi hagi vídeos amb consentiment). |
| `src/i18n.json` | Textos de la interfície (menú, panell d'accessibilitat, peu) i noms de fitxer per idioma. |
| `src/templates/layout.html` | Plantilla comuna: capçalera, panell d'accessibilitat, menú i peu. |
| `src/assets/css/site.css` | Estils i temes de color (tots els textos amb contrast ≥ 7:1). |
| `src/assets/js/a11y.js` | Barra i panell d'accessibilitat: mida del text, temes, interlineat i espaiat, guia de lectura, lectura en veu alta. |
| `src/assets/js/assistant.js` | Assistent de recursos (cercador tancat sobre els continguts validats, entrada per text o veu). |
| `src/assets/js/features.js` | Guies en àudio, simulador, filtres de testimonis, generador PDF/QR, paquet del pacient i formulari de validació. |
| `src/assets/js/vendor/qrcode.js` | Generador de codis QR de Kazuhiko Arase (llicència MIT), v1.4.4. |
| `src/assets/fonts/` | Tipografia Atkinson Hyperlegible allotjada localment (llicència SIL OFL). |
| `src/assets/img/team/` | Fotografies de l'equip (320×320, sense metadades). S'assignen amb el camp `photo` de `team.json`. |
| `src/assets/img/logos/` | Logotips oficials: UPC (SVG del web de la UPC), Generalitat i AGAUR (portal d'identitat corporativa de la Generalitat), B1+B2+B3 (web de l'associació), Fundació Punt de Vista (capçalera de pdvista.org, 118×90 px: és l'única versió publicada) i COOOC (PNG oficial de coooc.cat, reduït a 600 px). |

Cada pàgina comença amb un bloc `<!-- meta {"title": ..., "description": ...} -->`. Dins del contingut es poden fer servir marcadors com `{{href:patients}}` (enllaç a una pàgina en el mateix idioma) o `{{icon:eye}}` (icona). La llista completa és a la capçalera de `build.py`.

## Estructura del lloc

Reorganitzada segons el *Documento Maestro V2* (sessions de cocreació del 19 i 20 de novembre de 2026): tres grans àrees, cadascuna amb subseccions accessibles des de la portada amb un o dos clics, i accessos transversals a la capçalera (Assistent de recursos, Qui som).

| Pàgina | clau a `i18n.json` | ca |
| --- | --- | --- |
| Inici (barra d'accessibilitat + assistent + lector) | `home` | `index.html` |
| 1. Pacients | `patients` | `pacients.html` |
| 1.1 Acabo de rebre el diagnòstic | `pat_diagnosis` | `pacients-diagnostic.html` |
| 1.2 Entendre la meva patologia | `pat_conditions` | `pacients-patologies.html` |
| 1.3 Ajudes òptiques, tecnologia i apps | `pat_aids` | `pacients-ajudes-tecnologia.html` |
| 1.4 Experiències reals i ajuda mútua | `pat_stories` | `pacients-experiencies.html` |
| 1.5 On anar i suport psicològic | `pat_support` | `pacients-on-acudir.html` |
| 2. Familiars i interessats | `families` | `familiars.html` |
| 2.1 Comprendre la baixa visió (simulador) | `fam_understand` | `familiars-comprendre.html` |
| 2.2 Com acompanyar i guiar amb seguretat | `fam_guide` | `familiars-acompanyar.html` |
| 2.3 Adaptar la casa i la il·luminació | `fam_home` | `familiars-casa-il-luminacio.html` |
| 2.4 Escoles, instituts i societat | `fam_society` | `familiars-escoles-societat.html` |
| 3. Professionals | `professionals` | `professionals.html` |
| 3.1 Mapa de derivació clínica i social | `pro_referral` | `professionals-derivacio.html` |
| 3.2 Generador de recursos per a la consulta | `pro_generator` | `professionals-generador-recursos.html` |
| 3.3 Formació i especialització | `pro_training` | `professionals-formacio.html` |
| Paquet de recursos (el que obre el QR) | `pack` | `paquet-recursos.html` |
| Assistent de recursos | `assistant` | `assistent.html` |
| Qui som · El projecte · Equip · Participa en la validació | `about` · `project` · `team` · `validation` | `qui-som.html` · `projecte.html` · `equip.html` · `validacio.html` |
| Glossari · Accessibilitat | `glossary` · `accessibility` | `glossari.html` · `accessibilitat.html` |

Els noms de fitxer en castellà i anglès són a `src/i18n.json`. Els identificadors dels ancoratges (`#primers-passos`, `#mites`…) són els mateixos en els tres idiomes perquè les fitxes del generador i l'assistent hi puguin enllaçar.

## Correspondència amb l'informe (REQ-01 a REQ-12)

| Requisit | Implementació |
| --- | --- |
| REQ-01 Accessibilitat core | Regions semàntiques, h1-h3 seqüencials comprovats en cada compilació, botó **Escolta la pàgina** sempre visible (lector integrat), compatibilitat amb lectors de pantalla i línia braille. |
| REQ-02 Barra visual | Barra persistent (fixa a dalt quan no tapa massa pantalla): text fins al 300 % amb icones en `em` que no es deformen, contrast clar/fosc d'un clic; panell amb 7 esquemes (inclòs negre sobre groc), interlineat i espaiat en 3 nivells; regles `forced-colors` perquè cap icona ni indicador desaparegui amb l'alt contrast del sistema. |
| REQ-03 Multimèdia | `alt` obligatori (comprovat), descripcions del simulador escrites a mà, cap vídeo sense subtítols i transcripció (comprovat), audiodescripció prevista a `testimonials.json`. |
| REQ-04 Assistent | `assistant.js`: arbre de decisions de l'informe (perfil → necessitat → màx. 3 enllaços verificats), entrada per text o veu, corpus tancat generat a partir de les pàgines publicades. No fa servir cap model generatiu; vegeu «Pendent». |
| REQ-05 Diagnòstic | Pàgina 1.1: explicació planera, glossari bàsic, mites i realitats, què es pot fer i què no. |
| REQ-06 Recursos | Pàgines 1.2 (per malaltia, incloses minoritàries, i per tipus de pèrdua) i 1.3 (ajudes, filtres, apps IA, avenços). |
| REQ-07 Suport | Pàgines 1.4 (repositori de testimonis filtrable, grups d'ajuda mútua) i 1.5 (directori i psicologia). |
| REQ-08 Familiars | Pàgines 2.1 (simulador i diferències amb altres discapacitats), 2.2 (guies en text i àudio), 2.3 (glossari de consells). |
| REQ-09 Societat | Pàgina 2.4 (escoles, «Inclusió a la diversitat», bastó blanc). |
| REQ-10 Derivació | Pàgina 3.1 (mapa per a oftalmologia, CAP, optometria i treball social; comunicació del diagnòstic; urgències). |
| REQ-11 Caselles | Pàgina 3.2: caselles → PDF accessible unificat (impressió del navegador) + codi QR al paquet del pacient. Sense servidor ni dades personals. |
| REQ-12 Validació | `STAGING=1`, pàgina «Participa en la validació» amb formulari accessible (opcionalment enviat a `FEEDBACK_ENDPOINT`). |

## Accessibilitat

- Objectiu WCAG 2.2 AA, i AAA en contrast (≥ 7:1 en tots els temes).
- Barra d'accessibilitat a totes les pàgines (text A−/A+, contrast clar/fosc, Escolta la pàgina, Més opcions) i panell complet: text fins al 300 %, temes automàtic, clar, negre sobre blanc, negre sobre groc, fosc, blanc sobre negre i groc sobre negre; interlineat i espaiat entre lletres i paraules en tres nivells (el primer compleix WCAG 1.4.12); enllaços destacats, guia de lectura, cursor gran, escala de grisos, aturar animacions i lectura en veu alta (Web Speech API).
- Compatible amb els modes d'alt contrast de Windows/macOS (`forced-colors`): punts, números, barres, botons premuts, logotips i codis QR es mantenen visibles.
- Cada canvi s'anuncia als lectors de pantalla i també amb un avís visual. Navegació completa amb teclat, enllaç per saltar al contingut, focus molt visible.
- Les preferències només es desen al navegador de cada persona (localStorage); no hi ha galetes ni analítica de tercers. Amb `file://` viatgen als enllaços interns amb el paràmetre `?bvx=`.

## Pendent de revisar abans de publicar

1. **Validació dels continguts** nous (àrees, fitxes del generador, mapa de derivació, glossari) per l'equip clínic i el Servei de Llengües i Terminologia. Les pàgines ho indiquen amb una nota.
2. **Assistent amb IA (REQ-04):** la versió actual és un motor de recuperació tancat i determinista (sense model generatiu, per tant sense al·lucinacions) que ja segueix l'arbre de decisions. Per afegir-hi un model de llenguatge (RAG) caldrà un servidor; el corpus validat ja es genera a `dist/assets/js/index-<idioma>.js`, i totes les respostes actuals són a `src/data/assistant.json`.
3. **Testimonis i vídeos de simulació:** cal enregistrar-los amb consentiment informat, amb subtítols (WebVTT), audiodescripció i transcripció, i afegir-los a `src/data/testimonials.json` (fitxers a `src/assets/media/`).
4. **Directori validat de professionals** (optometristes, rehabilitadors, psicòlegs): l'informe el demana, però no s'hi ha posat cap nom fins que l'equip el validi.
5. **Cites anònimes** de la pàgina 1.4: són idees de les sessions resumides amb paraules nostres. Cal confirmar amb l'IP que es poden publicar així.
6. **COOOC:** s'ha afegit com a entitat col·laboradora amb el seu logotip oficial (l'informe el cita com a «Col·laboració COOOC» i seu de les sessions). Cal confirmar-ho i demanar permís d'ús del logotip.
7. **Formulari de validació:** sense `FEEDBACK_ENDPOINT` mostra un resum per copiar i enviar al CUV. Cal decidir on es recullen les respostes (servidor de la UPC, formulari institucional…) i, si s'hi desen dades, revisar-ho amb protecció de dades.
8. **Directori d'apps** (pàgina 1.3): orientatiu, revisat al novembre de 2026; cal revisar-lo periòdicament.
9. **Logotip de la Fundació Punt de Vista:** només hi ha una versió petita (118×90 px) a pdvista.org; cal demanar-los una versió vectorial o d'alta resolució i permís d'ús.
10. **Fotografies de l'equip, logotips de l'AGAUR/Generalitat, CUV/FOOT i contacte:** continuen pendents com a la versió anterior.
