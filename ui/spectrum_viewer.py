"""
Spectrum viewer window for displaying individual spectra
"""

import os
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import ttkbootstrap as tb
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class SpectrumViewer:
    """Window for viewing individual spectrum"""
    
    def __init__(self, parent, spectrum_name, spectrum_df):
        self.parent = parent
        self.spectrum_name = spectrum_name
        self.spectrum_df = spectrum_df
        
        # Create window
        self.window = tb.Toplevel(parent)
        self.window.title(f"Spectrum: {spectrum_name}")
        self.window.geometry("900x700")
        
        self.setup_ui()
    
    def get_theme_colors(self):
        """Get appropriate colors based on current theme"""
        try:
            current_theme = tb.Style().theme.name.lower()
            
            # Define light and dark themes
            light_themes = {
                'cosmo', 'flatly', 'journal', 'litera', 'lumen', 'minty', 
                'pulse', 'sandstone', 'united', 'yeti', 'morph', 'simplex',
                'cerulean', 'spacelab', 'default'
            }
            
            dark_themes = {
                'cyborg', 'darkly', 'slate', 'solar', 'superhero', 'vapor',
                'quartz', 'theme'
            }
            
            # Determine if current theme is dark or light
            if current_theme in dark_themes:
                return {
                    'text': 'white',
                    'grid': 'lightgray',
                    'line': 'white'
                }
            else:  # Default to light theme colors
                return {
                    'text': 'black',
                    'grid': 'gray',
                    'line': 'black'
                }
        except:
            # Fallback to light theme colors if detection fails
            return {
                'text': 'black',
                'grid': 'gray', 
                'line': 'black'
            }
    
    def setup_ui(self):
        """Setup the viewer UI"""
        # Create toolbar frame
        toolbar_frame = tb.Frame(self.window)
        toolbar_frame.pack(side="top", fill="x", padx=5, pady=5)
        
        # Create figure for plotting with transparent background
        self.fig = Figure(figsize=(10, 6), facecolor='none', edgecolor='none')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('none')
        
        # Get theme colors
        theme_colors = self.get_theme_colors()
        
        # Extract data
        wavenumber = self.spectrum_df['Wavenumber'].values
        wavelength = 10000 / wavenumber
        emissivity = self.spectrum_df['Emissivity'].values
        uncertainty = self.spectrum_df['Uncertainty'].values
        
        # Plot data
        self.ax.plot(wavelength, emissivity, linewidth=2, label=self.spectrum_name)
        self.ax.errorbar(wavelength, emissivity, yerr=uncertainty, alpha=0.3)
        
        # Apply theme-aware styling
        self.ax.set_xlabel('Wavelength (μm)', fontsize=12, color=theme_colors['text'])
        self.ax.set_ylabel('Emissivity', fontsize=12, color=theme_colors['text'])
        self.ax.set_title(f'Spectrum: {self.spectrum_name}', fontsize=14, color=theme_colors['text'])
        self.ax.grid(True, alpha=0.3, color=theme_colors['grid'])
        self.ax.tick_params(colors=theme_colors['text'])
        self.ax.legend()
        
        # Add wavenumber on secondary x-axis
        self.ax2 = self.ax.twiny()
        self.ax2.set_xlim(self.ax.get_xlim())
        self.ax2.set_xlabel('Wavenumber (cm$^{-1}$)', fontsize=12, color=theme_colors['text'])
        self.ax2.tick_params(colors=theme_colors['text'])
        
        wavelength_ticks = np.linspace(min(wavelength), max(wavelength), num=5)
        wavenumber_ticks = 10000 / wavelength_ticks
        self.ax2.set_xticks(wavelength_ticks)
        self.ax2.set_xticklabels([f"{wn:.0f}" for wn in wavenumber_ticks])
        
        # Normal x-axis direction (wavelength increases left to right)
        
        # Create canvas for plotting
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Add custom buttons
        self.add_custom_buttons(toolbar_frame)
        
        # Bind events for interactive updates
        self.ax.callbacks.connect('xlim_changed', self.on_xlim_changed)
        
        # Add statistics panel
        self.add_statistics_panel()
    
    def add_custom_buttons(self, parent):
        """Add custom buttons to toolbar"""
        # Separator
        tb.Separator(parent, orient="vertical").pack(side="left", padx=10, fill="y")
        
        # Save button
        save_button = tb.Button(parent, text="Save Plot", 
                              command=self.save_plot)
        save_button.pack(side="left", padx=5)
        
        # Export data button
        export_button = tb.Button(parent, text="Export Data", 
                                command=self.export_data)
        export_button.pack(side="left", padx=5)
        
        # Close button
        close_button = tb.Button(parent, text="Close", 
                               command=self.window.destroy)
        close_button.pack(side="right", padx=5)
    
    def add_statistics_panel(self):
        """Add panel showing spectrum statistics"""
        stats_frame = tb.Labelframe(self.window, text="Spectrum Statistics", padding=10)
        stats_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        # Calculate statistics
        emissivity = self.spectrum_df['Emissivity'].values
        uncertainty = self.spectrum_df['Uncertainty'].values
        wavelength = 10000 / self.spectrum_df['Wavenumber'].values
        
        stats = {
            "Data points": len(emissivity),
            "Wavelength range": f"{wavelength.min():.2f} - {wavelength.max():.2f} μm",
            "Emissivity range": f"{emissivity.min():.4f} - {emissivity.max():.4f}",
            "Mean emissivity": f"{emissivity.mean():.4f}",
            "Std deviation": f"{emissivity.std():.4f}",
            "Mean uncertainty": f"{uncertainty.mean():.4f}"
        }
        
        # Display statistics in two columns
        stats_text = tb.Frame(stats_frame)
        stats_text.pack(fill="x")
        
        items = list(stats.items())
        mid = len(items) // 2
        
        # Left column
        left_frame = tb.Frame(stats_text)
        left_frame.pack(side="left", fill="x", expand=True)
        
        for label, value in items[:mid]:
            row = tb.Frame(left_frame)
            row.pack(fill="x", pady=2)
            tb.Label(row, text=f"{label}:", width=15, anchor="w").pack(side="left")
            tb.Label(row, text=value, bootstyle="info").pack(side="left")
        
        # Right column
        right_frame = tb.Frame(stats_text)
        right_frame.pack(side="left", fill="x", expand=True)
        
        for label, value in items[mid:]:
            row = tb.Frame(right_frame)
            row.pack(fill="x", pady=2)
            tb.Label(row, text=f"{label}:", width=15, anchor="w").pack(side="left")
            tb.Label(row, text=value, bootstyle="info").pack(side="left")
    
    def on_xlim_changed(self, event):
        """Update wavenumber axis when wavelength axis changes"""
        new_xlim = self.ax.get_xlim()
        self.ax2.set_xlim(new_xlim)
        
        # Create updated wavelength ticks within current view
        visible_wavelength = np.linspace(new_xlim[0], new_xlim[1], num=5)
        visible_wavenumber = 10000 / visible_wavelength
        
        # Update the wavenumber axis ticks
        self.ax2.set_xticks(visible_wavelength)
        self.ax2.set_xticklabels([f"{wn:.0f}" for wn in visible_wavenumber])
        
        # Redraw canvas
        self.canvas.draw_idle()
    
    def save_plot(self):
        """Save plot to file"""
        file_types = [
            ("PNG Image", "*.png"),
            ("PDF Document", "*.pdf"),
            ("SVG Image", "*.svg"),
            ("JPEG Image", "*.jpg")
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            initialfile=self.spectrum_name
        )
        
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save plot: {str(e)}")
    
    def export_data(self):
        """Export spectrum data to file"""
        file_types = [
            ("CSV file", "*.csv"),
            ("Text file", "*.txt")
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=file_types,
            initialfile=f"{self.spectrum_name}_data"
        )
        
        if file_path:
            try:
                # Add wavelength column
                export_df = self.spectrum_df.copy()
                export_df['Wavelength'] = 10000 / export_df['Wavenumber']
                
                # Reorder columns
                export_df = export_df[['Wavenumber', 'Wavelength', 'Emissivity', 'Uncertainty']]
                
                # Save to file
                if file_path.endswith('.csv'):
                    export_df.to_csv(file_path, index=False)
                else:
                    export_df.to_csv(file_path, sep='\t', index=False)
                
                messagebox.showinfo("Success", f"Data exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    def show(self):
        """Show the viewer window"""
        self.window.deiconify()
        self.window.focus_set()
