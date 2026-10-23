"""Pure layout helpers (no Kivy import: testable on a PC): how a row of chips shares its width, and the biggest font that fits."""


def weights(needs):
    """Width weights for a row of buttons: each button gets a share proportional to the width its text needs (a long text such as
    'Por desbloquear' gets more room than 'Todos'), and the row is always completely filled."""
    return [max(1.0, float(n)) for n in needs]


def fit_size(measure, text, available, biggest, smallest, step=0.5):
    """Biggest font size (between `smallest` and `biggest`) for which `measure(text, size)` fits in `available`.
    Returns `smallest` when even that is too wide (the text is then shortened with '...')."""
    size = biggest
    while size > smallest and measure(text, size) > available:
        size -= step
    return max(size, smallest)
