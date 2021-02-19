import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
import numpy as np
import sympy as sp


globals_eval = {"COS": np.cos, "SIN": np.sin, "EXP": np.exp}
globals_sym = {"COS": sp.cos, "SIN": sp.sin, "EXP": sp.exp}
variables = {}


def get_variable_names():
    names = []
    for name in globals_eval.keys():
        if name != "__builtins__":
            names.append(name)

    names += list(variables.keys())

    return names


def evaluate(string, mode):
    output = None

    if mode == "Eval":
        if string[-1] == '=':
            output = str(eval(string[:-1], globals_eval, variables))
            print(output)
        else:
            exec(string, globals_eval, variables)
            print("Exec done")

    elif mode == "Function":
        # TODO Sanity check
        # TODO Explain all of this

        # Expression must be in the following format: f(x) = ...

        # Extract variable name and function name
        first_brace_idx = string.find('(')
        equal_idx = string.find('=')
        variable = string[first_brace_idx + 1]
        function = string[:first_brace_idx]

        # Declare symbolic variable
        variables[variable] = sp.Symbol(variable)

        # Declare symbolic function
        exec(function + "_sym" + string[equal_idx:], globals_sym, variables)

        # Declare python function (python functions have a _f suffix)
        variables[function] = lambda xx: variables[function + "_sym"].subs(variables[variable], xx).evalf()

    return output


def plot(root):  # TODO Clean
    # Open new window
    top = tk.Toplevel()
    top.transient(root)  # Plot window is always on top of main window
    top.title("Plot")

    # CREATE FUNCTION SELECTOR
    # Search function names
    func_names = [name for name, var in variables.items() if callable(var)]

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

        # Compute plot range
        # Catch value error in case of invalid input
        try:
            x_list = np.linspace(float(min_var.get()), float(max_var.get()), int(point_nb_var.get()))
        except ValueError:
            return
        # Compute curve points
        f_eval = variables[function_name]
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

    # Variables label
    tk.Label(top, text="Variables:", font="Calibri 16").pack(side=tk.TOP, pady=(0, 10))

    # Print each variable
    for var_name, var_value in variables.items():
        tk.Label(top, text="{0} = {1}".format(var_name, str(var_value))).pack(side=tk.TOP)
