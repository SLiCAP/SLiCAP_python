"""Instruction-file boilerplate (see SLNG.md, "Instruction-file architecture").

Two files run a GUI project:

- ``main.py``  — GUI-managed. Sets up the project and runs the instruction file::

      import SLiCAP as sl
      sl.initProject("<project name>")
      import <instr_stem>          # executes the instruction file

- ``<instr_stem>.py`` — GUI-edited. The analysis content::

      import SLiCAP as sl
      cir = sl.makeCircuit("sch/design.slicap_sch")   # SLiCAP schematics only
      LAPLACE1 = sl.doLaplace(cir, ...)
      ...

``initProject`` lives ONLY in ``main.py`` so the instruction file stays
import-safe (importing it from another project must not reset the parent's
HTML/labels state). These helpers are pure text/​file operations — no Qt.
"""
import ast
import re
from pathlib import Path

_IMPORT_LINE = "import SLiCAP as sl"


def parse_calls(text: str) -> list[dict]:
    """Inventory of the ``sl.*`` calls defined in instruction-file *text*.

    Returns an ordered list of dicts::

        {"name": …, "func": …, "assigned": bool,
         "args": [src, …], "kwargs": {kw: src, …}}

    - Assignments ``NAME = sl.<func>(…)`` are keyed by the target name and
      get ``assigned=True`` (their value is reachable as a variable — the
      plot wizard's "from other plots" mode needs this).
    - The list is in file order. Only the LAST assignment of each name is
      kept — instructions execute top-to-bottom, so the last one wins at
      runtime. This is what makes
      the append-only edit model work (SLNG.md): dialogs prefill from the
      parsed last definition and append the regenerated call.
    - Bare calls ``sl.<func>("fileName", …)`` are listed as they are, in
      file order, keyed by their first-argument string literal and with
      ``assigned=False``. Merging bare calls by that literal was the
      previous form and was REMOVED (2026-11-09): it dated from the plot
      era (``sl.plot("FIG", …)``, last one wins) and had no reader left,
      while the netlist line ``sl.makeCircuit("sch/x.spice_sch")`` and the
      image line ``sl.updateImages("sch/x.spice_sch")`` of one schematic
      merged into one entry, so the NGspice instruction dialog reported a
      netlist line that was in the file as missing.

    Unparseable text (the user is mid-edit) yields ``[]``.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    def _sl_call(node):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "sl"):
            return node
        return None

    out: list[dict] = []
    for stmt in tree.body:
        name = call = None
        assigned = False
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)):
            call = _sl_call(stmt.value)
            name = stmt.targets[0].id
            assigned = call is not None
        elif isinstance(stmt, ast.Expr):
            call = _sl_call(stmt.value)
            if (call is not None and call.args
                    and isinstance(call.args[0], ast.Constant)
                    and isinstance(call.args[0].value, str)):
                name = call.args[0].value
        if call is None or name is None:
            continue
        entry = {
            "name":     name,
            "func":     call.func.attr,
            "assigned": assigned,
            "args":     [ast.get_source_segment(text, a) for a in call.args],
            "kwargs":   {kw.arg: ast.get_source_segment(text, kw.value)
                         for kw in call.keywords if kw.arg},
        }
        if assigned:
            out = [e for e in out if not (e["assigned"] and e["name"] == name)]
        out.append(entry)
    return out


def literal(src, default=None):
    """The literal value of an argument's source text, as parse_calls
    returns it ('"1n"' -> '1n', '50' -> 50); *default* for None, an empty
    text or an expression. ONE helper for the dialogs that prefill from a
    parsed call: the NGspice and Traces dialogs each had their own copy
    (``_lit``) until 2026-11-21."""
    if not src:
        return default
    try:
        return ast.literal_eval(src)
    except (ValueError, SyntaxError):
        return default


def quoted(text) -> str:
    """The Python string literal of *text*, written as a user writes it by
    hand: the inverse of literal(), so ``literal(quoted(s)) == s`` for
    every str without both kinds of quote.

    The writer for the texts that the GUI puts into generated Python as
    string literals: instruction files, main.py and run scripts. The quotes
    follow Anton's rule (2026-11-22):

    - double quotes outside, ``"Gain 'open loop'"``;
    - single quotes outside when the text holds a double quote and no
      single quote, ``'Gain "open loop"'``;
    - a text with both kinds keeps double quotes outside, and each inner
      double quote becomes a single quote. Only then does the text change.

    A quote never gets a backslash. Escaping it (``\\"``) was considered
    and REJECTED 2026-11-22: nobody writes it so by hand. A backslash is
    always doubled, so ``$\\tau$`` reaches LaTeX as typed. A printable
    character is kept as typed, also a non-ASCII one such as a mu or an
    Omega: the files are UTF-8. Every other character is written as an
    escape: a line break, a tab, U+2028, a no-break space. A value that is
    not a str is written as str(text).

    Two kinds of writers do not use it. The SLiCAP analysis dialog writes
    its keyword values single-quoted, by hand (``source='V1'``), in the
    style of the manual (open for 6.5.0). Code that writes a literal with
    repr() is correct as it is: repr() always gives a valid literal.

    Six dialogs had a quoting helper of their own until 2026-11-22. Three
    of them wrote a backslash as it was, so ``$\\tau$`` read back as a TAB
    and "au". They also wrote a double quote as a single quote. None of the
    six escaped a line break. REPLACED 2026-11-22: a text now reads back as
    typed.
    """
    text = str(text)
    outer = "'" if '"' in text and "'" not in text else '"'
    if outer == '"':
        text = text.replace('"', "'")
    out = []
    for char in text:
        if char == "\\":
            out.append("\\\\")
        elif char.isprintable():
            out.append(char)
        else:
            out.append(char.encode("unicode_escape").decode("ascii"))
    return outer + "".join(out) + outer


def _char_offset(text: str, line: int, col: int) -> int:
    """The character position in *text* of an ast location: 1-based *line*
    and *col* in UTF-8 bytes, as ast reports them. Lines end at "\n" only,
    as for the Python tokenizer."""
    start = 0
    for _ in range(line - 1):
        start = text.index("\n", start) + 1
    end = text.find("\n", start)
    end = len(text) if end < 0 else end
    head = text[start:end].encode("utf-8")[:col].decode("utf-8", errors="ignore")
    return start + len(head)


_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
           ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _bound_in(stmt) -> set:
    """The names a top-level statement binds at module level, anywhere in
    it: every assignment form (plain, annotated, augmented, tuple targets,
    walrus), loop and with targets, imports, and the names of a def or a
    class, also inside a nested if/for/with/try block. The bodies of
    functions, classes, lambdas and comprehensions are their own scopes."""
    names = set()
    todo = [stmt]
    while todo:
        node = todo.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            continue
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            # a comprehension is its own scope, but a walrus in it binds
            # at module level
            names |= {n.target.id for n in ast.walk(node)
                      if isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name)}
            continue
        if isinstance(node, _SCOPES):
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names |= {a.asname or a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
        todo.extend(ast.iter_child_nodes(node))
    return names


def bound_names(text: str) -> set:
    """Every name the instruction file binds at module level, nested blocks,
    imports and defs included ("sl" too); empty when it does not parse. A
    dialog proposing a new name must avoid all of them (2026-11-21).

    ONE notion of "name taken" (2026-11-22). The Traces, Axes and Figure
    dialogs, Create circuit object and the system dialogs use it.
    assigned_names() counted the top-level ``x = ...`` targets only. It
    missed an import, a tuple or annotated target, a loop and a nested
    block. REMOVED 2026-11-22. The dialogs counted the sl.* call names
    only. REPLACED 2026-11-22."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    names = set()
    for stmt in tree.body:
        names |= _bound_in(stmt)
    return names


def _last_assignment(tree, name):
    """The last top-level statement of *tree* that binds *name* in any way
    (_bound_in): the one that decides its value at runtime, or None."""
    found = None
    for stmt in tree.body:
        if name in _bound_in(stmt):
            found = stmt
    return found


def definition_of(text: str, name: str):
    """The call that defines *name* at runtime, as a parse_calls entry with
    a ``"dump"`` of the call (to see a hand edit later), when the LAST
    top-level assignment of *name*, of any kind, is a plain
    ``name = sl.<func>(...)`` with one target and no starred arguments;
    None otherwise (a later ``name = None``, ``name = other = sl.f()``,
    ``*args``/``**kwargs``, or text that does not parse).

    ONE notion of "the definition" for what the system run dialog lists,
    what it checks at OK and what statement_range replaces: the first
    version listed by parse_calls and replaced the last assignment of any
    kind, so a later ``R1 = None`` was overwritten and the run stayed
    twice (a review, 2026-11-21)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    stmt = _last_assignment(tree, name)
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == name):
        return None
    call = stmt.value
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name) and call.func.value.id == "sl"):
        return None
    if (any(isinstance(a, ast.Starred) for a in call.args)
            or any(kw.arg is None for kw in call.keywords)):
        return None
    return {"name": name, "func": call.func.attr, "assigned": True,
            "args": [ast.get_source_segment(text, a) for a in call.args],
            "kwargs": {kw.arg: ast.get_source_segment(text, kw.value)
                       for kw in call.keywords},
            "dump": ast.dump(call)}


def statement_range(text: str, name: str):
    """The character range ``(start, end)`` in *text* of the LAST top-level
    statement that assigns *name*: the definition that wins at runtime, the
    one parse_calls keeps. Exact to the column, so a comment or another
    statement on the same line stays. None when there is none or the text
    does not parse (the user is mid-edit).

    The system run dialog replaces a run there (2026-11-21). Whole lines
    (``statement_span``) were the first form and were REPLACED the same
    day: they took a trailing comment and a second statement on the line
    with them."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    stmt = _last_assignment(tree, name)
    if stmt is None:
        return None
    return (_char_offset(text, stmt.lineno, stmt.col_offset),
            _char_offset(text, stmt.end_lineno, stmt.end_col_offset))


def assigned_before(text: str, name: str, position: int) -> bool:
    """Whether a top-level statement that starts before character
    *position* assigns *name*: a run that reads SPECS_x must come after the
    line that defines it."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for stmt in tree.body:
        if (name in _bound_in(stmt)
                and _char_offset(text, stmt.lineno, stmt.col_offset) < position):
            return True
    return False


# ── editing in place (Anton, 2026-11-22 and 2026-11-25) ─────────────────────
#
# "Editing an existing object means editing the existing one and keeping it
# on the line where it was." ONE function decides where the statements of a
# dialog go, for every dialog (TODO.md "Edit in place, in every dialog").
# The append-only editing of 2026-07-08 (SLNG.md) is REPLACED by it.

class Placement:
    """Where the statements of a dialog go in the instruction file
    (:func:`place`).

    ``append``: new statements only, appended at the end of the file.
    ``edits``: ``(start, end, text)`` replacements in the file, ascending
    and not overlapping. ``problems``: why the statements cannot go in;
    OK stays disabled and the first one is shown."""

    def __init__(self, append="", edits=(), problems=()):
        self.append = append
        self.edits = list(edits)
        self.problems = list(problems)


def _loads(stmt) -> set:
    """The names a top-level statement reads when it runs. The bodies of
    functions, classes and lambdas run later and are skipped. A
    comprehension runs at once: its own loop variables are not names of
    the file."""
    names = set()
    todo = [stmt]
    while todo:
        node = todo.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                             ast.GeneratorExp)):
            local = {n.id for g in node.generators for n in ast.walk(g.target)
                     if isinstance(n, ast.Name)}
            names |= {n.id for n in ast.walk(node)
                      if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                      and n.id not in local}
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            names.add(node.id)
        todo.extend(ast.iter_child_nodes(node))
    return names


def _early_uses(tree) -> list:
    """``(statement, name, definition)`` for every top-level statement that
    reads a name the file binds only in a LATER statement: a NameError when
    the file runs."""
    first = {}
    for stmt in tree.body:
        for name in _bound_in(stmt):
            first.setdefault(name, stmt)
    index = {id(stmt): i for i, stmt in enumerate(tree.body)}
    out = []
    for i, stmt in enumerate(tree.body):
        for name in sorted(_loads(stmt)):
            definition = first.get(name)
            if definition is not None and index[id(definition)] > i:
                out.append((stmt, name, definition))
    return out


def _span(text, stmt):
    """The character range of a statement."""
    return (_char_offset(text, stmt.lineno, stmt.col_offset),
            _char_offset(text, stmt.end_lineno, stmt.end_col_offset))


def _removal(text, stmt):
    """The range that removes a statement: its whole lines when nothing
    else stands on them (a comment after it goes with it), else the
    statement and the semicolon after it."""
    start, end = _span(text, stmt)
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end < 0 else line_end
    after = text[end:line_end].strip()
    if not text[line_start:start].strip() and (not after or after.startswith("#")):
        if line_end < len(text):
            return line_start, line_end + 1
        return max(line_start - 1, 0), line_end
    semicolon = re.match(r"\s*;[ \t]*", text[end:line_end])
    return start, end + (semicolon.end() if semicolon else 0)


def _line(text, position) -> int:
    return text.count("\n", 0, position) + 1


def statement_dump(text: str, name: str):
    """``ast.dump`` of the last top-level statement that binds *name*, or
    None. A dialog keeps it when it loads the statement. A non-modal
    dialog then sees at OK that the statement was changed meanwhile."""
    try:
        stmt = _last_assignment(ast.parse(text), name)
    except SyntaxError:
        return None
    return None if stmt is None else ast.dump(stmt)


def rewrites(text: str, name: str, snippet: str) -> bool:
    """Whether the statement of *name* in the dialog's *snippet* differs
    from its last definition in *text*. Right after loading, a difference
    means the statement holds parts the dialog cannot show: OK would
    rewrite them (decision 4, Anton 2026-11-25: warn, then rewrite)."""
    try:
        last = _last_assignment(ast.parse(text), name)
        mine = [s for s in ast.parse(snippet).body if name in _bound_in(s)]
    except SyntaxError:
        return False
    return last is not None and bool(mine) and ast.dump(last) != ast.dump(mine[-1])


def place(text: str, snippet: str, editing=(), loaded=None) -> Placement:
    """Where the statements of a dialog's *snippet* go in the instruction
    file *text*. *editing* names the objects the dialog loaded with "Edit
    existing"; *loaded* maps them to their statement_dump() at loading.

    Without an edited name in the snippet, everything is appended (a new
    object). Otherwise, the rules Anton decided on 2026-11-25:

    1. The statement of an edited name replaces the LAST definition of that
       name, where it stands. The name is fixed while editing (the
       dialogs).
    2. Earlier definitions of the name, copies from append-only editing,
       are removed.
    3. A line that would read a name before its definition is refused,
       with the line named: OK stays disabled.
    4. A statement the dialog writes unchanged keeps its text as written,
       layout and comments included (the dialogs warn when it would
       change at once: rewrites()).
    5. A NEW statement written together with an edited one goes directly
       above it, in the order of the snippet. A new statement after the
       last edited one is appended at the end of the file, as every new
       object is: a new figure with an axis edited from one of its cells.
       It went directly below the last edited one at first (for the run
       dialog's ``TR1 = R1.traces``), which was REPLACED on 2026-11-26
       (Anton): the new figure landed below the axis, before the other
       axes it uses, and was refused by rule 3.

    The system run dialog replaced its run in place from 2026-11-21; this
    generalises it to every dialog."""
    snippet = snippet.strip("\n")
    if not snippet:
        return Placement()
    try:
        parts = ast.parse(snippet).body
    except SyntaxError as exc:
        return Placement(problems=["The dialog wrote no valid Python (line %s: %s)."
                                   % (exc.lineno, exc.msg)])
    editing = {str(n) for n in (editing or ()) if n}
    if not editing:
        return Placement(append=snippet)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return Placement(problems=["The instruction file does not parse (line %s: "
                                   "%s). Correct it first." % (exc.lineno, exc.msg)])
    definitions = {name: [s for s in tree.body if name in _bound_in(s)]
                   for name in editing}
    # the parts of the snippet, grouped around the edited statements
    groups, pending, seen = [], [], set()
    for i, part in enumerate(parts):
        names = _bound_in(part) & editing
        name = next(iter(names)) if len(names) == 1 else None
        if name is not None and not definitions[name] and loaded and name in loaded:
            return Placement(problems=["%s is no longer in the instruction file. "
                                       "Open the dialog again." % name])
        if name is None or not definitions[name]:
            pending.append(i)
            continue
        if name in seen:
            return Placement(problems=["%s is written twice." % name])
        seen.add(name)
        groups.append([name, i, pending + [i]])
        pending = []
    if not groups:
        return Placement(append=snippet)
    trailing = [ast.get_source_segment(snippet, parts[i]) for i in pending]
    problems, edits = [], []
    for name, anchor, members in groups:
        last = definitions[name][-1]
        if not (isinstance(last, ast.Assign) and len(last.targets) == 1
                and isinstance(last.targets[0], ast.Name)):
            # an if block, a loop, a tuple target: replacing it would take
            # the rest of that statement with it
            problems.append("%s is last defined on line %d by a statement "
                            "this dialog cannot edit. Edit it in the editor."
                            % (name, last.lineno))
            continue
        if loaded and name in loaded and loaded[name] != ast.dump(last):
            problems.append("%s was changed in the instruction file while the "
                            "dialog was open. Open the dialog again." % name)
            continue
        start, end = _span(text, last)
        pieces = []
        for i in members:
            if i == anchor and ast.dump(parts[i]) == ast.dump(last):
                pieces.append(text[start:end])
            else:
                pieces.append(ast.get_source_segment(snippet, parts[i]))
        edits.append((start, end, "\n".join(pieces)))
        for copy in definitions[name][:-1]:
            if (isinstance(copy, ast.Assign) and len(copy.targets) == 1
                    and isinstance(copy.targets[0], ast.Name)):
                edits.append(_removal(text, copy) + ("",))
    if problems:
        return Placement(problems=problems)
    if trailing:
        newline = "" if not text or text.endswith("\n") else "\n"
        edits.append((len(text), len(text), newline + "\n".join(trailing) + "\n"))
    edits = sorted(e for e in edits if text[e[0]:e[1]] != e[2])
    for (_s1, e1, _t1), (s2, _e2, _t2) in zip(edits, edits[1:]):
        if s2 < e1:
            return Placement(problems=["The edited statements overlap in the "
                                       "instruction file. Edit them by hand."])
    new = text
    for start, end, piece in reversed(edits):
        new = new[:start] + piece + new[end:]
    try:
        new_tree = ast.parse(new)
    except SyntaxError as exc:
        return Placement(problems=["The edit would not parse (line %s: %s)."
                                   % (exc.lineno, exc.msg)])

    def old_position(position):
        """The position in *text* of a position in *new*; a position in
        written text maps to the start of the statement it replaces, with
        True."""
        shift = 0
        for start, end, piece in edits:
            if position < start + shift:
                break
            if position < start + shift + len(piece):
                return start, True
            shift += len(piece) - (end - start)
        return position - shift, False

    before = {(ast.dump(s), n) for s, n, _d in _early_uses(tree)}
    for stmt, name, definition in _early_uses(new_tree):
        if (ast.dump(stmt), name) in before:
            continue
        user, written = old_position(_span(new, stmt)[0])
        where = _line(text, old_position(_span(new, definition)[0])[0])
        if written:
            who = ", ".join(sorted(_bound_in(stmt))) or "line %d" % _line(text, user)
            problems.append("%s would use %s before its definition on line %d. "
                            "Move %s above line %d first."
                            % (who, name, where, name, _line(text, user)))
        else:
            problems.append("Line %d would use %s before its definition on line "
                            "%d, because the earlier %s is removed. Move line %d "
                            "below line %d first, or delete it."
                            % (_line(text, user), name, where, name,
                               _line(text, user), where))
    return Placement(problems=problems) if problems else Placement(edits=edits)


def trace_set_of(text: str, result: str):
    """The name of the trace set ``NAME = <result>.traces`` written AFTER
    the last definition of *result* (the line the system run dialog writes
    after a run), or None. A trace set between two definitions of the
    result holds the superseded run's traces and does not count."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    found = None
    for stmt in tree.body:
        bound = _bound_in(stmt)
        value = getattr(stmt, "value", None)
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and isinstance(value, ast.Attribute) and value.attr == "traces"
                and isinstance(value.value, ast.Name) and value.value.id == result):
            found = stmt.targets[0].id
        elif result in bound or found in bound:
            found = None          # the run, or that trace set, is bound anew
    return found


def pardef_sources(src) -> dict:
    """The parameters a ``pardefs=`` / ``params=`` source text defines, per
    source, for the fields that may name one (a sweep limit):
    ``{"circuit": [...], "specs": [...], "user": [...], "spec_var": name}``
    from an ``sl.selectPars(...)`` call (``spec_var`` is the variable its
    specs are read from, ``SPECS_<stem>``, or None). A list is ``None`` when its names are not
    in the text - ``pardefs='circuit'``, or ``circuit="all"`` /
    ``specs="all"`` - so every identifier must be allowed for that source
    (Anton, 2026-11-09). A dict or a list of pairs counts as user values."""
    out = {"circuit": [], "specs": [], "user": [], "spec_var": None}
    if src is None:
        return out
    try:
        node = ast.parse(str(src).strip(), mode="eval").body
    except SyntaxError:
        return out
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        value = node
    if value == "circuit":
        out["circuit"] = None
        return out
    if isinstance(value, dict):
        out["user"] = [str(k) for k in value]
        return out
    if isinstance(value, (list, tuple)):
        out["user"] = [str(p[0]) for p in value
                       if isinstance(p, (list, tuple)) and len(p) == 2]
        return out
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "selectPars"):
        return out
    if len(node.args) > 1 and isinstance(node.args[1], ast.Name):
        out["spec_var"] = node.args[1].id        # SPECS_<stem>: the spec file
    for kw in node.keywords:
        try:
            v = ast.literal_eval(kw.value)
        except (ValueError, SyntaxError):
            continue
        if kw.arg in ("circuit", "specs"):
            out[kw.arg] = None if v == "all" else [str(n) for n in (v or [])]
        elif kw.arg == "user" and isinstance(v, dict):
            out["user"] = [str(n) for n in v]
    return out


def next_result_name(base: str, text: str) -> str:
    """Next free result-variable name ``<base><N>`` for the instruction-file
    *text*: ``LAPLACE2`` if ``LAPLACE1`` is already assigned, else ``LAPLACE1``.
    """
    nums = [int(m.group(1))
            for m in re.finditer(r"\b" + re.escape(base) + r"(\d+)\s*=", text)]
    return f"{base}{max(nums, default=0) + 1}"


def _has_import(lines) -> bool:
    return any(l.strip() == _IMPORT_LINE for l in lines)


def header_insertion(text: str):
    """The instruction-file header that *text* lacks, as ``(position,
    line)``: insert *line* at character *position*. None when the file has
    the header. ONE rule for where the header goes and how its line is
    written. The instruction editor applies it on every insert
    (InstrEditor._seed_header), and ensure_header() gives the text.

    The header is ``import SLiCAP as sl`` only. It no longer seeds
    ``cir = sl.makeCircuit(...)``: creating a circuit object is a SEPARATE,
    explicit action (Anton, 2026-08-16). The old behaviour bound the one
    name 'cir' to whichever schematic happened to be active first. It then
    checked only whether ANY makeCircuit line existed, so instructions for
    other schematics were composed against that same circuit. A circuit
    object is also APPENDED where it is created, never prepended.
    Prepending a second one would silently change the meaning of every
    instruction already in the file.

    The import is recognised by ast, so a comment after it counts. The
    header goes after a module docstring and after ``from __future__``
    imports, which must stay first (2026-11-21, a review: prepended before
    them the file did not compile). *line* starts with a line break when
    the text before it does not end in one. A file that does not parse is
    judged by its lines and gets the header at the top.

    REPLACED 2026-11-22: header_position() gave the position only. The
    instruction editor and ensure_header() each built the line themselves.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        if _has_import(text.splitlines()):
            return None
        return 0, _IMPORT_LINE + "\n"
    for stmt in tree.body:
        if isinstance(stmt, ast.Import) and any(
                a.name == "SLiCAP" and a.asname == "sl" for a in stmt.names):
            return None
    position = 0
    for i, stmt in enumerate(tree.body):
        docstring = (i == 0 and isinstance(stmt, ast.Expr)
                     and isinstance(stmt.value, ast.Constant)
                     and isinstance(stmt.value.value, str))
        future = isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__"
        if not (docstring or future):
            break
        end = _char_offset(text, stmt.end_lineno, stmt.end_col_offset)
        nl = text.find("\n", end)
        position = len(text) if nl < 0 else nl + 1
    head = text[:position]
    newline = "\n" if head and not head.endswith("\n") else ""
    return position, newline + _IMPORT_LINE + "\n"


def circuit_objects(text: str) -> list:
    """Every circuit object the instruction file DEFINES, in file order:
    ``[{"name": "cir", "path": "sch/Vamp.slicap_sch"}, …]``.

    The instruction file - not the set of open tabs - is the authority on
    which circuit objects exist and which schematic each one was built from
    (Anton, 2026-08-16).  It is also what actually runs, so an instruction
    can only reference a circuit defined here.
    """
    out = []
    for call in parse_calls(text):
        if call["func"] != "makeCircuit" or not call["assigned"]:
            continue
        arg = (call["args"] or [""])[0].strip()
        if len(arg) >= 2 and arg[0] in "\"'" and arg[-1] == arg[0]:
            arg = arg[1:-1]
        out.append({"name": call["name"], "path": arg})
    return out


def netlist_calls(text: str) -> list:
    """The paths of every ``sl.makeCircuit(...)`` call in the instruction
    file, assigned or not, in file order: ``["sch/amp.spice_sch", …]``.

    An NGspice schematic has no circuit object. Its netlist step is a bare
    ``sl.makeCircuit("sch/<name>.spice_sch")`` line, which writes
    cir/<name>.spice_cir. An NGspice instruction may only be added when
    that line exists (Anton, 2026-11-07: the file, not the disk, says
    which netlists the run makes; a .spice_cir left by an earlier session
    does not count)."""
    out = []
    for call in parse_calls(text):
        if call["func"] != "makeCircuit":
            continue
        arg = (call["args"] or [""])[0].strip()
        if len(arg) >= 2 and arg[0] in "\"'" and arg[-1] == arg[0]:
            arg = arg[1:-1]
        out.append(arg)
    return out


# the functions whose result is a Laplace transfer function: a filter block
# of a system diagram is made from one (SystemExtensionSpecs.md 10.3.1)
TRANSFER_FUNCS = ("doLaplace", "filterFunc", "sectionFunc", "transferFunc")


def spec_var_name(file_name: str) -> str:
    """The variable an instruction file loads a spec CSV into:
    ``SPECS_<stem>`` with the stem made a valid identifier fragment
    (``specs.csv`` -> ``SPECS_specs``).  Shared by the snippet dialog and
    the analysis dialog so one CSV is loaded into ONE variable."""
    stem = file_name.strip().rsplit(".", 1)[0] if "." in file_name else file_name.strip()
    frag = re.sub(r"\W", "_", stem).strip("_") or "specs"
    if frag[0].isdigit():
        frag = "_" + frag
    return f"SPECS_{frag}"


def ensure_header(text: str) -> str:
    """*text* with the instruction-file header, as the instruction editor
    makes it on its next insert (header_insertion). Idempotent: a text
    that has the header is returned as it is."""
    insertion = header_insertion(text)
    if insertion is None:
        return text
    position, line = insertion
    return text[:position] + line + text[position:]


def main_py_source(project_name: str, instr_stem: str | None = None,
                   author: str | None = None) -> str:
    """Source of the project ``main.py`` that sets up the project and runs the
    instruction file (omitted when *instr_stem* is None — project creation).

    *author* is only passed at project creation; later rewrites (instruction
    runs) omit it, which is harmless: initProject() persisted it in the
    project SLiCAP.ini and keeps the stored value when the kwarg is absent."""
    if author is not None:
        init_line = (f"sl.initProject({quoted(project_name)}, "
                     f"author={quoted(author)})")
    else:
        init_line = f"sl.initProject({quoted(project_name)})"
    lines = [_IMPORT_LINE, init_line]
    if instr_stem:
        lines.append(f"import {instr_stem}")
        # Design-data manifest (SLNG.md): after the instruction file ran,
        # walk its namespace and index the results for the Design data
        # panel. Guarded — a manifest problem must never fail the run.
        lines += [
            "try:",
            "    from SLiCAP.schematic.design_data import write_manifest",
            f"    write_manifest(vars({instr_stem}), "
            f"{quoted(instr_stem + '.py')})",
            "except Exception as e:",
            "    print('Warning: design-data manifest not written:', e)",
        ]
    return "\n".join(lines) + "\n"


def write_main_py(project_root, project_name: str, instr_stem: str | None = None,
                  author: str | None = None) -> Path:
    """Write/refresh ``<project_root>/main.py``; return its path."""
    path = Path(project_root) / "main.py"
    path.write_text(main_py_source(project_name, instr_stem, author),
                    encoding="utf-8")
    return path
