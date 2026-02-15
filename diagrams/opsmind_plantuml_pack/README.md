# OpsMind PlantUML Pack

Developer-focused architecture diagrams in PlantUML.

## Files
- `c4-container.puml` — C4 Container diagram (system/container level)
- `c4-component-orchestrator.puml` — C4 Component diagram (orchestrator internals)
- `sequence-500-spike.puml` — Sequence diagram for an HTTP 500 spike RCA turn
- `security-boundaries.puml` — Trust boundaries & security controls (developer view)

## Rendering (local)
### Option A: PlantUML CLI
1. Install Java + PlantUML
2. Render:
   ```bash
   plantuml -tpng c4-container.puml
   plantuml -tpng c4-component-orchestrator.puml
   plantuml -tpng sequence-500-spike.puml
   plantuml -tpng security-boundaries.puml
   ```

### Option B: VS Code
Install the PlantUML extension and export from the editor.

## C4 include dependency
C4 diagrams use `C4-PlantUML` includes via GitHub raw URLs.
For offline rendering, vendor the C4 library into your repo and change includes:
- Replace:
  `!define C4P https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master`
- With (example):
  `!define C4P ./C4-PlantUML`
