"""
Multi-spectrum viewer for comparing multiple spectra simultaneously
"""

import os
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import pandas as pd
import ttkbootstrap as tb
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.colors as mcolors


class MultiSpectrumViewer:
    """Window for viewing and comparing multiple spectra"""
    
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.loaded_spectra = {}  # Dictionary to store loaded spectra data
        self.color_cycle = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        self.color_index = 0
        
        # Create window
        self.window = tb.Toplevel(parent)
        self.window.title("Multi-Spectrum Viewer")
        self.window.geometry("1200x800")
        
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
        """Setup the multi-spectrum viewer UI"""
        # Create main paned window
        main_paned = tb.PanedWindow(self.window, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left panel - Spectrum selection and controls
        left_frame = tb.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Plot area
        right_frame = tb.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        self.setup_control_panel(left_frame)
        self.setup_plot_panel(right_frame)
    
    def setup_control_panel(self, parent):
        """Setup the control panel for spectrum selection"""
        # Available spectra section
        available_frame = tb.Labelframe(parent, text="Available Spectra", padding=10)
        available_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # End-member spectra
        em_frame = tb.Labelframe(available_frame, text="End-Members", padding=5)
        em_frame.pack(fill="x", pady=5)
        
        self.em_listbox = tk.Listbox(em_frame, height=6, selectmode="extended")
        self.em_listbox.pack(fill="x", pady=2)
        
        em_button_frame = tb.Frame(em_frame)
        em_button_frame.pack(fill="x", pady=2)
        tb.Button(em_button_frame, text="Add Selected", bootstyle="success",
                 command=lambda: self.add_spectra_from_list(self.em_listbox, "end_member")).pack(side="left", padx=2)
        
        # Mixed spectra
        mixed_frame = tb.Labelframe(available_frame, text="Mixed Spectra", padding=5)
        mixed_frame.pack(fill="x", pady=5)
        
        self.mixed_listbox = tk.Listbox(mixed_frame, height=4, selectmode="extended")
        self.mixed_listbox.pack(fill="x", pady=2)
        
        mixed_button_frame = tb.Frame(mixed_frame)
        mixed_button_frame.pack(fill="x", pady=2)
        tb.Button(mixed_button_frame, text="Add Selected", bootstyle="success",
                 command=lambda: self.add_spectra_from_list(self.mixed_listbox, "mixed")).pack(side="left", padx=2)
        
        # Loaded spectra section
        loaded_frame = tb.Labelframe(parent, text="Loaded Spectra", padding=10)
        loaded_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Loaded spectra tree with checkboxes for visibility
        columns = ("name", "type", "color", "visible")
        self.loaded_tv = tb.Treeview(loaded_frame, columns=columns, show="headings", height=8)
        
        self.loaded_tv.heading("name", text="Name")
        self.loaded_tv.heading("type", text="Type")
        self.loaded_tv.heading("color", text="Color")
        self.loaded_tv.heading("visible", text="Visible")
        
        self.loaded_tv.column("name", width=120)
        self.loaded_tv.column("type", width=80)
        self.loaded_tv.column("color", width=60)
        self.loaded_tv.column("visible", width=60)
        
        self.loaded_tv.pack(fill="both", expand=True, pady=2)
        
        # Double-click to toggle visibility
        self.loaded_tv.bind("<Double-1>", self.toggle_spectrum_visibility)
        
        # Control buttons
        control_frame = tb.Frame(loaded_frame)
        control_frame.pack(fill="x", pady=5)
        
        tb.Button(control_frame, text="Remove Selected", bootstyle="danger",
                 command=self.remove_selected_spectra).pack(side="left", padx=2)
        tb.Button(control_frame, text="Clear All", bootstyle="warning",
                 command=self.clear_all_spectra).pack(side="left", padx=2)
        tb.Button(control_frame, text="Refresh Lists", bootstyle="info",
                 command=self.refresh_available_spectra).pack(side="right", padx=2)
        
        # Plot controls
        plot_controls = tb.Labelframe(parent, text="Plot Controls", padding=10)
        plot_controls.pack(fill="x", padx=5, pady=5)
        
        # Normalization option
        self.normalize_var = tk.BooleanVar(value=False)
        tb.Checkbutton(plot_controls, text="Normalize spectra", 
                      variable=self.normalize_var,
                      command=self.update_plot).pack(anchor="w")
        
        # Offset option
        self.offset_var = tk.BooleanVar(value=False)
        tb.Checkbutton(plot_controls, text="Offset spectra vertically", 
                      variable=self.offset_var,
                      command=self.update_plot).pack(anchor="w")
        
        # Show uncertainties
        self.uncertainty_var = tk.BooleanVar(value=True)
        tb.Checkbutton(plot_controls, text="Show uncertainties", 
                      variable=self.uncertainty_var,
                      command=self.update_plot).pack(anchor="w")
        
        # Populate initial lists
        self.refresh_available_spectra()
    
    def setup_plot_panel(self, parent):
        """Setup the plot panel"""
        # Create matplotlib figure with transparent background
        self.fig = Figure(figsize=(10, 8), facecolor='none', edgecolor='none')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('none')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Add toolbar
        toolbar_frame = tb.Frame(parent)
        toolbar_frame.pack(side="bottom", fill="x")
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Custom toolbar buttons
        tb.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        
        tb.Button(toolbar_frame, text="Save Plot", 
                 command=self.save_plot).pack(side="left", padx=5)
        tb.Button(toolbar_frame, text="Export Data", 
                 command=self.export_data).pack(side="left", padx=5)
        
        # Initialize empty plot
        self.show_empty_plot()
    
    def show_empty_plot(self):
        """Show empty plot with instructions"""
        self.ax.clear()
        
        # Get theme colors
        theme_colors = self.get_theme_colors()
        
        self.ax.text(0.5, 0.5, 'Add spectra from the left panel to compare them', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=14, 
                    color='gray', style='italic')
        self.ax.set_xlabel('Wavelength (μm)', fontsize=12, color=theme_colors['text'])
        self.ax.set_ylabel('Emissivity', fontsize=12, color=theme_colors['text'])
        self.ax.set_title('Multi-Spectrum Comparison', fontsize=14, color=theme_colors['text'])
        self.ax.grid(True, alpha=0.3, color=theme_colors['grid'])
        self.ax.tick_params(colors=theme_colors['text'])
        self.canvas.draw()
    
    def refresh_available_spectra(self):
        """Refresh the available spectra lists"""
        # Clear existing lists
        self.em_listbox.delete(0, tk.END)
        self.mixed_listbox.delete(0, tk.END)
        
        # Refresh data manager
        self.data_manager.refresh_lists()
        
        # Populate end-member list
        for item in self.data_manager.end_member_list:
            self.em_listbox.insert(tk.END, item)
        
        # Populate mixed spectra list
        for item in self.data_manager.mixed_list:
            self.mixed_listbox.insert(tk.END, item)
    
    def add_spectra_from_list(self, listbox, spectra_type):
        """Add selected spectra from listbox to the comparison"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No spectra selected")
            return
        
        for index in selection:
            spectrum_name = listbox.get(index)
            self.add_spectrum(spectrum_name, spectra_type)
    
    def add_spectrum(self, name, spectra_type):
        """Add a spectrum to the comparison"""
        if name in self.loaded_spectra:
            messagebox.showinfo("Info", f"Spectrum '{name}' is already loaded")
            return
        
        try:
            # Determine folder and load spectrum
            folder = "spectral/spectral_library" if spectra_type == "end_member" else "spectral/mixed_pre_processed"
            file_path = os.path.join(folder, f"{name}.txt")
            spectrum_df = self.data_manager.load_spectrum(file_path)
            
            # Assign color
            color = self.color_cycle[self.color_index % len(self.color_cycle)]
            self.color_index += 1
            
            # Store spectrum data
            self.loaded_spectra[name] = {
                'data': spectrum_df,
                'type': spectra_type,
                'color': color,
                'visible': True
            }
            
            # Update loaded spectra tree
            self.update_loaded_tree()
            
            # Update plot
            self.update_plot()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load spectrum '{name}': {str(e)}")
    
    def update_loaded_tree(self):
        """Update the loaded spectra treeview"""
        # Clear existing items
        for item in self.loaded_tv.get_children():
            self.loaded_tv.delete(item)
        
        # Add loaded spectra
        for name, info in self.loaded_spectra.items():
            visibility = "✓" if info['visible'] else "✗"
            type_label = "End-Member" if info['type'] == "end_member" else "Mixed"
            
            self.loaded_tv.insert("", "end", values=(name, type_label, info['color'], visibility))
    
    def toggle_spectrum_visibility(self, event):
        """Toggle visibility of selected spectrum"""
        selection = self.loaded_tv.selection()
        if not selection:
            return
        
        item = selection[0]
        spectrum_name = self.loaded_tv.item(item, "values")[0]
        
        if spectrum_name in self.loaded_spectra:
            self.loaded_spectra[spectrum_name]['visible'] = not self.loaded_spectra[spectrum_name]['visible']
            self.update_loaded_tree()
            self.update_plot()
    
    def remove_selected_spectra(self):
        """Remove selected spectra from comparison"""
        selection = self.loaded_tv.selection()
        if not selection:
            messagebox.showwarning("Warning", "No spectra selected")
            return
        
        for item in selection:
            spectrum_name = self.loaded_tv.item(item, "values")[0]
            if spectrum_name in self.loaded_spectra:
                del self.loaded_spectra[spectrum_name]
        
        self.update_loaded_tree()
        self.update_plot()
    
    def clear_all_spectra(self):
        """Clear all loaded spectra"""
        if self.loaded_spectra and messagebox.askyesno("Confirm", "Remove all loaded spectra?"):
            self.loaded_spectra.clear()
            self.color_index = 0
            self.update_loaded_tree()
            self.show_empty_plot()
    
    def update_plot(self):
        """Update the comparison plot"""
        self.ax.clear()
        
        if not self.loaded_spectra:
            self.show_empty_plot()
            return
        
        # Get visible spectra
        visible_spectra = {name: info for name, info in self.loaded_spectra.items() if info['visible']}
        
        if not visible_spectra:
            # Get theme colors
            theme_colors = self.get_theme_colors()
            
            self.ax.text(0.5, 0.5, 'No visible spectra\nDouble-click items in the list to show/hide', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, 
                        color='gray', style='italic')
            self.ax.set_xlabel('Wavelength (μm)', fontsize=12, color=theme_colors['text'])
            self.ax.set_ylabel('Emissivity', fontsize=12, color=theme_colors['text'])
            self.ax.set_title('Multi-Spectrum Comparison', fontsize=14, color=theme_colors['text'])
            self.ax.grid(True, alpha=0.3, color=theme_colors['grid'])
            self.ax.tick_params(colors=theme_colors['text'])
            self.canvas.draw()
            return
        
        # Plot each visible spectrum
        offset_value = 0
        offset_increment = 0.1 if self.offset_var.get() else 0
        
        for i, (name, info) in enumerate(visible_spectra.items()):
            spectrum_df = info['data']
            color = info['color']
            
            # Extract data
            wavenumber = spectrum_df['Wavenumber'].values
            wavelength = 10000 / wavenumber
            emissivity = spectrum_df['Emissivity'].values
            uncertainty = spectrum_df['Uncertainty'].values
            
            # Apply normalization if requested
            if self.normalize_var.get():
                emissivity = (emissivity - emissivity.min()) / (emissivity.max() - emissivity.min())
                uncertainty = uncertainty / (spectrum_df['Emissivity'].max() - spectrum_df['Emissivity'].min())
            
            # Apply offset
            plot_emissivity = emissivity + offset_value
            plot_uncertainty = uncertainty
            
            # Plot spectrum
            line_style = '-' if info['type'] == 'end_member' else '--'
            label = f"{name} ({'EM' if info['type'] == 'end_member' else 'Mixed'})"
            
            self.ax.plot(wavelength, plot_emissivity, color=color, linewidth=2, 
                        linestyle=line_style, label=label)
            
            # Add uncertainties if requested
            if self.uncertainty_var.get():
                self.ax.fill_between(wavelength, 
                                   plot_emissivity - plot_uncertainty,
                                   plot_emissivity + plot_uncertainty,
                                   alpha=0.2, color=color)
            
            offset_value += offset_increment
        
        # Get theme colors for styling
        theme_colors = self.get_theme_colors()
        
        # Apply theme-aware styling
        self.ax.set_xlabel('Wavelength (μm)', fontsize=12, color=theme_colors['text'])
        ylabel = 'Normalized Emissivity' if self.normalize_var.get() else 'Emissivity'
        if self.offset_var.get():
            ylabel += ' (offset)'
        self.ax.set_ylabel(ylabel, fontsize=12, color=theme_colors['text'])
        self.ax.set_title('Multi-Spectrum Comparison', fontsize=14, color=theme_colors['text'])
        self.ax.grid(True, alpha=0.3, color=theme_colors['grid'])
        self.ax.tick_params(colors=theme_colors['text'])
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adjust layout
        self.fig.tight_layout()
        self.canvas.draw()
    
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
            initialfile="multi_spectrum_comparison"
        )
        
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save plot: {str(e)}")
    
    def export_data(self):
        """Export all loaded spectrum data to file"""
        if not self.loaded_spectra:
            messagebox.showwarning("Warning", "No spectra loaded")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("Excel file", "*.xlsx")],
            initialfile="multi_spectrum_data"
        )
        
        if file_path:
            try:
                # Combine all spectrum data
                combined_data = []
                
                for name, info in self.loaded_spectra.items():
                    spectrum_df = info['data'].copy()
                    spectrum_df['Spectrum_Name'] = name
                    spectrum_df['Spectrum_Type'] = info['type']
                    spectrum_df['Wavelength'] = 10000 / spectrum_df['Wavenumber']
                    combined_data.append(spectrum_df)
                
                if combined_data:
                    export_df = pd.concat(combined_data, ignore_index=True)
                    
                    # Reorder columns
                    columns = ['Spectrum_Name', 'Spectrum_Type', 'Wavenumber', 'Wavelength', 'Emissivity', 'Uncertainty']
                    export_df = export_df[columns]
                    
                    # Save to file
                    if file_path.endswith('.xlsx'):
                        export_df.to_excel(file_path, index=False)
                    else:
                        export_df.to_csv(file_path, index=False)
                    
                    messagebox.showinfo("Success", f"Data exported to:\n{file_path}")
                else:
                    messagebox.showwarning("Warning", "No data to export")
                    
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    def show(self):
        """Show the viewer window"""
        self.window.deiconify()
        self.window.focus_set()