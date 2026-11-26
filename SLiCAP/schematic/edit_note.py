"""The edit state of an instruction dialog, and the note that shows it.

Editing an existing object edits it where it stands (Anton, 2026-11-22).
The rules, decided on 2026-11-25, are in ``instr_file.place()``. This widget
is the part every dialog shares:

- it remembers which objects the dialog loaded with "Edit existing", and
  their statements as they stood (``loaded()``, for a non-modal dialog);
- it shows why OK is disabled, for example a line that would use a name
  before its definition;
- it warns when the dialog rewrites a statement that holds parts it cannot
  show (decision 4: warn, then rewrite).

The name is fixed while editing (decision 1): the name field the dialog
gives to ``follow()`` is read-only while it edits, and gets a free name
again for a new object.
"""
import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from .instr_file import place, rewrites, statement_dump


class EditNote(QLabel):
    """The edit state and the note of an instruction dialog over the file
    *text* (the text at open). *with_text*: the dialog has no preview, so
    the note itself shows what OK writes."""

    def __init__(self, text, with_text=False, parent=None):
        super().__init__(parent)
        self._text = text or ""
        self._with_text = with_text
        self._names = []          # the edited objects, in loading order
        self._loaded = {}         # name -> its statement at loading
        self._pending = []        # loaded, not yet compared with the dialog
        self._rewritten = []      # the dialog cannot show all of these
        self._field = None        # the dialog's name field (follow())
        self._free_name = None
        self._field_name = None   # the edited object it holds
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setStyleSheet("color: #b34700; font-size: 9pt;")
        self.setVisible(False)

    def follow(self, field, free_name) -> None:
        """Keep the name field *field* fixed while the dialog edits the
        object it names; a new object gets ``free_name()``."""
        self._field, self._free_name = field, free_name

    def start(self, name, in_field=True, warned=False) -> None:
        """The dialog loaded *name* with "Edit existing". Called when the
        fields are filled: the next check() compares the statement with
        what the dialog writes. *in_field*: the object of the name field;
        False for an object the dialog names elsewhere (a measurement row
        of the Traces dialog). *warned*: edited in another dialog that
        warned itself about parts it cannot show (an axis edited from a
        cell of the Figures dialog), so no comparison here."""
        name = str(name)
        in_field = in_field and self._field is not None
        if in_field and self._field_name not in (None, name):
            # another object of the name field: no longer edited, and the
            # field keeps the name it gets below
            old, self._field_name = self._field_name, None
            self.drop(old)
        if name not in self._names:
            self._names.append(name)
        self._loaded[name] = statement_dump(self._text, name)
        if not warned:
            self._pending.append(name)
        if in_field:
            self._field_name = name
            self._field.setReadOnly(True)
            self._field.setText(name)

    def stop(self) -> None:
        """The object of the name field is a new one again: the field gets
        a free name."""
        if self._field_name is not None:
            self.drop(self._field_name)

    def drop(self, name) -> None:
        """The dialog no longer edits *name*."""
        name = str(name)
        self._names = [n for n in self._names if n != name]
        self._pending = [n for n in self._pending if n != name]
        self._rewritten = [n for n in self._rewritten if n != name]
        self._loaded.pop(name, None)
        if name == self._field_name:
            self._field_name = None
            self._field.setReadOnly(False)
            self._field.setText(self._free_name())

    def names(self) -> tuple:
        """The objects the dialog edits."""
        return tuple(self._names)

    def loaded(self) -> dict:
        """``{name: statement_dump}`` of the edited objects at loading."""
        return dict(self._loaded)

    def check(self, snippet: str) -> bool:
        """Show the state for the dialog's *snippet*: why it cannot go in,
        or that OK rewrites a statement. False when OK must stay disabled."""
        for name in self._pending:
            if rewrites(self._text, name, snippet) and name not in self._rewritten:
                self._rewritten.append(name)
        self._pending = []
        problems = place(self._text, snippet, self._names, self._loaded).problems \
            if snippet else []
        if problems:
            self._show(html.escape(problems[0]))
            return False
        rewritten = [n for n in self._rewritten if n in self._names]
        if not rewritten:
            self.setVisible(False)
            return True
        what = ", ".join(rewritten)
        holds = "holds" if len(rewritten) == 1 else "hold"
        note = ("%s %s parts this dialog cannot show. OK writes "
                % (html.escape(what), holds))
        them = "it" if len(rewritten) == 1 else "them"
        if self._with_text:
            note += "%s as:<pre>%s</pre>" % (them, html.escape(snippet))
        else:
            note += "%s as in the preview." % them
        self._show(note)
        return True

    def _show(self, rich: str) -> None:
        self.setText(rich)
        self.setVisible(True)
