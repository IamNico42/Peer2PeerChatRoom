import tkinter as tk

class EmojiBar(tk.Frame):
    def __init__(self, master, target_entry: tk.Entry, *, emojis=None, max_height=38, bg="#23272f", fg="#f6f6f6"):
        super().__init__(master, bg=bg)
        self.master = master
        self.target_entry = target_entry
        self.max_height = max_height
        self.bg = bg
        self.fg = fg
        self.visible = True
        self.animating = False
        self.anim_id = None
        self.current_height = max_height

        # Container für das animierbare Innenleben
        self.clip = tk.Canvas(self, height=self.max_height, bg=bg, highlightthickness=0, bd=0)
        self.clip.pack(fill="x", expand=True)
        self.inner = tk.Frame(self.clip, bg=bg)
        self.clip.create_window((0, 0), window=self.inner, anchor="nw")

        emojis = emojis or ["😀", "😂", "😍", "😎", "👍", "🎉", "🔥", "🥳", "😭", "😡", "🤔", "🙌", "❤️", "😅", "😇"]
        for emoji in emojis:
            btn = tk.Button(
                self.inner,
                text=emoji,
                font=("Segoe UI Emoji", 13),
                width=2,
                relief="flat",
                bg=bg,
                fg=fg,
                activebackground="#36393f",
                command=lambda e=emoji: self.target_entry.insert(tk.END, e)
            )
            btn.pack(side="left", padx=1)

    def toggle(self):
        if self.animating:
            return
        self.visible = not self.visible
        target = self.max_height if self.visible else 0
        self.animate_to(target)

    def animate_to(self, target):
        self.animating = True
        current = self.clip.winfo_height()
        step = 2 if target > current else -2

        def step_anim():
            nonlocal current
            if (step > 0 and current >= target) or (step < 0 and current <= target):
                self.clip.configure(height=target)
                self.animating = False
                return
            current += step
            self.clip.configure(height=current)
            self.anim_id = self.after(8, step_anim)

        step_anim()

    def set_height(self, h):
        self.current_height = h
        self.configure(height=h)
        self.update_idletasks()
