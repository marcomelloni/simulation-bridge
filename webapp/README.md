# Simulation Bridge Webapp

Interfaccia web moderna sviluppata con React + TypeScript per rendere Simulation Bridge accessibile e semplice da usare. La webapp fornisce dashboard, gestione configurazioni, progetti, automazioni, collaborazione e monitoraggio streaming.

## Requisiti
- Node.js >= 18
- npm o yarn

## Installazione e avvio
```bash
npm install
npm run dev
```
La console di sviluppo sarà disponibile su [http://localhost:5173](http://localhost:5173).

## Build di produzione
```bash
npm run build
```
I file ottimizzati saranno generati nella cartella `dist/`.

## Struttura principale
- `src/App.tsx`: definisce il routing principale della console.
- `src/components/Layout.tsx`: layout con navigazione laterale e top bar.
- `src/pages/`: raccolta delle pagine (Dashboard, Configurazioni, Progetti, Automazioni, Collaborazione, Streaming).

## Linting
```bash
npm run lint
```
Esegue ESLint sulle sorgenti TypeScript/React.
