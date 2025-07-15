"""
Main window class for the Mineral Spectra Analyzer application
"""

import os
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from ui.data_tab import DataTab
from ui.analysis_tab import AnalysisTab
from ui.results_tab import ResultsTab
from ui.settings_tab import SettingsTab
from ui.dialogs import AboutDialog, DocumentationDialog
from ui.multi_spectrum_viewer import MultiSpectrumViewer
from core.data_manager2 import DataManager


class MainWindow:
    """Main application window with tabbed interface"""
    
    def __init__(self, master):
        self.master = master
        self.root = master
        self.root.geometry("1200x800")
        self.fullscreen = False
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Initialize data folders
        self.init_folders([
            "spectral/mixed_raw_files",
            "spectral/end-member_raw_files",
            "spectral/mixed_pre_processed",
            "spectral/spectral_library"
        ])
        
        # Create main layout
        self.create_main_layout()
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()
        
        # Status bar
        self.create_status_bar()
        
        # Initial status message
        self.update_status("Ready")
    
    def init_folders(self, folders):
        """Create directories if they don't exist"""
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    def create_main_layout(self):
        """Create main application layout with modern tabbed interface"""
        # Create menu bar first (but don't populate it yet)
        self.create_menu_bar()
        
        # Create notebook (tabbed interface)
        self.notebook = tb.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Create tabs
        self.data_tab = DataTab(self.notebook, self.data_manager, self.update_status)
        self.analysis_tab = AnalysisTab(self.notebook, self.data_manager, self.update_status)
        self.results_tab = ResultsTab(self.notebook, self.update_status, self.data_manager)
        self.settings_tab = SettingsTab(self.notebook, self.update_status, self.data_manager)
        
        # Add tabs to notebook
        self.notebook.add(self.data_tab.frame, text="Data Management")
        self.notebook.add(self.analysis_tab.frame, text="Analysis")
        self.notebook.add(self.results_tab.frame, text="Results")
        self.notebook.add(self.settings_tab.frame, text="Settings")
        
        # Connect analysis tab to results tab
        self.analysis_tab.set_results_tab(self.results_tab)
        
        # Connect data tab to analysis tab for refresh notifications
        self.data_tab.set_analysis_tab(self.analysis_tab)
        
        # Now populate the menu bar with commands
        self.populate_menu_bar()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Analysis menu
        self.analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Analysis", menu=self.analysis_menu)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Multi-Spectrum Viewer", command=self.open_multi_spectrum_viewer)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Fullscreen", command=self.toggle_fullscreen)
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        for theme in tb.Style().theme_names():
            theme_menu.add_command(label=theme.capitalize(), 
                                 command=lambda t=theme: self.change_theme(t))
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
    
    def populate_menu_bar(self):
        """Populate menu bar with commands after all components are created"""
        # Clear and repopulate file menu
        self.file_menu.delete(0, "end")
        self.file_menu.add_command(label="Import End-Member", 
                                 command=lambda: self.data_tab.add_spectra("end_member"))
        self.file_menu.add_command(label="Import Mixed Spectra", 
                                 command=lambda: self.data_tab.add_spectra("unmix"))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export Results", command=self.results_tab.export_results)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.close_window)
        
        # Clear and repopulate analysis menu
        self.analysis_menu.delete(0, "end")
        self.analysis_menu.add_command(label="Run WLS Analysis", 
                                     command=lambda: self.analysis_tab.run_analysis_with_params("WLS"))
        self.analysis_menu.add_command(label="Run STO Analysis", 
                                     command=lambda: self.analysis_tab.run_analysis_with_params("STO"))
    
    def create_status_bar(self):
        """Create application status bar"""
        status_frame = tb.Frame(self.root)
        status_frame.pack(side="bottom", fill="x")
        
        # Left side - status text
        self.status_var = tk.StringVar()
        status_label = tb.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side="left", padx=10)
        
        # Right side - additional info
        tb.Separator(status_frame, orient="vertical").pack(side="right", padx=8, fill="y")
        
        version_label = tb.Label(status_frame, text="v1.0")
        version_label.pack(side="right", padx=10)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_var.set(message)
    
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Control-q>", lambda e: self.close_window())
        self.root.bind("<Control-o>", lambda e: self.data_tab.add_spectra())
        self.root.bind("<Control-r>", lambda e: self.analysis_tab.run_analysis_from_ui())
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        return "break"
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)
        return "break"
    
    def change_theme(self, theme_name):
        """Change application theme"""
        tb.Style(theme=theme_name)
        self.update_status(f"Theme changed to {theme_name}")
    
    def show_documentation(self):
        """Show application documentation"""
        doc_dialog = DocumentationDialog(self.root)
        doc_dialog.show()
    
    def show_about(self):
        """Show about dialog"""
        about_dialog = AboutDialog(self.root)
        about_dialog.show()
    
    def close_window(self):
        """Close the application"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()
    
    def switch_to_analysis_tab(self):
        """Switch to the analysis tab"""
        self.notebook.select(1)  # Index 1 is the analysis tab
    
    def open_multi_spectrum_viewer(self):
        """Open the multi-spectrum comparison viewer"""
        try:
            viewer = MultiSpectrumViewer(self.root, self.data_manager)
            viewer.show()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open multi-spectrum viewer: {str(e)}")
