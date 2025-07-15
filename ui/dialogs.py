"""
Dialog windows for the Mineral Spectra Analyzer
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledFrame


class AboutDialog:
    """About dialog window"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tb.Toplevel(parent)
        self.window.title("About")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the about dialog UI"""
        # Center content
        content_frame = tb.Frame(self.window)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Application icon placeholder
        icon_frame = tb.Frame(content_frame, width=64, height=64)
        icon_frame.pack(pady=10)
        
        # Application name
        tb.Label(content_frame, text="Mineral Spectra Analyzer", 
                font=("TkDefaultFont", 14, "bold")).pack(pady=5)
        
        # Version
        tb.Label(content_frame, text="Version 1.0").pack()
        
        # Description
        tb.Label(content_frame, 
                text="Advanced spectral unmixing analysis tool\nfor mineral identification",
                justify="center").pack(pady=10)
        
        # Copyright
        tb.Label(content_frame, 
                text="© 2025 Your Organization",
                bootstyle="secondary").pack(pady=5)
        
        # Close button
        tb.Button(content_frame, text="Close", 
                 command=self.window.destroy).pack(pady=10)
        
        # Make dialog modal
        self.window.transient(self.parent)
        self.window.grab_set()
    
    def show(self):
        """Show the about dialog"""
        self.parent.wait_window(self.window)


class DocumentationDialog:
    """Documentation viewer dialog"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tb.Toplevel(parent)
        self.window.title("Documentation")
        self.window.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the documentation dialog UI"""
        # Create scrolled frame
        doc_frame = ScrolledFrame(self.window)
        doc_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        inner_frame = doc_frame.container
        
        # Documentation content
        tb.Label(inner_frame, text="Mineral Spectra Analyzer", 
                font=("TkDefaultFont", 16, "bold")).pack(pady=10)
        
        # Add documentation sections
        sections = [
            ("Overview", 
             "The Mineral Spectra Analyzer is a sophisticated tool for analyzing mineral " +
             "spectral data using advanced unmixing algorithms. It helps identify the " +
             "composition of mixed mineral samples by comparing them to a library of " +
             "known end-member spectra."),
            
            ("Getting Started",
             "1. Import your end-member spectra using File > Import End-Member\n" +
             "2. Import mixed spectra to analyze using File > Import Mixed Spectra\n" +
             "3. Go to the Analysis tab\n" +
             "4. Select a mixed spectrum and one or more end-members\n" +
             "5. Choose an algorithm (WLS or STO)\n" +
             "6. Click 'Run Analysis'\n" +
             "7. View results in the Results tab"),
            
            ("Data Management",
             "The Data Management tab allows you to:\n" +
             "• Import new spectral data files (CSV or TXT format)\n" +
             "• View existing spectra in your library\n" +
             "• Rename or delete spectra\n" +
             "• Preview spectral plots\n\n" +
             "Supported file formats include CSV files with wavenumber, emissivity, " +
             "and uncertainty columns."),
            
            ("Analysis Methods",
             "WLS (Weighted Least Squares):\n" +
             "• Uses measurement uncertainties as weights\n" +
             "• Minimizes weighted residuals\n" +
             "• Removes negative abundances iteratively\n" +
             "• Best for data with known uncertainties\n\n" +
             "STO (Sum-to-One):\n" +
             "• Constrains abundances to sum to 1\n" +
             "• Physically meaningful for closed systems\n" +
             "• Provides normalized abundances\n" +
             "• Ideal for mineral mixtures"),
            
            ("Results Interpretation",
             "The Results tab displays:\n" +
             "• Spectral fit plot showing mixed spectrum vs. model\n" +
             "• Residual error plot\n" +
             "• RMS error value\n" +
             "• Abundance table with uncertainties\n" +
             "• Total abundance (should be close to 1 for good fits)\n\n" +
             "Lower RMS values indicate better fits."),
            
            ("Exporting Results",
             "Results can be exported in CSV or TXT format including:\n" +
             "• Sample and algorithm information\n" +
             "• End-member abundances and errors\n" +
             "• Optionally, full spectral data\n" +
             "• Model fit and end-member spectra"),
            
            ("Tips and Best Practices",
             "• Ensure all spectra cover the same wavelength range\n" +
             "• Use high-quality end-member spectra\n" +
             "• Start with fewer end-members and add more if needed\n" +
             "• Check residual plots for systematic errors\n" +
             "• Consider using wavelength filtering for noisy regions\n" +
             "• Compare WLS and STO results for validation")
        ]
        
        for title, content in sections:
            section_frame = tb.Labelframe(inner_frame, text=title, padding=10)
            section_frame.pack(fill="x", pady=10, padx=5)
            
            tb.Label(section_frame, text=content, wraplength=700, 
                    justify="left").pack(pady=5)
        
        # Close button
        close_frame = tb.Frame(self.window)
        close_frame.pack(side="bottom", fill="x", pady=10)
        
        tb.Button(close_frame, text="Close", 
                 command=self.window.destroy).pack()
    
    def show(self):
        """Show the documentation dialog"""
        self.window.deiconify()
        self.window.focus_set()


class ProgressDialog:
    """Progress dialog for long operations"""
    
    def __init__(self, parent, title="Processing", message="Please wait..."):
        self.parent = parent
        self.window = tb.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.resizable(False, False)
        
        self.setup_ui(message)
        
        # Make dialog modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center on parent
        self.center_on_parent()
    
    def setup_ui(self, message):
        """Setup the progress dialog UI"""
        # Center content
        content_frame = tb.Frame(self.window)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Message
        self.message_label = tb.Label(content_frame, text=message)
        self.message_label.pack(pady=10)
        
        # Progress bar
        self.progress = tb.Progressbar(content_frame, mode="indeterminate", 
                                     length=300)
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # Cancel button (optional)
        self.cancel_button = tb.Button(content_frame, text="Cancel", 
                                     state="disabled")
        self.cancel_button.pack(pady=5)
    
    def center_on_parent(self):
        """Center the dialog on its parent window"""
        self.window.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.window.winfo_width()
        dialog_height = self.window.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.window.geometry(f"+{x}+{y}")
    
    def update_message(self, message):
        """Update the progress message"""
        self.message_label.config(text=message)
        self.window.update()
    
    def set_determinate(self, maximum=100):
        """Switch to determinate mode"""
        self.progress.stop()
        self.progress.config(mode="determinate", maximum=maximum)
    
    def update_progress(self, value):
        """Update progress value (for determinate mode)"""
        self.progress['value'] = value
        self.window.update()
    
    def enable_cancel(self, command):
        """Enable the cancel button with a callback"""
        self.cancel_button.config(state="normal", command=command)
    
    def close(self):
        """Close the progress dialog"""
        self.progress.stop()
        self.window.destroy()


class InputDialog:
    """Generic input dialog"""
    
    def __init__(self, parent, title="Input", prompt="Enter value:", 
                 initial_value="", validate=None):
        self.parent = parent
        self.result = None
        self.validate = validate
        
        self.window = tb.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.resizable(False, False)
        
        self.setup_ui(prompt, initial_value)
        
        # Make dialog modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center on parent
        self.center_on_parent()
    
    def setup_ui(self, prompt, initial_value):
        """Setup the input dialog UI"""
        # Center content
        content_frame = tb.Frame(self.window)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Prompt
        tb.Label(content_frame, text=prompt).pack(pady=5)
        
        # Input field
        self.input_var = tk.StringVar(value=initial_value)
        self.input_entry = tb.Entry(content_frame, textvariable=self.input_var, 
                                  width=30)
        self.input_entry.pack(pady=5)
        self.input_entry.select_range(0, "end")
        self.input_entry.focus()
        
        # Buttons
        button_frame = tb.Frame(content_frame)
        button_frame.pack(pady=10, fill="x")
        
        tb.Button(button_frame, text="OK", 
                 command=self.on_ok).pack(side="left", padx=10)
        tb.Button(button_frame, text="Cancel", 
                 command=self.on_cancel).pack(side="right", padx=10)
        
        # Key bindings
        self.input_entry.bind("<Return>", lambda e: self.on_ok())
        self.input_entry.bind("<Escape>", lambda e: self.on_cancel())
    
    def center_on_parent(self):
        """Center the dialog on its parent window"""
        self.window.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.window.winfo_width()
        dialog_height = self.window.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.window.geometry(f"+{x}+{y}")
    
    def on_ok(self):
        """Handle OK button click"""
        value = self.input_var.get().strip()
        
        # Validate if function provided
        if self.validate:
            error = self.validate(value)
            if error:
                tk.messagebox.showwarning("Invalid Input", error, parent=self.window)
                return
        
        self.result = value
        self.window.destroy()
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.window.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.parent.wait_window(self.window)
        return self.result
