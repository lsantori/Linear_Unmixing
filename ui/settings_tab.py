"""
Settings tab for the Mineral Spectra Analyzer
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledFrame


class SettingsTab:
    """Settings tab implementation"""
    
    def __init__(self, parent, status_callback, data_manager=None):
        self.parent = parent
        self.update_status = status_callback
        self.data_manager = data_manager
        
        # Create main frame
        self.frame = tb.Frame(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings tab UI"""
        # Create scrolled frame for settings
        settings_frame = ScrolledFrame(self.frame, autohide=True)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        inner_frame = settings_frame.container
        
        # Application settings section
        app_section = tb.Labelframe(inner_frame, text="Application Settings", padding=15)
        app_section.pack(fill="x", pady=10)
        
        # Theme selection
        theme_frame = tb.Frame(app_section)
        theme_frame.pack(fill="x", pady=5)
        
        tb.Label(theme_frame, text="Theme:").pack(side="left", padx=5)
        
        self.theme_var = tk.StringVar(value=tb.Style().theme.name)
        theme_combobox = tb.Combobox(theme_frame, values=sorted(tb.Style().theme_names()), 
                                    textvariable=self.theme_var)
        theme_combobox.pack(side="left", padx=5)
        theme_combobox.bind("<<ComboboxSelected>>", 
                          lambda e: self.change_theme(self.theme_var.get()))
        
        
        # Data folder settings
        folder_section = tb.Labelframe(inner_frame, text="Data Folders", padding=15)
        folder_section.pack(fill="x", pady=10)
        
        self.folder_vars = {}
        folders = [
            ("Mixed Raw Files", "spectral/mixed_raw_files"),
            ("End-Member Raw Files", "spectral/end-member_raw_files"),
            ("Mixed Pre-Processed", "spectral/mixed_pre_processed"),
            ("Spectral Library", "spectral/spectral_library")
        ]
        
        for label, path in folders:
            folder_frame = tb.Frame(folder_section)
            folder_frame.pack(fill="x", pady=5)
            
            tb.Label(folder_frame, text=f"{label}:").pack(side="left", padx=5)
            
            path_var = tk.StringVar(value=path)
            self.folder_vars[label] = path_var
            path_entry = tb.Entry(folder_frame, textvariable=path_var, width=40)
            path_entry.pack(side="left", padx=5, fill="x", expand=True)
            
            tb.Button(folder_frame, text="Browse", 
                     command=lambda pv=path_var: self.select_folder(pv)).pack(side="left", padx=5)
        
        # Analysis settings
        analysis_section = tb.Labelframe(inner_frame, text="Analysis Settings", padding=15)
        analysis_section.pack(fill="x", pady=10)
        
        # Default algorithm
        alg_frame = tb.Frame(analysis_section)
        alg_frame.pack(fill="x", pady=5)
        
        tb.Label(alg_frame, text="Default Algorithm:").pack(side="left", padx=5)
        
        self.default_alg_var = tk.StringVar(value="WLS")
        tb.Radiobutton(alg_frame, text="WLS", variable=self.default_alg_var, 
                      value="WLS").pack(side="left", padx=10)
        tb.Radiobutton(alg_frame, text="STO", variable=self.default_alg_var, 
                      value="STO").pack(side="left", padx=10)
        
        # Export settings
        export_section = tb.Labelframe(inner_frame, text="Export Settings", padding=15)
        export_section.pack(fill="x", pady=10)
        
        # Default export format
        export_frame = tb.Frame(export_section)
        export_frame.pack(fill="x", pady=5)
        
        tb.Label(export_frame, text="Default Export Format:").pack(side="left", padx=5)
        
        self.export_format_var = tk.StringVar(value="csv")
        tb.Radiobutton(export_frame, text="CSV", variable=self.export_format_var, 
                      value="csv").pack(side="left", padx=10)
        tb.Radiobutton(export_frame, text="TXT", variable=self.export_format_var, 
                      value="txt").pack(side="left", padx=10)
        
        # Include spectra by default
        self.include_spectra_var = tk.BooleanVar(value=True)
        tb.Checkbutton(export_section, text="Include spectral data in exports by default", 
                      variable=self.include_spectra_var).pack(anchor="w", pady=5)
        
        # Plot settings
        plot_section = tb.Labelframe(inner_frame, text="Plot Settings", padding=15)
        plot_section.pack(fill="x", pady=10)
        
        # Default DPI for saved plots
        dpi_frame = tb.Frame(plot_section)
        dpi_frame.pack(fill="x", pady=5)
        
        tb.Label(dpi_frame, text="Default plot DPI:").pack(side="left", padx=5)
        self.plot_dpi_var = tk.IntVar(value=300)
        dpi_spinbox = tb.Spinbox(dpi_frame, from_=72, to=600, increment=50,
                                textvariable=self.plot_dpi_var, width=10)
        dpi_spinbox.pack(side="left", padx=5)
        
        # Save settings button
        tb.Button(inner_frame, text="Save Settings", 
                 bootstyle="success", command=self.save_settings).pack(pady=15)
        
        # Reset to defaults button
        tb.Button(inner_frame, text="Reset to Defaults", 
                 bootstyle="warning", command=self.reset_defaults).pack()
        
    
    def select_folder(self, path_var):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(initialdir=path_var.get())
        if folder:
            path_var.set(folder)
    
    def change_theme(self, theme_name):
        """Change application theme"""
        tb.Style(theme=theme_name)
        self.update_status(f"Theme changed to {theme_name}")
    
    def save_settings(self):
        """Save application settings"""
        # In a real application, this would save to a configuration file
        # For now, we'll just show a success message
        
        # Validate settings
        valid = True
        for label, path_var in self.folder_vars.items():
            if not path_var.get():
                messagebox.showwarning("Invalid Settings", 
                                     f"{label} path cannot be empty")
                valid = False
                break
        
        if valid:
            # Here you would typically save to a config file
            # For example, using configparser or json
            messagebox.showinfo("Settings", "Settings saved successfully")
            self.update_status("Settings saved")
    
    def reset_defaults(self):
        """Reset all settings to default values"""
        if messagebox.askyesno("Reset Settings", 
                             "Are you sure you want to reset all settings to defaults?"):
            # Reset theme
            self.theme_var.set("superhero")
            self.change_theme("superhero")
            
            # Reset folders
            default_folders = {
                "Mixed Raw Files": "spectral/mixed_raw_files",
                "End-Member Raw Files": "spectral/end-member_raw_files",
                "Mixed Pre-Processed": "spectral/mixed_pre_processed",
                "Spectral Library": "spectral/spectral_library"
            }
            
            for label, path in default_folders.items():
                self.folder_vars[label].set(path)
            
            # Reset analysis settings
            self.default_alg_var.set("WLS")
            
            # Reset export settings
            self.export_format_var.set("csv")
            self.include_spectra_var.set(True)
            
            # Reset plot settings
            self.plot_dpi_var.set(300)
            
            messagebox.showinfo("Settings", "Settings reset to defaults")
            self.update_status("Settings reset to defaults")
    
    
