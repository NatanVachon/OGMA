import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
import numpy as np
import sympy as sp


globals_eval = {"COS": np.cos, "SIN": np.sin, "EXP": np.exp}
globals_sym = {"COS": sp.cos, "SIN": sp.sin, "EXP": sp.exp}
variables_sym = {}
variables_eval = {}


def get_variable_names():
    names = []
    for name in globals_eval.keys():
        if name != "__builtins__":
            names.append(name)

    names += list(variables_eval.keys())

    return names


def evaluate(string, mode):
    output = None

    if mode == "Eval":
        if string[-1] == '=':
            output = str(eval(string[:-1], globals_eval, variables_eval))
            print(output)
        else:
            exec(string, globals_eval, variables_eval)
            print("Exec done")

    elif mode == "Declare":
        # TODO Explain all of this

        # Sanity check
        assert '=' in string, "A declaration must contain a '=' character"

        # Check if we declare a variable or a function
        equal_idx = string.find('=')

        # If there are parenthesis before the equal character, a function is declared
        if '(' in string[:equal_idx] and ')' in string[:equal_idx]:
            # Expression must be in the following format: f(x) = ...

            # Extract variable name and function name
            first_brace_idx = string.find('(')
            variable = string[first_brace_idx + 1]
            function = string[:first_brace_idx]

            # Declare symbolic variable
            variables_sym[variable] = sp.Symbol(variable)

            # Declare symbolic function
            exec(function + "_sym" + string[equal_idx:], globals_sym, variables_sym)

            # Declare python symbolic function
            variables_sym[function] = lambda xx: \
                variables_sym[function + "_sym"].subs(variables_sym[variable], xx).evalf()

            # Declare python eval function
            def f_eval(xx):
                f_x = variables_sym[function + "_sym"].subs(variables_sym[variable], xx)
                for s in f_x.free_symbols:
                    f_x = f_x.subs(s, variables_eval[str(s)])
                return f_x.evalf()

            variables_eval[function] = f_eval

        # Else, a variable is declared
        else:
            # Get declared variable name
            variable = string[:equal_idx]

            # Declare symbolic variable
            variables_sym[variable] = sp.Symbol(variable)

            # Assign variable value
            exec(string, globals_eval, variables_eval)
            pass

    return output


def plot(root):  # TODO Clean
    # Open new window
    top = tk.Toplevel()
    top.transient(root)  # Plot window is always on top of main window
    top.title("Plot")

    # CREATE FUNCTION SELECTOR
    # Search function names
    func_names = [name for name, var in variables_eval.items() if callable(var)]

    # FUNCTION FRAME
    function_frame = tk.Frame(top)
    function_frame.pack(side=tk.TOP)
    # Function choose label
    tk.Label(function_frame, text="Plotted function").pack(side=tk.TOP)
    # Function choose dropdown
    string_var = tk.StringVar()
    if len(func_names) > 0:
        string_var.set(func_names[0])
    string_var.trace("w", lambda *args: plot_func())
    tk.OptionMenu(function_frame, string_var, '', *func_names).pack(side=tk.TOP)

    # PLOT RANGE FRAME
    range_frame = tk.Frame(top)
    range_frame.pack(side=tk.TOP)
    # Min value label and entry
    tk.Label(range_frame, text="x_min:").pack(side=tk.LEFT)
    min_var = tk.StringVar(value="-10.0")
    min_var.trace("w", lambda *args: plot_func())  # Update plot on min modification
    min_entry = tk.Entry(range_frame, textvariable=min_var)
    min_entry.pack(side=tk.LEFT)
    # Max value label and entry
    tk.Label(range_frame, text="x_max:").pack(side=tk.LEFT)
    max_var = tk.StringVar(value="10.0")
    max_var.trace("w", lambda *args: plot_func())  # Update plot on max modification
    max_entry = tk.Entry(range_frame, textvariable=max_var)
    max_entry.pack(side=tk.LEFT)
    # Point nb label and entry
    tk.Label(range_frame, text="Point nb:").pack(side=tk.LEFT)
    point_nb_var = tk.StringVar(value="100")
    point_nb_var.trace("w", lambda *args: plot_func())  # Update plot on step modification
    point_nb_entry = tk.Entry(range_frame, textvariable=point_nb_var)
    point_nb_entry.pack(side=tk.LEFT)

    # Create plot
    f = Figure()
    a = f.add_subplot(111)
    a.grid()
    l, = a.plot([], [])

    # Create and assign function name change callback
    def plot_func():
        # Get plotted function
        function_name = string_var.get()

        # Plotted function sanity check
        if function_name == '':
            return

        # Compute plot range
        # Catch value error in case of invalid input
        try:
            x_list = np.linspace(float(min_var.get()), float(max_var.get()), int(point_nb_var.get()))
        except ValueError:
            return
        # Compute curve points
        f_eval = variables_eval[function_name]
        y_list = ([sp.re(f_eval(x)) for x in x_list])
        # Update plot
        l.set_xdata(x_list)
        l.set_ydata(y_list)
        a.set_title(function_name)
        a.relim()
        a.autoscale_view()
        f.canvas.draw()
        f.canvas.flush_events()

    # Plot function
    plot_func()

    # Create canvas
    canvas = FigureCanvasTkAgg(f, top)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def open_variable_window(root):
    # Open new window
    top = tk.Toplevel(background="Gray")
    top.title("Variables")
    top.transient(root)  # Variable window is always on top of the main window

    # Print each function and variable
    for var_name, var_value in variables_sym.items():
        # If the name ends with "_sym", this is a function
        if var_name[-4:] == "_sym":
            tk.Label(top, text="{0} = {1}".format(var_name[:-4], str(var_value))).pack(side=tk.TOP)

        # If the variable isn't callable and exists in variables_sym and variables_eval, it's a constant
        if not callable(var_value) and var_name in variables_eval.keys():
            tk.Label(top, text="{0} = {1}".format(var_name, str(variables_eval[var_name]))).pack(side=tk.TOP)
