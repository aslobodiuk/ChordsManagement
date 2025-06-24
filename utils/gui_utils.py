import tkinter as tk

def show_non_blocking_message(root, msg_type: str = 'success', msg: str = "Success", duration: int = 2000):
    style = {
        'success': ('#dff0d8', '#3c763d'),
        'error': ('#f2dede', '#a94442')
    }
    # Create a popup window
    popup = tk.Toplevel(root)
    popup.title("")
    popup.attributes("-topmost", True)
    popup.resizable(False, False)
    popup.overrideredirect(True)  # Hide window decorations

    # Set popup size
    width, height = 200, 60
    popup.geometry(f"{width}x{height}")

    # Calculate position: top-right of the root window
    root.update_idletasks()  # Ensure root window has correct size
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()

    x = root_x + root_width - width - 10  # 10px padding from right
    y = root_y + 10  # 10px padding from top
    popup.geometry(f"+{x}+{y}")

    # Add message label
    label = tk.Label(popup, text=msg, font=("Arial", 11), bg=style[msg_type][0], fg=style[msg_type][1], relief="solid",
                     bd=1)
    label.pack(expand=True, fill="both", padx=10, pady=10)

    # Auto-destroy after duration (e.g., 2000 ms)
    popup.after(duration, popup.destroy)
