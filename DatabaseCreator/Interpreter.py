import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk
import numpy as np
import sympy as sp


globals_eval = {"COS": np.cos, "SIN": np.sin, "EXP": np.exp, "LOG": np.log}
globals_sym = {"COS": sp.cos, "SIN": sp.sin, "EXP": sp.exp, "LOG": sp.log}
variables_sym = {}
variables_eval = {}

variable_callbacks = {"any": []}  # Contains functions to be called when a variable is updated


# Callback execution function
def execute_callbacks(var):
    for callback in variable_callbacks[var]:
        callback()


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
            print(function + "_sym" + string[equal_idx:])
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

            # Save python function in eval variables
            variables_eval[function] = f_eval

            if function in variable_callbacks.keys():
                # Execute function callbacks
                execute_callbacks(function)
            else:
                # Create callback list for the new function
                variable_callbacks[function] = []

            # Add callbacks to each free symbol of the newly declared function
            for symbol in variables_sym[function + "_sym"].free_symbols:
                # Don't add callback on the function argument
                if str(symbol) != variable:
                    variable_callbacks[str(symbol)].append(lambda: execute_callbacks(function))

        # Else, a constant is declared
        else:
            # Get declared constant name
            constant = string[:equal_idx]

            # Declare symbolic variable
            variables_sym[constant] = sp.Symbol(constant)

            # Assign constant value
            exec(string, globals_eval, variables_eval)

            if constant in variable_callbacks.keys():
                # Execute constant callbacks
                execute_callbacks(constant)
            else:
                # Create callback list for the new constant
                variable_callbacks[constant] = []

                # Add callbacks to each free symbol of the newly declared constant
                for symbol in variables_sym[constant].free_symbols:
                    # Avoid infinite calls
                    if str(symbol) != constant:
                        variable_callbacks[str(symbol)].append(lambda: execute_callbacks(constant))

        # Call variable callbacks
        execute_callbacks("any")

    elif mode == "Solve":
        # TODO For the moment, the unknown variable is always X
        # Declare unknown variable
        variables_sym['X'] = sp.Symbol('X')

        # Evaluate equation
        equal_idx = string.find('=')
        equation = "_solve = " + string[:equal_idx] + "-" + string[equal_idx+1:]
        exec(equation, globals_sym, variables_sym)

        # Compute solution
        output = sp.solve(variables_sym["_solve"], variables_sym['X'])
        print(output)

    return output


class PlotWindow(tk.Toplevel):
    window = None

    @staticmethod
    def toggle(root):
        if PlotWindow.window:
            PlotWindow.window.destroy()
            PlotWindow.window = None
        else:
            PlotWindow.window = PlotWindow(root)

    def __init__(self, root, **kw):
        # Super class initialization
        super().__init__(**kw)

        # Configure new window
        self.transient(root)  # Plot window is always on top of main window
        self.title("Plot")
        self.bind('p', lambda event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Initialize plotted function name
        self.function_name = ""

        # CREATE FUNCTION SELECTOR
        # Search function names
        func_names = [name for name, var in variables_eval.items() if callable(var)]

        # FUNCTION FRAME
        function_frame = tk.Frame(self)
        function_frame.pack(side=tk.TOP)
        # Function choose label
        tk.Label(function_frame, text="Plotted function").pack(side=tk.TOP)
        # Function choose dropdown
        self.function_name_var = tk.StringVar()
        if len(func_names) > 0:
            self.function_name_var.set(func_names[0])
        self.function_name_var.trace("w", lambda *args: self.plot_function())
        tk.OptionMenu(function_frame, self.function_name_var, '', *func_names).pack(side=tk.TOP)

        # PLOT RANGE FRAME
        range_frame = tk.Frame(self)
        range_frame.pack(side=tk.TOP)
        # Min value label and entry
        tk.Label(range_frame, text="x_min:").pack(side=tk.LEFT)
        self.min_var = tk.StringVar(value="-10.0")
        self.min_var.trace("w", lambda *args: self.plot_function())  # Update plot on min modification
        min_entry = tk.Entry(range_frame, textvariable=self.min_var)
        min_entry.pack(side=tk.LEFT)
        # Max value label and entry
        tk.Label(range_frame, text="x_max:").pack(side=tk.LEFT)
        self.max_var = tk.StringVar(value="10.0")
        self.max_var.trace("w", lambda *args: self.plot_function())  # Update plot on max modification
        max_entry = tk.Entry(range_frame, textvariable=self.max_var)
        max_entry.pack(side=tk.LEFT)
        # Point nb label and entry
        tk.Label(range_frame, text="Point nb:").pack(side=tk.LEFT)
        self.point_nb_var = tk.StringVar(value="100")
        self.point_nb_var.trace("w", lambda *args: self.plot_function())  # Update plot on step modification
        point_nb_entry = tk.Entry(range_frame, textvariable=self.point_nb_var)
        point_nb_entry.pack(side=tk.LEFT)

        # Create plot
        self.f = Figure()
        self.a = self.f.add_subplot(111)
        self.a.grid()
        self.l, = self.a.plot([], [])

        # Plot function
        self.plot_function()

        # Create canvas
        canvas = FigureCanvasTkAgg(self.f, self)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def plot_function(self):
        # Remove function callback
        if self.function_name != "" and self.plot_function in variable_callbacks[self.function_name]:
            variable_callbacks[self.function_name].remove(self.plot_function)

        # Get new function name
        self.function_name = self.function_name_var.get()

        # Add function callback
        if self.function_name != "":
            variable_callbacks[self.function_name].append(self.plot_function)

        # Plotted function sanity check
        if self.function_name == '':
            return

        # Compute plot range
        # Catch value error in case of invalid input
        try:
            x_list = np.linspace(float(self.min_var.get()), float(self.max_var.get()), int(self.point_nb_var.get()))
        except ValueError:
            return
        # Compute curve points
        f_eval = variables_eval[self.function_name]
        y_list = ([sp.re(f_eval(x)) for x in x_list])
        # Update plot
        self.l.set_xdata(x_list)
        self.l.set_ydata(y_list)
        self.a.set_title(self.function_name)
        self.a.relim()
        self.a.autoscale_view()
        self.f.canvas.draw()
        self.f.canvas.flush_events()

    def destroy(self):
        # Remove function callback
        if self.function_name != "" and self.plot_function in variable_callbacks[self.function_name]:
            variable_callbacks[self.function_name].remove(self.plot_function)

        # Destroy window
        super().destroy()


def toggle_variable_window(root):
    # Define destroy function
    def destroy():
        toggle_variable_window.top.destroy()
        toggle_variable_window.top = None
        # Add display function to variables callback
        variable_callbacks["any"].remove(display_variables)

    # Define display function
    def display_variables():
        ax.clear()
        ax.set_axis_off()
        # Initialize y position
        y_pos = 1.0
        for var_name, var_value in variables_sym.items():
            # If the name ends with "_sym", this is a function
            if var_name[-4:] == "_sym":
                # TODO get_latex_rpz
                var_value_str = str(var_value).replace('**', '^').replace('*', '')  # TODO REMOVE
                ax.text(0.1, y_pos, "${0} = {1}$".format(var_name[:-4], var_value_str), fontsize=16)
                y_pos -= 0.1

            # If the variable isn't callable and exists in variables_sym and variables_eval, it's a constant
            elif not callable(var_value) and var_name in variables_eval.keys():
                var_value_str = str(variables_eval[var_name]).replace('**', '^').replace('*', '')  # TODO REMOVE
                ax.text(0.1, y_pos, "${0} = {1}$".format(var_name, var_value_str), fontsize=16)
                y_pos -= 0.1

        # Update figure
        f.canvas.draw()
        f.canvas.flush_events()

    # Check not to raise error
    if not hasattr(toggle_variable_window, "top"):
        toggle_variable_window.top = None

    # If window is already open, close it
    if toggle_variable_window.top:
        destroy()
        return

    # Open new window
    toggle_variable_window.top = tk.Toplevel()
    toggle_variable_window.top.title("Variables")
    toggle_variable_window.top.transient(root)  # Variable window is always on top of the main window
    # Set window geometry
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    toggle_variable_window.top.geometry("{0}x{1}+{2}+{3}".format(int(0.1 * w), int(0.5 * h), int(0.9 * w), 10))
    # Bind destroy
    toggle_variable_window.top.bind('v', lambda event: destroy())

    # Create figure
    f = Figure()
    ax = f.add_subplot(111)

    # Add display function to variables callback
    variable_callbacks["any"].append(display_variables)

    # Display current variables
    display_variables()

    # Create canvas
    canvas = FigureCanvasTkAgg(f, toggle_variable_window.top)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
