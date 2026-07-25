# Schematic-only UI: design notes and implementation plan

Summary
- Purpose: Make `slicap-schematics` open a minimal schematic workspace: canvas-centric view with the Instruction and Log panels disabled and the `Instructions` menu item disabled.
- Scope: UI-only changes; CLI already passes a `schematic_only` boolean into the window constructor.

Design principles
- Treat `schematic_only` as a read-only startup mode flag and centralize mode-specific behavior in one place (preferably `MainWindow.__init__` or a small `SchematicWindow` subclass).
- Prefer skipping creation of optional widgets (Instruction, Log docks) rather than creating-and-hiding them. This avoids extra layout state and accidental persistence.
- Disable menu actions (`QAction.setEnabled(False)`) instead of removing menus to remain robust across GNOME/global-menu behaviors.
- Avoid applying persistent saved window state when starting in `schematic_only` mode (do not call the normal `restoreState`/`restoreGeometry` path for this mode).
- Keep CLI/startup parsing (`SLiCAP/schematic/main.py`) separate from UI mode implementation.

Files to change (recommended)
- `SLiCAP/schematic/window.py`:
  - Add a small helper `_configure_for_schematic_only(self)` called early from `MainWindow.__init__`.
  - When `schematic_only` is True:
    - Do not create Instruction and Log dock widgets, or if creation is unavoidable, call `.hide()` and mark them as non-closable / not visible.
    - Ensure the `CanvasPanel` is set as the central widget.
    - Find the `Instructions` action(s) and call `setEnabled(False)`.
    - Skip calling `restoreState(...)` / `restoreGeometry(...)` so full-GUI saved state is not applied.
  - Add guard checks where other code references the docks so they tolerate absence.

- `SLiCAP/schematic/main.py`:
  - No UI logic here; ensure the boolean `schematic_only` is passed into `MainWindow` (already present).
  - Keep `AA_DontUseNativeMenuBar` handling as-is; it is orthogonal to the above.

Testing & verification
- Add an offscreen unit test that instantiates `MainWindow(schematic_only=True)` and asserts:
  - `isinstance(window.centralWidget(), CanvasPanel)`
  - Instruction and Log docks are not present or are hidden
  - `instructions_action.isEnabled()` is False
- Run the test suite (`pytest`) and a small local UI sanity check using an offscreen Qt platform where possible.

Runtime diagnostics (optional)
- Add a short startup debug log in `main()` when `schematic_only` is True to print `argv[0]`, whether `schematic_only` was inferred, and whether the main menu and embedded menu are present. This helps debug installed-script behavior.

Alternatives and enhancements
- Subclassing: create `SchematicWindow(MainWindow)` that overrides dock/menu creation to keep the modes isolated. This is cleaner but slightly larger change.
- Window configurator: implement a tiny `WindowConfigurator` object with `apply_schematic_mode(window)` for testability.

UX & persistence notes
- Do not persist schematic-only modifications to the normal window-state settings — users starting the full GUI should see their normal saved layout.
- Use `setEnabled(False)` on menu actions to preserve predictable menu layout on desktops that use a global menu bar.

Commands to run locally
```bash
python -m pytest -q
python -m pip install --upgrade .
# then run either `slicap-schematics` or `slicap` to test installed launcher
```

Next steps
- When you are ready, I can implement the minimal change in `SLiCAP/schematic/window.py` (skip docks and disable menu action) and add the test. Or I can implement the subclass-based approach if you prefer a cleaner separation.

Date: 2026-07-07
