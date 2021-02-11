import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
import numpy as np
import sympy as sp


class Interpreter:
    def __init__(self):
        self.globals_eval = {"COS": np.cos, "SIN": np.sin, "EXP": np.exp}
        self.globals_sym = {"COS": sp.cos, "SIN": sp.sin, "EXP": sp.exp}
        self.variables = {}

        # JFD
        # self.evaluate("F(X)=COS(X)", "Function")

    def evaluate(self, string, mode):
        output = None

        if mode == "Eval":
            if string[-1] == '=':
                output = str(eval(string[:-1], self.globals_eval, self.variables))
                print(output)
            else:
                exec(string, self.globals_eval, self.variables)
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
            self.variables[variable] = sp.Symbol(variable)

            # Declare symbolic function
            exec(function + "_sym" + string[equal_idx:], self.globals_sym, self.variables)

            # Declare python function (python functions have a _f suffix)
            self.variables[function] = lambda xx: self.variables[function + "_sym"].subs(self.variables[variable], xx).evalf()

        return output

    def plot(self):  # TODO Clean
        # Open new window
        top = tk.Toplevel()
        top.title("Plot")

        # CREATE FUNCTION SELECTOR
        # Search function names
        func_names = [name for name, var in self.variables.items() if callable(var)]

        # Create string variable for dropdown menu
        string_var = tk.StringVar()

        if len(func_names) > 0:
            string_var.set(func_names[0])

        # FUNCTION FRAME
        function_frame = tk.Frame(top)
        function_frame.pack(side=tk.TOP)
        # Function choose label
        tk.Label(function_frame, text="Plotted function").pack(side=tk.TOP)
        # Function choose dropdown
        tk.OptionMenu(function_frame, string_var, '', *func_names).pack(side=tk.TOP)

        # PLOT RANGE FRAME
        range_frame = tk.Frame(top)
        range_frame.pack(side=tk.TOP)
        # Min value label and entry
        tk.Label(range_frame, text="x_min:").pack(side=tk.LEFT)
        min_var = tk.StringVar(value="0.0")
        min_var.trace("w", lambda *args: plot_func())  # Update plot on min modification
        min_entry = tk.Entry(range_frame, textvariable=min_var)
        min_entry.pack(side=tk.LEFT)
        # Max value label and entry
        max_var = tk.StringVar(value="1.0")
        max_var.trace("w", lambda *args: plot_func())  # Update plot on max modification
        max_entry = tk.Entry(range_frame, textvariable=max_var)
        max_entry.pack(side=tk.RIGHT)
        tk.Label(range_frame, text="x_max:").pack(side=tk.RIGHT)

        # Create plot
        f = Figure()
        a = f.add_subplot(111)
        a.grid()
        l, = a.plot([], [])

        # Create and assign function name change callback
        def plot_func():
            # Get plotted function
            function_name = string_var.get()
            if function_name == "":
                return
            # Compute plot range
            x_list = np.linspace(float(min_var.get()), float(max_var.get()), 100)
            # Compute curve points
            f_eval = self.variables[function_name]
            y_list = [f_eval(x) for x in x_list]
            # Update plot
            l.set_xdata(x_list)
            l.set_ydata(y_list)
            a.set_title(function_name)
            a.relim()
            a.autoscale_view()
            f.canvas.draw()
            f.canvas.flush_events()

        string_var.trace("w", lambda *args: plot_func())

        # Plot function
        plot_func()

        # Create canvas
        canvas = FigureCanvasTkAgg(f, top)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
