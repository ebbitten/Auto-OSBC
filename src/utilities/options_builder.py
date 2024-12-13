import customtkinter

from view.font import button_med_font, subheading_font


class OptionsUI(customtkinter.CTkScrollableFrame):
    WIDTH = 800
    HEIGHT = 600

    def __init__(self, parent, title: str, option_info: dict, initial_values: dict, controller):
        super().__init__(parent)
        self.initial_values = initial_values

        parent.minsize(self.WIDTH, self.HEIGHT)
        parent.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        # Contains the widgets for option selection
        self.widgets = {}
        self.labels = {}
        self.frames = {}
        self.slider_values = {}

        self.controller = controller

        # Grid layout
        self.num_of_options = len(option_info.keys())
        self.rowconfigure(0, weight=0)  # Title
        for i in range(self.num_of_options):
            self.rowconfigure(i + 1, weight=0)
        self.rowconfigure(self.num_of_options + 1, weight=1)
        self.rowconfigure(self.num_of_options + 2, weight=0)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        # Title
        self.lbl_example_bot_options = customtkinter.CTkLabel(
            master=self, text=f"{title} Options", font=subheading_font()
        )
        self.lbl_example_bot_options.grid(row=0, column=0, padx=10, pady=20)

        # Create the options
        current_row = 1
        for key, info in option_info.items():
            if info["type"] == "slider":
                self.__create_slider(key, info, current_row)
            elif info["type"] == "checkbox":
                self.__create_checkbox(key, info, current_row)
            elif info["type"] == "dropdown":
                self.__create_dropdown(key, info, current_row)
            elif info["type"] == "text_edit":
                self.__create_text_edit(key, info, current_row)
            current_row += 1

            # Set initial values if they exist
            if key in self.initial_values:
                if info["type"] == "slider":
                    self.widgets[key].set(self.initial_values[key])
                elif info["type"] == "checkbox":
                    if self.initial_values[key]:
                        self.widgets[key].select()
                elif info["type"] == "dropdown":
                    self.widgets[key].set(self.initial_values[key])
                elif info["type"] == "text_edit":
                    self.widgets[key].insert(0, self.initial_values[key])

        # Save button
        self.btn_save = customtkinter.CTkButton(
            master=self,
            text="Save",
            command=self.__save_clicked,
            font=button_med_font(),
        )
        self.btn_save.grid(
            row=self.num_of_options + 2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=50,
            pady=10,
        )

    # ... rest of OptionsUI implementation ...


class OptionsBuilder:
    def __init__(self):
        self.options = {}
        self.initial_values = {}

    def set_initial_values(self, values: dict):
        """Set initial values for options from saved settings"""
        self.initial_values = values

    def add_slider_option(self, key: str, label: str, min_val: int, max_val: int):
        self.options[key] = {
            "type": "slider",
            "label": label,
            "min": min_val,
            "max": max_val,
        }

    def add_checkbox_option(self, key: str, label: str, options: list):
        self.options[key] = {"type": "checkbox", "label": label, "options": options}

    def add_dropdown_option(self, key: str, label: str, options: list):
        self.options[key] = {"type": "dropdown", "label": label, "options": options}

    def add_text_edit_option(self, key: str, label: str, placeholder: str):
        self.options[key] = {
            "type": "text_edit",
            "label": label,
            "placeholder": placeholder,
        }

    def build_ui(self, parent, controller) -> OptionsUI:
        """
        Build the options UI with the defined options.
        Args:
            parent: The parent widget
            controller: The bot controller
        Returns:
            The built OptionsUI
        """
        return OptionsUI(
            parent=parent,
            title=controller.get_active_bot().bot_title,
            option_info=self.options,
            initial_values=self.initial_values,
            controller=controller,
        )
