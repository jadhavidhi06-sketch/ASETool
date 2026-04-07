import curses

def run_curses_menu(options):
    selected = [False]*len(options)
    def _menu(stdscr):
        curses.curs_set(0)
        idx = 0
        while True:
            stdscr.clear()
            stdscr.addstr(0,0,"Use arrows to move, space to toggle, Enter to confirm\n")
            for i,opt in enumerate(options):
                mark = "[x]" if selected[i] else "[ ]"
                if i==idx:
                    stdscr.addstr(i+2,0, f"> {mark} {opt}\n", curses.A_REVERSE)
                else:
                    stdscr.addstr(i+2,0, f"  {mark} {opt}\n")
            k = stdscr.getch()
            if k in (curses.KEY_DOWN, ord('j')):
                idx = (idx+1)%len(options)
            elif k in (curses.KEY_UP, ord('k')):
                idx = (idx-1)%len(options)
            elif k == ord(' '):
                selected[idx] = not selected[idx]
            elif k in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                break
    curses.wrapper(_menu)
    chosen = [o for i,o in enumerate(options) if selected[i]]
    return chosen or options
