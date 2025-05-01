import tkinter as tk

class AutocompleteEntry(tk.Entry):
    def __init__(self, player_names, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_names = sorted(player_names)
        self.var = self["textvariable"] = tk.StringVar()
        self.var.trace_add("write", self.update_suggestions)

        self.listbox = None
        self.bind("<Tab>", self.select_suggestion)
        self.bind("<Down>", self.move_down)

    def update_player_names(self, new_names):
        self.player_names = sorted(new_names)

    def update_suggestions(self, *args):
        typed = self.var.get().strip()
        
        # Hide dropdown if entry is empty
        if not typed:
            if self.listbox:
                self.listbox.destroy()
            return

        last_word = typed.split()[-1]
        matches = [name for name in self.player_names if last_word.lower() in name.lower()]
        self.show_dropdown(matches)

    def show_dropdown(self, matches):
        if self.listbox:
            self.listbox.destroy()

        if not matches:
            return

        self.listbox = tk.Listbox()
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.place(in_=self, relx=0, rely=1, anchor="nw", width=self.winfo_width())

        for match in matches:
            self.listbox.insert(tk.END, match)

    def select_suggestion(self, event=None):
        if self.listbox and self.listbox.size() > 0:
            selected = self.listbox.get(0)
            self.replace_current_word(selected)
            self.listbox.destroy()
            self.icursor(tk.END)
            return "break"
    def replace_current_word(self, replacement):
        current_text = self.var.get()
        cursor_pos = self.index(tk.INSERT)
        
        # Find the boundaries of the word at cursor
        start = current_text.rfind(" ", 0, cursor_pos) + 1
        end = current_text.find(" ", cursor_pos)
        if end == -1:
            end = len(current_text)

        new_text = current_text[:start] + replacement + current_text[end:]
        self.var.set(new_text)
    def move_down(self, event=None):
        if self.listbox:
            self.listbox.focus()
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.listbox.event_generate("<Return>")
            return "break"

    def on_listbox_select(self, event):
        if not self.listbox:
            return
        selection = self.listbox.get(self.listbox.curselection())
        self.replace_current_word(selection)
        self.listbox.destroy()
        self.icursor(tk.END)
