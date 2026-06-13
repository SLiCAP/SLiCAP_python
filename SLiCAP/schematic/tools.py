from collections import defaultdict

from .component_item import ComponentItem, SYMBOL_PREFIX

_ANNOTATION = {"ground", "port"}


def rename_left_right_top_bottom(scene) -> int:
    """
    Renumber all non-annotation component IDs left-to-right, top-to-bottom.

    Components are grouped by refdes PREFIX (not symbol), so everything sharing a
    prefix is numbered in one sequence — every subcircuit block uses 'X', and
    e.g. nmos/pmos both use 'M', so their refdes must not collide.  Sort order:
    y ascending (top first), then x ascending (left first) within the same row.
    The per-prefix counter is seeded to match (keep consistent with _next_id).

    Returns the number of components whose ID actually changed.
    """
    groups: dict[str, list[ComponentItem]] = defaultdict(list)
    for item in scene.items():
        if isinstance(item, ComponentItem) and item.symbol_name not in _ANNOTATION:
            prefix = SYMBOL_PREFIX.get(item.symbol_name, "X")
            groups[prefix].append(item)

    changed = 0
    for prefix, comps in groups.items():
        comps.sort(key=lambda c: (round(c.pos().y()), round(c.pos().x())))
        for i, comp in enumerate(comps, start=1):
            new_id = f"{prefix}{i}"
            if comp.instance_id != new_id:
                comp.instance_id = new_id
                comp.update_labels()
                changed += 1
        scene._counters[prefix] = len(comps) + 1

    return changed
