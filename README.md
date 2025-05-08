# Power BI Semantic Analyzer

Modulo Python per analisi massiva dei modelli semantici pubblicati su Power BI Service. Pensato per integrazione agentica (es. LangChain).

## Funzionalità principali
- Autenticazione MSAL (client credentials)
- Interrogazione Power BI REST API
- Connessione XMLA endpoint (DMV)
- Output JSON strutturato (Pydantic)
- Wrapper LangChain (Tool/RunnableLambda)

## Configurazione
Vedi `.env.example` per i parametri richiesti.

## Requisiti
- Python 3.9+
- Vedi `requirements.txt`

## Uso
1. Configura le variabili d'ambiente
2. Installa le dipendenze
3. Esegui il modulo o integra tramite LangChain
