
GeoFEA — RS2-style UI (patched interactive drawing)

• RS2-like layout: ribbon tabs, Model Items + Display Options, SNAP/GRID/ORTHO/OSNAP.
• Interactive geometry drawing (Polygon/Rectangle/Circle) with grid snap & orthogonal mode.
• Heads-up length/angle HUD; right-click/Enter to finish polygon; Esc to cancel.
• Triangle mesher (with structured fallback), linear elastic solver (imperial units).
• GitHub Actions workflow builds a onefile .exe (no local Python required).

Build:
1) Upload this folder to a GitHub repo (keep .github/workflows).
2) Actions → run “Build GeoFEA (RS2 UI Patched) EXE”.
3) Download artifact GeoFEA-RS2.exe.
