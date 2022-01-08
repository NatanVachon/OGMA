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


def evaluate(equation):
    # Compute python string
    print(equation)

    output = None

    # Check if every variable in the expression is declared
    declared_vars = set(get_variable_names())
    left_undeclared_vars = equation.left.variables - declared_vars
    right_undeclared_vars = equation.right.variables - declared_vars

    # VARIABLE DECLARATION MODE
    # We enter this mode if :
    #   - Maximum one undeclared variable on the left side
    #   - No undeclared variable on the right side

    if len(left_undeclared_vars) == 1 and len(right_undeclared_vars) == 0:
        # Declare unknown variable
        new_var = next(iter(left_undeclared_vars))
        variables_sym[new_var] = sp.Symbol(new_var)

        # Create equation object
        equation = "_solve = " + str(equation.left) + '-' + str(equation.right)
        exec(equation, globals_sym, variables_sym)

        # Compute solution
        output = sp.solve(variables_sym["_solve"], variables_sym[new_var])

        # Assign value
        # exec(string, globals_eval, variables_eval)
        variables_eval[new_var] = output[0]

        if new_var in variable_callbacks.keys():
            # Execute constant callbacks
            execute_callbacks(new_var)
        else:
            # Create callback list for the new constant
            variable_callbacks[new_var] = []

            # Add callbacks to each free symbol of the newly declared constant
            for free_sym in variables_sym[new_var].free_symbols:
                # Avoid infinite calls
                if str(free_sym) != new_var:
                    variable_callbacks[str(free_sym)].append(lambda: execute_callbacks(new_var))

        # Call variable callbacks
        execute_callbacks("any")

    # VARIABLE UPDATE MODE
    # We enter this mode if :
    #   - No undeclared variable on the left side
    #   - No undeclared variable on the right side
    #   - Exactly one declared variable on the left side

    elif len(left_undeclared_vars) == 0 and len(right_undeclared_vars) == 0 and len(equation.left.base) == 1:
        # Get updated variable
        var = str(equation.left.base[0])

        # Create equation object
        equation = "_solve = " + str(equation.left) + '-' + str(equation.right)
        exec(equation, globals_sym, variables_sym)

        # Compute solution
        output = sp.solve(variables_sym["_solve"], variables_sym[var])

        # Assign value
        # exec(string, globals_eval, variables_eval)
        variables_eval[var] = output[0]

    # FUNCTION DECLARATION MODE
    # We enter this mode if :
    #   - Exactly two undeclared variable on the left side (function name and silent variable)
    #   - Exactly one undeclared variable on the right side (silent variable)
    #   - The right side undeclared variable is one of the left's
    elif len(left_undeclared_vars) == 2 and len(right_undeclared_vars) == 1 \
            and right_undeclared_vars[0] in left_undeclared_vars:

        # Create left side string
        left_string = str(equation.left)  # TODO remove parenthesis fix

        assert '(' in left_string and ')' in left_string, "Missing parenthesis for function declaration"
        # Expression must be in the following format: f(x) = ...

        # Extract variable name and function name TODO look for (?) format
        first_brace_idx = left_string.find('(')
        variable = left_string[first_brace_idx + 1]
        function = left_string[first_brace_idx - 1]

        # Declare symbolic variable
        variables_sym[variable] = sp.Symbol(variable)

        # Declare symbolic function
        exec(function + "_sym" + '=' + str(equation.right), globals_sym, variables_sym)

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

    # EVALUATION MODE
    # We enter this mode if :
    #   - No undeclared variables on the left side
    #   - No characters on the right side
    elif len(left_undeclared_vars) == 0 and len(equation.right) == 0:
        output = str(eval(str(equation.left), globals_eval, variables_eval))
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
            if len(var_name) > 4 and var_name[-4:] == "_sym":
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
