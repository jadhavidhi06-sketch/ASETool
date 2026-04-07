import curses
import curses.ascii
import math

def run_curses_menu(options, defaults=None, title="Use arrows to move, space to toggle, Enter to confirm"):
    """
    options: list[str]
    defaults: iterable of indices or option strings to pre-select (optional)
    Returns: list of selected option strings (if none selected, returns all options)
    """
    if defaults is None:
        defaults = []
    selected = [False] * len(options)

    # normalize defaults (accept indices or option values)
    for d in defaults:
        if isinstance(d, int) and 0 <= d < len(options):
            selected[d] = True
        elif isinstance(d, str) and d in options:
            selected[options.index(d)] = True

    def _clamp(n, lo, hi):
        return max(lo, min(hi, n))

    def _menu(stdscr):
        # Initialize
        try:
            curses.curs_set(0)
        except Exception:
            pass  # some terminals don't support cursor visibility changes

        stdscr.keypad(True)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except Exception:
            pass

        idx = 0
        top = 0  # index of top-most visible option for scrolling

        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()

            # Title / help line
            title_line = title
            stdscr.addnstr(0, 0, title_line, width - 1, curses.A_BOLD)

            visible_height = height - 2  # leave one line for title and one for status/footer
            if visible_height <= 0:
                # terminal too small
                stdscr.addnstr(1, 0, "Terminal too small", width - 1, curses.A_REVERSE)
                stdscr.refresh()
                k = stdscr.getch()
                if k in (27, ord('q')):  # ESC or q to quit
                    return False
                continue

            # Adjust scrolling window so idx is visible
            if idx < top:
                top = idx
            elif idx >= top + visible_height:
                top = idx - visible_height + 1

            # Render options
            for disp_i in range(visible_height):
                opt_i = top + disp_i
                if opt_i >= len(options):
                    break
                mark = "[x]" if selected[opt_i] else "[ ]"
                line_prefix = "> " if opt_i == idx else "  "
                line = f"{line_prefix}{mark} {options[opt_i]}"
                attr = curses.A_REVERSE if opt_i == idx else curses.A_NORMAL
                stdscr.addnstr(1 + disp_i, 0, line, width - 1, attr)

            # Footer / status
            status = "Space: toggle  Enter: confirm  Esc/q: cancel  Home/End/PageUp/PageDown supported"
            stdscr.addnstr(height - 1, 0, status, width - 1, curses.A_DIM)

            stdscr.refresh()
            k = stdscr.getch()

            # Mouse support
            if k == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, bstate = curses.getmouse()
                    # click inside list area?
                    if 1 <= my < 1 + visible_height:
                        clicked = top + (my - 1)
                        if clicked < len(options):
                            # toggle on click, move cursor there
                            idx = clicked
                            selected[idx] = not selected[idx]
                except Exception:
                    pass
                continue

            # Navigation keys
            if k in (curses.KEY_DOWN, ord('j')):
                idx = (idx + 1) % len(options)
            elif k in (curses.KEY_UP, ord('k')):
                idx = (idx - 1) % len(options)
            elif k in (curses.KEY_NPAGE,):  # Page Down
                idx = _clamp(idx + visible_height, 0, len(options) - 1)
            elif k in (curses.KEY_PPAGE,):  # Page Up
                idx = _clamp(idx - visible_height, 0, len(options) - 1)
            elif k in (curses.KEY_HOME,):
                idx = 0
            elif k in (curses.KEY_END,):
                idx = len(options) - 1
            elif k in (ord(' '),):
                selected[idx] = not selected[idx]
            elif k in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                return True
            elif k in (27, ord('q')):  # ESC or q to cancel
                return False
            # allow direct numeric selection 1..9
            elif curses.ascii.isdigit(k):
                digit = int(chr(k))
                if 1 <= digit <= len(options):
                    idx = digit - 1
            # otherwise ignore and continue

    ok = curses.wrapper(_menu)
    chosen = [o for i, o in enumerate(options) if selected[i]]
    if not ok:
        return []
    return chosen or options

if __name__ == "__main__":
    # quick CLI demo
    opts = [f"Option {i}" for i in range(1, 21)]
    selected = run_curses_menu(opts, defaults=[0, "Option 5"])
    print("Selected:", selected)
