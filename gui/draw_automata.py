from pyglet import app, shapes, text, image
from pyglet.window import Window

from game_model.constants import *
from timed_automata.timed_automata_classes import TimedAutomata, State, Transition

font_name = 'Times New Roman'
font_size = 20


def draw_state(x, y, width, height, current_state=False):
    nodes = [shapes.Ellipse(x, y, width, height, color=WHITE),
             shapes.Ellipse(x, y, width - 2, height - 2, color=BLACK if not current_state else (0, 255, 0))]
    return nodes


def draw_lane_change_automata(x_start=0, y_start=480) -> list:
    nodes = [
        # q0:
        *draw_state(x_start + 260, y_start + 370, 60, 30, True),
        text.Label("q0: cc",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 230, y=845),
        # q1:
        *draw_state(x_start + 400, y_start + 220, 30, 30),
        text.Label("q1",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 385, y=y_start + 215),
        # q0 -> q1:
        shapes.Line(x_start + 300, y_start + 350, x_start + 385, y_start + 245, width=2, color=WHITE),
        shapes.Line(x_start + 385, y_start + 245, x_start + 384, y_start + 255, width=2, color=WHITE),
        shapes.Line(x_start + 385, y_start + 245, x_start + 375, y_start + 246, width=2, color=WHITE),
        # q2:
        *draw_state(x_start + 260, y_start + 70, 120, 50),
        text.Label("q2: ¬∃c : pc(c)",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 180, y=y_start + 80),
        text.Label("x <= t_o",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 200, y=y_start + 45),
        # q1 -> q2:
        shapes.Line(x_start + 385, y_start + 195, x_start + 310, y_start + 115, width=2, color=WHITE),
        shapes.Line(x_start + 310, y_start + 115, x_start + 310, y_start + 125, width=2, color=WHITE),
        shapes.Line(x_start + 310, y_start + 115, x_start + 320, y_start + 120, width=2, color=WHITE),
        # q2 -> q0:
        shapes.Line(x_start + 260, y_start + 120, x_start + 260, y_start + 340, width=2, color=WHITE),
        shapes.Line(x_start + 260, y_start + 340, x_start + 265, y_start + 335, width=2, color=WHITE),
        shapes.Line(x_start + 260, y_start + 340, x_start + 255, y_start + 335, width=2, color=WHITE),
        # q3:
        *draw_state(x_start + 120, y_start + 220, 100, 30),
        text.Label("q3: x <= t_lc",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 50, y=y_start + 215),
        # q2 -> q3:
        shapes.Line(x_start + 210, y_start + 115, x_start + 140, y_start + 190, width=2, color=WHITE),
        shapes.Line(x_start + 140, y_start + 190, x_start + 145, y_start + 180, width=2, color=WHITE),
        shapes.Line(x_start + 140, y_start + 190, x_start + 150, y_start + 185, width=2, color=WHITE),
        # q3 -> q0:
        shapes.Line(x_start + 140, y_start + 250, x_start + 220, y_start + 350, width=2, color=WHITE),
        shapes.Line(x_start + 220, y_start + 350, x_start + 210, y_start + 345, width=2, color=WHITE),
        shapes.Line(x_start + 220, y_start + 350, x_start + 220, y_start + 340, width=2, color=WHITE),
    ]

    return nodes


def draw_crossing_automata(x_start=0, y_start=0) -> list:
    nodes = [
        # q0:
        *draw_state(x_start + 60, y_start + 370, 30, 30, True),
        text.Label("q0",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 50, y=y_start + 365),
        # q1:
        *draw_state(x_start + 200, y_start + 370, 30, 30),
        text.Label("q1",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 190, y=y_start + 365),
        # q2:
        *draw_state(x_start + 350, y_start + 370, 30, 30),
        text.Label("q2",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 340, y=y_start + 365),
        # q3:
        *draw_state(x_start + 300, y_start + 80, 30, 30),
        text.Label("q3",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 290, y=y_start + 75),
        # q4:
        *draw_state(x_start + 110, y_start + 80, 30, 30),
        text.Label("q4",
                   font_name='Times New Roman',
                   font_size=20,
                   x=x_start + 100, y=y_start + 75),
    ]

    return nodes


def sub_sup(n: int, subscript=True) -> str:
    sub = ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"]
    sup = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]
    res = ''
    for i in range(len(str(n))):
        i = n % 10
        n = int(n / 10)
        res = (sub[i] if subscript else sup[i]) + res
    return res


win = Window(width=450, height=900)


@win.event
def on_draw():
    for shape in draw_lane_change_automata():
        shape.draw()
    shapes.Line(0, 480, 450, 480, width=2, color=WHITE).draw()
    for shape in draw_crossing_automata():
        shape.draw()


if __name__ == '__main__':
    s0 = State(player=0, name='s0', time_invariants=[lambda l: l[0] < 5])
    s1 = State(player=0, name='s1', time_invariants=[lambda l: l[0] > 4])

    t1 = Transition(0, s0, s1, [], time_guards=[lambda l: l[0] >= 4])
    t2 = Transition(0, s1, s0, [0])

    a = TimedAutomata(None, 0, [s0, s1], s0, [t1, t2], 1, None)

    print(a.current_state.name)
    print(a.clocks)
    a.move(delay=2)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t1)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t2)
    print(a.current_state.name)
    print(a.clocks)
    a.move(delay=2)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t1)
    print(a.current_state.name)
    print(a.clocks)
    a.move(delay=0.1)
    a.move(transition=t1)
    print(a.current_state.name)
    print(a.clocks)
    a.move(transition=t2)
    print(a.current_state.name)
    print(a.clocks)
    app.run()
