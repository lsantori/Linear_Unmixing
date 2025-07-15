"""
Results tab for the Mineral Spectra Analyzer
"""

import os
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import pandas as pd
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledFrame
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.interpolate import CubicSpline


class ResultsTab:
    """Results tab implementation"""
    
    def __init__(self, parent, status_callback, data_manager=None):
        self.parent = parent
        self.update_status = status_callback
        self.data_manager = data_manager
        
        # Create main frame
        self.frame = tb.Frame(parent)
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
                'quartz', 'theme'  # Add any custom dark themes
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
        """Setup the interactive results tab UI"""
        # Create notebook for results
        self.results_notebook = tb.Notebook(self.frame)
        self.results_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create placeholder tab
        placeholder = tb.Frame(self.results_notebook)
        self.results_notebook.add(placeholder, text="No Results")
        
        # Create centered message with better styling
        message_frame = tb.Frame(placeholder)
        message_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Icon-like visual element
        icon_frame = tb.Frame(message_frame)
        icon_frame.pack(pady=20)
        
        tb.Label(icon_frame, text="📊", font=("TkDefaultFont", 48)).pack()
        
        tb.Label(message_frame, 
                text="No Analysis Results Available",
                font=("TkDefaultFont", 16, "bold")).pack(pady=10)
        
        tb.Label(message_frame,
                text="Run a spectral unmixing analysis to view interactive results here",
                bootstyle="secondary", font=("TkDefaultFont", 11)).pack()
        
        # Quick actions frame
        actions_frame = tb.Frame(message_frame)
        actions_frame.pack(pady=20)
        
        tb.Label(actions_frame, text="Quick Actions:", 
                font=("TkDefaultFont", 10, "bold")).pack()
        
        tb.Button(actions_frame, text="Go to Analysis Tab", 
                 bootstyle="info-outline",
                 command=self.go_to_analysis).pack(pady=5)
    
    def go_to_analysis(self):
        """Switch to the analysis tab"""
        # Get the parent notebook and switch to analysis tab
        try:
            parent_notebook = self.frame.master.master  # Go up to main window
            parent_notebook.select(1)  # Index 1 is analysis tab
        except:
            pass  # Fail silently if we can't navigate
    
    def create_results_tab(self, algorithm, mineral, endmembers, abundances, errors, 
                          bestfit, reserror, meanspec, measurerr, wavenumber, RMS, 
                          maxwl=None, normalized_abundances=None, all_selected_endmembers=None,
                          mixed_spectrum_data=None, endmember_spectral_data=None):
        """Create an interactive results dashboard"""
        # Remove placeholder tab if it exists
        if len(self.results_notebook.tabs()) == 1 and \
           self.results_notebook.tab(0, "text") == "No Results":
            self.results_notebook.forget(0)
        
        # Store results data for this tab
        self.current_results = {
            'algorithm': algorithm,
            'mineral': mineral,
            'endmembers': endmembers,
            'abundances': abundances,
            'errors': errors,
            'bestfit': bestfit,
            'reserror': reserror,
            'meanspec': meanspec,
            'measurerr': measurerr,
            'wavenumber': wavenumber,
            'RMS': RMS,
            'maxwl': maxwl,
            'normalized_abundances': normalized_abundances,
            'all_selected_endmembers': all_selected_endmembers or endmembers,
            'mixed_spectrum_data': mixed_spectrum_data,
            'endmember_spectral_data': endmember_spectral_data
        }
        
        # Create a new tab frame
        result_tab = tb.Frame(self.results_notebook)
        tab_title = f"{algorithm}_{mineral}"
        self.results_notebook.add(result_tab, text=tab_title)
        self.results_notebook.select(self.results_notebook.index("end") - 1)
        
        # Create scrollable content inside the tab
        scrolled_frame = ScrolledFrame(result_tab, autohide=True)
        scrolled_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Main container
        main_container = scrolled_frame.container
        main_container.grid_columnconfigure(0, weight=1)
        
        # Configure rows for simplified layout - maximize spectral plots
        main_container.grid_rowconfigure(0, weight=0)  # Header (minimal)
        main_container.grid_rowconfigure(1, weight=0)  # Abundance table
        main_container.grid_rowconfigure(2, weight=3)  # Spectral plots (much larger)
        main_container.grid_rowconfigure(3, weight=0)  # Export section (minimal)
        
        # Create simplified dashboard
        self.create_dashboard_header(main_container, algorithm, mineral, RMS)
        self.create_abundance_table(main_container, algorithm, endmembers, abundances, errors, normalized_abundances)
        self.create_spectral_plots(main_container, mineral, algorithm, wavenumber, meanspec, bestfit, reserror, measurerr)
        self.create_export_section(main_container)
    
    def create_dashboard_header(self, parent, algorithm, mineral, RMS):
        """Create a compact header with essential information"""
        header_frame = tb.Labelframe(parent, text="Analysis Summary", padding=5)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=2)
        
        # Compact horizontal layout
        info_frame = tb.Frame(header_frame)
        info_frame.pack(fill="x")
        
        # Title and RMS in one line
        title_text = f"{algorithm} Analysis: {mineral}"
        tb.Label(info_frame, text=title_text, font=("TkDefaultFont", 12, "bold")).pack(side="left")
        
        # RMS info - more compact
        rms_color = "success" if RMS < 0.01 else "warning" if RMS < 0.05 else "danger"
        rms_text = f"RMS: {RMS:.4f}"
        tb.Label(info_frame, text=rms_text, bootstyle=rms_color, 
                font=("TkDefaultFont", 10)).pack(side="right")
    
    def create_abundance_table(self, parent, algorithm, endmembers, abundances, errors, normalized_abundances):
        """Create a simple abundance table"""
        table_frame = tb.Labelframe(parent, text="Mineral Abundances", padding=10)
        table_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Create table with headers
        headers = ["End-Member", "Abundance", "Error", "Relative Error (%)"]
        if algorithm == 'STO' and normalized_abundances is not None:
            headers.insert(-1, "Normalized")
        
        # Header row
        for i, header in enumerate(headers):
            tb.Label(table_frame, text=header, font=("TkDefaultFont", 10, "bold"), 
                    bootstyle="info").grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        # Data rows
        em_names = [str(em) for em in endmembers]
        for i, (em, abundance, error) in enumerate(zip(em_names, abundances, errors)):
            rel_error = (error / abundance * 100) if abundance > 0 else 0
            
            # End-member name
            tb.Label(table_frame, text=em).grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
            
            # Abundance
            tb.Label(table_frame, text=f"{abundance:.4f}").grid(row=i+1, column=1, padx=5, pady=2)
            
            # Error
            tb.Label(table_frame, text=f"±{error:.4f}").grid(row=i+1, column=2, padx=5, pady=2)
            
            # Normalized abundance (if STO)
            col_offset = 0
            if algorithm == 'STO' and normalized_abundances is not None:
                tb.Label(table_frame, text=f"{normalized_abundances[i]:.4f}").grid(
                    row=i+1, column=3, padx=5, pady=2)
                col_offset = 1
            
            # Relative error (color coded)
            rel_error_color = "success" if rel_error < 10 else "warning" if rel_error < 25 else "danger"
            tb.Label(table_frame, text=f"{rel_error:.1f}%", 
                    bootstyle=rel_error_color).grid(row=i+1, column=3+col_offset, padx=5, pady=2)
    
    
    def create_spectral_plots(self, parent, mineral, algorithm, wavenumber, meanspec, bestfit, reserror, measurerr):
        """Create interactive spectral plots"""
        try:
            plots_frame = tb.Labelframe(parent, text="Spectral Analysis", padding=15)
            plots_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
            plots_frame.grid_rowconfigure(0, weight=1)
            plots_frame.grid_columnconfigure(0, weight=1)
            
            print(f"Creating spectral plots for {mineral} using {algorithm}")
            print(f"Data shapes - wavenumber: {wavenumber.shape}, meanspec: {meanspec.shape}, bestfit: {bestfit.shape}")
            
            # Get theme-appropriate colors
            colors = self.get_theme_colors()
            
            # Create figure with subplots - even larger size for better visibility
            fig = Figure(figsize=(16, 12), dpi=80, facecolor='none', edgecolor='none')
            
            # Convert wavenumber to wavelength
            wavelength = 10000 / wavenumber
            
            # Adjust subplot spacing manually
            fig.subplots_adjust(left=0.08, bottom=0.1, right=0.95, top=0.92, wspace=0.25, hspace=0.35)
            
            # Main fit plot (spans top row)
            ax1 = fig.add_subplot(2, 2, (1, 2))
            ax1.set_facecolor('none')  # Transparent background
            ax1.plot(wavelength, meanspec, color=colors['line'], linewidth=2, label='Observed', alpha=0.8)
            ax1.plot(wavelength, bestfit, 'r-', linewidth=2, label='Model Fit')
            ax1.fill_between(wavelength, meanspec - measurerr, meanspec + measurerr, 
                            alpha=0.3, color='gray', label='Uncertainty')
            
            ax1.set_xlabel('Wavelength (μm)', fontsize=11, color=colors['text'])
            ax1.set_ylabel('Emissivity', fontsize=11, color=colors['text'])
            ax1.set_title(f'Spectral Fit: {algorithm} Analysis of {mineral}', fontsize=12, fontweight='bold', color=colors['text'])
            ax1.legend(fontsize=10)
            ax1.grid(True, alpha=0.3, color=colors['grid'])
            ax1.tick_params(colors=colors['text'])
            ax1.spines['bottom'].set_color(colors['line'])
            ax1.spines['top'].set_color(colors['line'])
            ax1.spines['left'].set_color(colors['line'])
            ax1.spines['right'].set_color(colors['line'])
            # Normal x-axis direction
            
            # Residual plot (bottom left)
            ax2 = fig.add_subplot(2, 2, 3)
            ax2.set_facecolor('none')  # Transparent background
            ax2.plot(wavelength, reserror, 'b-', linewidth=1, alpha=0.7)
            ax2.axhline(y=0, color=colors['line'], linestyle='--', alpha=0.5)
            ax2.fill_between(wavelength, -measurerr, measurerr, alpha=0.2, color='gray')
            
            ax2.set_xlabel('Wavelength (μm)', fontsize=11, color=colors['text'])
            ax2.set_ylabel('Residual', fontsize=11, color=colors['text'])
            ax2.set_title('Fit Residuals', fontsize=12, fontweight='bold', color=colors['text'])
            ax2.grid(True, alpha=0.3, color=colors['grid'])
            ax2.tick_params(colors=colors['text'])
            ax2.spines['bottom'].set_color(colors['line'])
            ax2.spines['top'].set_color(colors['line'])
            ax2.spines['left'].set_color(colors['line'])
            ax2.spines['right'].set_color(colors['line'])
            # Normal x-axis direction
            
            # Residual histogram (bottom right)
            ax3 = fig.add_subplot(2, 2, 4)
            ax3.set_facecolor('none')  # Transparent background
            n, bins, patches = ax3.hist(reserror, bins=20, alpha=0.7, color='blue', edgecolor=colors['line'])
            ax3.axvline(x=0, color=colors['line'], linestyle='--', alpha=0.5)
            ax3.axvline(x=np.mean(reserror), color='r', linestyle='-', alpha=0.7, label=f'Mean: {np.mean(reserror):.4f}')
            
            ax3.set_xlabel('Residual Value', fontsize=11, color=colors['text'])
            ax3.set_ylabel('Frequency', fontsize=11, color=colors['text'])
            ax3.set_title('Residual Distribution', fontsize=12, fontweight='bold', color=colors['text'])
            ax3.legend(fontsize=10)
            ax3.grid(True, alpha=0.3, color=colors['grid'])
            ax3.tick_params(colors=colors['text'])
            ax3.spines['bottom'].set_color(colors['line'])
            ax3.spines['top'].set_color(colors['line'])
            ax3.spines['left'].set_color(colors['line'])
            ax3.spines['right'].set_color(colors['line'])
            
            # Manual spacing is already set with subplots_adjust above
            
            # Add to GUI
            canvas = FigureCanvasTkAgg(fig, plots_frame)
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            canvas.draw()  # Explicitly draw the canvas
            
            # Add matplotlib toolbar
            toolbar_frame = tb.Frame(plots_frame)
            toolbar_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            
            # Store plot data for individual saving
            self.plot_data = {
                'wavelength': wavelength,
                'meanspec': meanspec,
                'bestfit': bestfit,
                'reserror': reserror,
                'measurerr': measurerr,
                'mineral': mineral,
                'algorithm': algorithm,
                'colors': colors
            }
            
            # Add custom save buttons for individual plots in separate frame below toolbar
            save_buttons_frame = tb.Frame(plots_frame)
            save_buttons_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
            self.add_individual_save_buttons(save_buttons_frame, fig, ax1, ax2, ax3, mineral, algorithm)
            
            print("✓ Spectral plots created successfully")
            
        except Exception as e:
            print(f"✗ Error creating spectral plots: {e}")
            import traceback
            traceback.print_exc()
            
            # Create error message frame
            error_frame = tb.Labelframe(parent, text="Spectral Analysis - Error", padding=15)
            error_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
            
            tb.Label(error_frame, text=f"Error creating plots: {str(e)}", 
                    bootstyle="danger").pack(pady=10)
    
    def add_individual_save_buttons(self, save_frame, fig, ax1, ax2, ax3, mineral, algorithm):
        """Add individual save buttons for each plot"""
        # Add a label for the save section
        tb.Label(save_frame, text="Save Individual Plots:", 
                font=("TkDefaultFont", 9, "bold")).pack(side="left", padx=(5, 10))
        
        # Individual plot save buttons
        tb.Button(save_frame, text="Save Spectral Fit", 
                 bootstyle="info-outline", 
                 command=lambda: self.save_spectral_fit_plot(f"{mineral}_{algorithm}_spectral_fit")).pack(side="left", padx=2)
        
        tb.Button(save_frame, text="Save Residuals", 
                 bootstyle="info-outline",
                 command=lambda: self.save_residuals_plot(f"{mineral}_{algorithm}_residuals")).pack(side="left", padx=2)
        
        tb.Button(save_frame, text="Save Histogram", 
                 bootstyle="info-outline",
                 command=lambda: self.save_histogram_plot(f"{mineral}_{algorithm}_histogram")).pack(side="left", padx=2)
        
        # Save all plots button with separator
        tb.Separator(save_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        tb.Button(save_frame, text="Save All Plots", 
                 bootstyle="success-outline",
                 command=lambda: self.save_all_individual_plots(fig, ax1, ax2, ax3, mineral, algorithm)).pack(side="left", padx=5)
    
    def save_spectral_fit_plot(self, default_filename):
        """Save the spectral fit plot"""
        from tkinter import filedialog, messagebox
        
        if not hasattr(self, 'plot_data'):
            messagebox.showerror("Error", "No plot data available")
            return
            
        file_types = [
            ("PNG Image", "*.png"),
            ("PDF Document", "*.pdf"), 
            ("SVG Image", "*.svg"),
            ("JPEG Image", "*.jpg")
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            initialfile=default_filename
        )
        
        if file_path:
            try:
                data = self.plot_data
                fig = Figure(figsize=(10, 6), dpi=300)
                ax = fig.add_subplot(111)
                
                # Recreate spectral fit plot
                ax.plot(data['wavelength'], data['meanspec'], color='black', linewidth=2, label='Observed', alpha=0.8)
                ax.plot(data['wavelength'], data['bestfit'], 'r-', linewidth=2, label='Model Fit')
                ax.fill_between(data['wavelength'], 
                               data['meanspec'] - data['measurerr'], 
                               data['meanspec'] + data['measurerr'], 
                               alpha=0.3, color='gray', label='Uncertainty')
                
                ax.set_xlabel('Wavelength (μm)', fontsize=12)
                ax.set_ylabel('Emissivity', fontsize=12)
                ax.set_title(f'Spectral Fit: {data["algorithm"]} Analysis of {data["mineral"]}', fontsize=14, fontweight='bold')
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3)
                
                fig.tight_layout()
                fig.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                
                messagebox.showinfo("Success", f"Spectral Fit Plot saved to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save Spectral Fit Plot: {str(e)}")
    
    def save_residuals_plot(self, default_filename):
        """Save the residuals plot"""
        from tkinter import filedialog, messagebox
        
        if not hasattr(self, 'plot_data'):
            messagebox.showerror("Error", "No plot data available")
            return
            
        file_types = [
            ("PNG Image", "*.png"),
            ("PDF Document", "*.pdf"), 
            ("SVG Image", "*.svg"),
            ("JPEG Image", "*.jpg")
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            initialfile=default_filename
        )
        
        if file_path:
            try:
                data = self.plot_data
                fig = Figure(figsize=(8, 6), dpi=300)
                ax = fig.add_subplot(111)
                
                # Recreate residuals plot
                ax.plot(data['wavelength'], data['reserror'], 'b-', linewidth=1, alpha=0.7)
                ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                ax.fill_between(data['wavelength'], -data['measurerr'], data['measurerr'], alpha=0.2, color='gray')
                
                ax.set_xlabel('Wavelength (μm)', fontsize=12)
                ax.set_ylabel('Residual', fontsize=12)
                ax.set_title('Fit Residuals', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                fig.tight_layout()
                fig.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                
                messagebox.showinfo("Success", f"Residuals Plot saved to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save Residuals Plot: {str(e)}")
    
    def save_histogram_plot(self, default_filename):
        """Save the histogram plot"""
        from tkinter import filedialog, messagebox
        
        if not hasattr(self, 'plot_data'):
            messagebox.showerror("Error", "No plot data available")
            return
            
        file_types = [
            ("PNG Image", "*.png"),
            ("PDF Document", "*.pdf"), 
            ("SVG Image", "*.svg"),
            ("JPEG Image", "*.jpg")
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            initialfile=default_filename
        )
        
        if file_path:
            try:
                data = self.plot_data
                fig = Figure(figsize=(8, 6), dpi=300)
                ax = fig.add_subplot(111)
                
                # Recreate histogram plot
                n, bins, patches = ax.hist(data['reserror'], bins=20, alpha=0.7, color='blue', edgecolor='black')
                ax.axvline(x=0, color='black', linestyle='--', alpha=0.5)
                ax.axvline(x=np.mean(data['reserror']), color='r', linestyle='-', alpha=0.7, 
                          label=f'Mean: {np.mean(data["reserror"]):.4f}')
                
                ax.set_xlabel('Residual Value', fontsize=12)
                ax.set_ylabel('Frequency', fontsize=12)
                ax.set_title('Residual Distribution', fontsize=14, fontweight='bold')
                ax.legend(fontsize=11)
                ax.grid(True, alpha=0.3)
                
                fig.tight_layout()
                fig.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                
                messagebox.showinfo("Success", f"Residual Histogram saved to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save Residual Histogram: {str(e)}")
    
    def save_all_individual_plots(self, fig, ax1, ax2, ax3, mineral, algorithm):
        """Save all individual plots at once"""
        from tkinter import filedialog, messagebox
        import os
        
        if not hasattr(self, 'plot_data'):
            messagebox.showerror("Error", "No plot data available")
            return
        
        # Ask user for directory
        directory = filedialog.askdirectory(
            title="Select directory to save all plots"
        )
        
        if directory:
            try:
                data = self.plot_data
                saved_files = []
                
                # Save spectral fit plot
                filename = f"{mineral}_{algorithm}_spectral_fit.png"
                file_path = os.path.join(directory, filename)
                fig1 = Figure(figsize=(10, 6), dpi=300)
                ax1 = fig1.add_subplot(111)
                ax1.plot(data['wavelength'], data['meanspec'], color='black', linewidth=2, label='Observed', alpha=0.8)
                ax1.plot(data['wavelength'], data['bestfit'], 'r-', linewidth=2, label='Model Fit')
                ax1.fill_between(data['wavelength'], data['meanspec'] - data['measurerr'], 
                               data['meanspec'] + data['measurerr'], alpha=0.3, color='gray', label='Uncertainty')
                ax1.set_xlabel('Wavelength (μm)', fontsize=12)
                ax1.set_ylabel('Emissivity', fontsize=12)
                ax1.set_title(f'Spectral Fit: {data["algorithm"]} Analysis of {data["mineral"]}', fontsize=14, fontweight='bold')
                ax1.legend(fontsize=11)
                ax1.grid(True, alpha=0.3)
                fig1.tight_layout()
                fig1.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                saved_files.append(filename)
                
                # Save residuals plot
                filename = f"{mineral}_{algorithm}_residuals.png"
                file_path = os.path.join(directory, filename)
                fig2 = Figure(figsize=(8, 6), dpi=300)
                ax2 = fig2.add_subplot(111)
                ax2.plot(data['wavelength'], data['reserror'], 'b-', linewidth=1, alpha=0.7)
                ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                ax2.fill_between(data['wavelength'], -data['measurerr'], data['measurerr'], alpha=0.2, color='gray')
                ax2.set_xlabel('Wavelength (μm)', fontsize=12)
                ax2.set_ylabel('Residual', fontsize=12)
                ax2.set_title('Fit Residuals', fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3)
                fig2.tight_layout()
                fig2.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                saved_files.append(filename)
                
                # Save histogram plot
                filename = f"{mineral}_{algorithm}_histogram.png"
                file_path = os.path.join(directory, filename)
                fig3 = Figure(figsize=(8, 6), dpi=300)
                ax3 = fig3.add_subplot(111)
                n, bins, patches = ax3.hist(data['reserror'], bins=20, alpha=0.7, color='blue', edgecolor='black')
                ax3.axvline(x=0, color='black', linestyle='--', alpha=0.5)
                ax3.axvline(x=np.mean(data['reserror']), color='r', linestyle='-', alpha=0.7, 
                          label=f'Mean: {np.mean(data["reserror"]):.4f}')
                ax3.set_xlabel('Residual Value', fontsize=12)
                ax3.set_ylabel('Frequency', fontsize=12)
                ax3.set_title('Residual Distribution', fontsize=14, fontweight='bold')
                ax3.legend(fontsize=11)
                ax3.grid(True, alpha=0.3)
                fig3.tight_layout()
                fig3.savefig(file_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
                saved_files.append(filename)
                
                messagebox.showinfo("Success", 
                                  f"All plots saved successfully to:\n{directory}\n\n" +
                                  "Files created:\n" + "\n".join(saved_files))
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save plots: {str(e)}")
    
    def create_export_section(self, parent):
        """Create minimal export section"""
        export_frame = tb.Labelframe(parent, text="Export", padding=3)
        export_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=2)
        
        # Compact button layout
        button_frame = tb.Frame(export_frame)
        button_frame.pack(fill="x")
        
        # Smaller buttons
        tb.Button(button_frame, text="Export Excel", 
                 bootstyle="success-outline", command=self.export_to_excel).pack(side="left", padx=3)
        
        tb.Button(button_frame, text="Copy Summary", 
                 bootstyle="secondary-outline", command=self.copy_summary).pack(side="left", padx=3)
    
    def export_to_excel(self):
        """Export comprehensive results to Excel file with all spectral data"""
        if not hasattr(self, 'current_results'):
            messagebox.showwarning("Warning", "No results to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
            initialfile=f"{self.current_results['algorithm']}_{self.current_results['mineral']}_results"
        )
        
        if file_path:
            try:
                results = self.current_results
                
                # Create summary data with additional info
                summary_data = {
                    'Algorithm': [results['algorithm']],
                    'Mixed_Sample': [results['mineral']],
                    'RMS_Error': [results['RMS']],
                    'Max_Wavelength_Filter': [results.get('maxwl', 'None')],
                    'Total_Selected_EndMembers': [len(results.get('all_selected_endmembers', []))],
                    'EndMembers_Used_in_Fit': [len(results['endmembers'])],
                    'Analysis_Date': [pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
                }
                
                # Create comprehensive abundance data showing ALL selected end-members
                all_selected = results.get('all_selected_endmembers', results['endmembers'])
                fitted_endmembers = [str(em) for em in results['endmembers']]
                
                abundance_data = {
                    'End_Member': [],
                    'Selected_for_Analysis': [],
                    'Used_in_Final_Fit': [],
                    'Abundance': [],
                    'Error': [],
                    'Relative_Error_Percent': []
                }
                
                if results['normalized_abundances'] is not None:
                    abundance_data['Normalized_Abundance'] = []
                
                # Add all selected end-members, even those not used
                for em in all_selected:
                    em_str = str(em)
                    abundance_data['End_Member'].append(em_str)
                    abundance_data['Selected_for_Analysis'].append('Yes')
                    
                    if em_str in fitted_endmembers:
                        # This end-member was used in the fit
                        idx = fitted_endmembers.index(em_str)
                        abundance_data['Used_in_Final_Fit'].append('Yes')
                        abundance_data['Abundance'].append(results['abundances'][idx])
                        abundance_data['Error'].append(results['errors'][idx])
                        rel_error = (results['errors'][idx] / results['abundances'][idx] * 100) if results['abundances'][idx] > 0 else 0
                        abundance_data['Relative_Error_Percent'].append(rel_error)
                        
                        if results['normalized_abundances'] is not None:
                            abundance_data['Normalized_Abundance'].append(results['normalized_abundances'][idx])
                    else:
                        # This end-member was selected but not used (zero abundance)
                        abundance_data['Used_in_Final_Fit'].append('No (Zero Abundance)')
                        abundance_data['Abundance'].append(0.0)
                        abundance_data['Error'].append(0.0)
                        abundance_data['Relative_Error_Percent'].append(0.0)
                        
                        if results['normalized_abundances'] is not None:
                            abundance_data['Normalized_Abundance'].append(0.0)
                
                # Create spectral data for the mixed sample
                wavelength = 10000 / results['wavenumber']
                mixed_spectral_data = {
                    'Wavenumber': results['wavenumber'].tolist(),
                    'Wavelength': wavelength.tolist(),
                    'Observed_Emissivity': results['meanspec'].tolist(),
                    'Model_Fit': results['bestfit'].tolist(),
                    'Residual': results['reserror'].tolist(),
                    'Uncertainty': results['measurerr'].tolist()
                }
                
                # Save to Excel or CSV
                if file_path.endswith('.xlsx'):
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        # Main results sheets
                        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                        pd.DataFrame(abundance_data).to_excel(writer, sheet_name='Abundances', index=False)
                        pd.DataFrame(mixed_spectral_data).to_excel(writer, sheet_name='Mixed_Spectrum', index=False)
                        
                        # Add individual end-member spectra if available
                        if results.get('mixed_spectrum_data') is not None:
                            # Original mixed spectrum (before any filtering)
                            mixed_original = results['mixed_spectrum_data'].copy()
                            mixed_original['Wavelength'] = 10000 / mixed_original['Wavenumber']
                            mixed_original = mixed_original[['Wavenumber', 'Wavelength', 'Emissivity', 'Uncertainty']]
                            mixed_original.to_excel(writer, sheet_name='Mixed_Original_Full', index=False)
                        
                        # Add individual end-member spectra
                        self._export_endmember_spectra(writer, results)
                        
                else:
                    # For CSV, save abundance data only
                    pd.DataFrame(abundance_data).to_csv(file_path, index=False)
                
                messagebox.showinfo("Success", f"Comprehensive results exported to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def _export_endmember_spectra(self, writer, results):
        """Export individual end-member spectra to separate Excel sheets"""
        try:
            all_selected = results.get('all_selected_endmembers', [])
            
            for i, em_name in enumerate(all_selected):
                try:
                    # Load the original end-member spectrum from file
                    em_file = os.path.join("spectral/spectral_library", f"{em_name}.txt")
                    if os.path.exists(em_file):
                        # Use the data manager if available
                        if self.data_manager:
                            em_df = self.data_manager.load_spectrum(em_file)
                        else:
                            # Fallback: load directly
                            em_df = pd.read_csv(em_file, sep='\t')
                        
                        # Add wavelength column
                        em_df['Wavelength'] = 10000 / em_df['Wavenumber']
                        em_df = em_df[['Wavenumber', 'Wavelength', 'Emissivity', 'Uncertainty']]
                        
                        # Create safe sheet name (Excel has 31 char limit)
                        sheet_name = f"EM_{em_name}"[:31]
                        em_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                except Exception as e:
                    print(f"Warning: Could not export end-member {em_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Could not export end-member spectra: {e}")
    
    def export_plots_pdf(self):
        """Export plots as PDF"""
        messagebox.showinfo("Info", "PDF export feature coming soon!")
    
    def copy_summary(self):
        """Copy analysis summary to clipboard"""
        if not hasattr(self, 'current_results'):
            messagebox.showwarning("Warning", "No results to copy")
            return
        
        try:
            results = self.current_results
            
            # Create summary text
            summary_text = f"""Analysis Results Summary
=====================================

Algorithm: {results['algorithm']}
Sample: {results['mineral']}
Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
RMS Error: {results['RMS']:.6f}

Abundance Results:
"""
            
            for i, (em, abundance, error) in enumerate(zip(results['endmembers'], 
                                                          results['abundances'], 
                                                          results['errors'])):
                rel_error = (error / abundance * 100) if abundance > 0 else 0
                summary_text += f"  {em}: {abundance:.4f} ± {error:.4f} ({rel_error:.1f}%)\n"
            
            if results['normalized_abundances'] is not None:
                summary_text += "\nNormalized Abundances:\n"
                for em, norm_ab in zip(results['endmembers'], results['normalized_abundances']):
                    summary_text += f"  {em}: {norm_ab:.4f}\n"
            
            # Copy to clipboard
            self.frame.clipboard_clear()
            self.frame.clipboard_append(summary_text)
            messagebox.showinfo("Success", "Summary copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy summary: {str(e)}")
    
    def create_plot(self, parent, mineral, algorithm, wavenumber, meanspec, 
                   bestfit, reserror, measurerr, RMS):
        """Create the spectral fit plot"""
        # Create figure for plotting
        fig = Figure(figsize=(6, 6))
        
        # Create subplots
        ax = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax)
        
        # Convert wavenumber to wavelength
        X_wavenumber = wavenumber
        X_wavelength = 10000 / X_wavenumber
        Y = bestfit
        RMS_str = "{:.4E}".format(RMS)

        # Plot data
        ax.plot(X_wavelength, meanspec, label=mineral, linewidth=2)
        ax.plot(X_wavelength, Y, 'r--', label=algorithm)
        ax.errorbar(X_wavelength, meanspec, yerr=measurerr, lw=1, c='c', alpha=0.5)
        ax.set_ylabel('Effective Emissivity', fontsize=12)
        ax.legend()
        # Normal x-axis direction
        ax.tick_params(labelbottom=False)

        ax2.plot(X_wavelength, reserror, c='k')
        ax2.axhline(y=0, linestyle='--', color='k', alpha=0.4)
        ax2.set_xlabel('Wavelength ($\mu$ m)', fontsize=12)
        ax2.set_ylabel('Residual Error', fontsize=12)
        ax2.invert_xaxis()
        ax2.text(0.05, 0.9, f'RMS error: {RMS_str}', transform=ax2.transAxes)

        # Wavenumber twin axis
        ax3 = ax.twiny()
        ax3.set_xlim(ax.get_xlim())
        ax3.set_xlabel('Wavenumber (cm$^{-1}$)', fontsize=12)
        wavelength_ticks = np.linspace(X_wavelength.min(), X_wavelength.max(), num=5)
        wavenumber_ticks = 10000 / wavelength_ticks
        ax3.set_xticks(wavelength_ticks)
        ax3.set_xticklabels([f"{wn:.0f}" for wn in wavenumber_ticks])
        # Normal x-axis direction

        fig.tight_layout()
        ax.spines['bottom'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        
        # Create distinct frames for canvas and toolbar
        canvas_frame = tb.Frame(parent)
        canvas_frame.pack(fill="both", expand=True)
        
        toolbar_frame = tb.Frame(parent)
        toolbar_frame.pack(fill="x", side="bottom")
        
        # Create canvas for plotting
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Store references for export functionality
        self.current_fig = fig
        self.current_mineral = mineral
        self.current_algorithm = algorithm
        
        # Create and configure the navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        toolbar.pack(side="left", fill="x", expand=True)
        
        # Function to update wavenumber axis when zooming or panning
        def on_xlim_changed(event):
            new_xlim = ax.get_xlim()
            ax3.set_xlim(new_xlim)
            
            # Create updated wavelength ticks within current view
            visible_wavelength = np.linspace(new_xlim[0], new_xlim[1], num=5)
            visible_wavenumber = 10000 / visible_wavelength
            
            # Update the wavenumber axis ticks
            ax3.set_xticks(visible_wavelength)
            ax3.set_xticklabels([f"{wn:.0f}" for wn in visible_wavenumber])
            
            # Redraw canvas
            canvas.draw_idle()
        
        # Connect the event handler for axis limits changing
        ax.callbacks.connect('xlim_changed', on_xlim_changed)
        
        # Function to save the current view of the plot
        def save_current_view():
            # Get the current figure's state with zoom/pan applied
            fig.tight_layout()  # Adjust the layout to ensure everything fits
            
            # Open file dialog to get save location and format
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("PDF Document", "*.pdf"),
                    ("SVG Image", "*.svg"),
                    ("JPEG Image", "*.jpg")
                ],
                initialfile=f"{mineral}_{algorithm}_plot"
            )
            
            if file_path:
                try:
                    # Save the figure with current zoom level and high DPI
                    fig.savefig(file_path, dpi=300, bbox_inches='tight')
                    messagebox.showinfo("Success", f"Plot saved to:\n{file_path}")
                    self.update_status(f"Plot saved to: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Save Error", f"Failed to save plot: {str(e)}")
        
        # Add custom save button next to the toolbar
        save_button = tb.Button(toolbar_frame, text="Save Current View", 
                              command=save_current_view)
        save_button.pack(side="right", padx=5)
        
        # Add help label below the toolbar
        help_frame = tb.Frame(parent)
        help_frame.pack(fill="x", side="bottom")
        help_label = tb.Label(help_frame, 
                            text="Use toolbar to zoom (magnifying glass), pan (hand), " +
                                 "and reset view (home)",
                            bootstyle="secondary")
        help_label.pack(pady=2)
    
    def create_wls_table(self, parent, endmembers, abundances, errors):
        """Create a table for WLS results"""
        # Create Treeview for table
        columns = ("end_member", "abundance", "error")
        
        self.results_tv = tb.Treeview(
            parent,
            columns=columns,
            show="headings",
            bootstyle="info",
            height=min(10, len(endmembers))
        )
        
        # Configure columns and headings
        self.results_tv.column("end_member", width=150, anchor="w")
        self.results_tv.column("abundance", width=100, anchor="center")
        self.results_tv.column("error", width=100, anchor="center")
        
        self.results_tv.heading("end_member", text="End Member")
        self.results_tv.heading("abundance", text="Abundance")
        self.results_tv.heading("error", text="Error")
        
        # Add scrollbars
        y_scrollbar = tb.Scrollbar(parent, orient="vertical", command=self.results_tv.yview)
        self.results_tv.configure(yscrollcommand=y_scrollbar.set)
        
        # Grid layout
        self.results_tv.pack(fill="both", expand=True, side="left")
        y_scrollbar.pack(fill="y", side="right")
        
        # Add data rows
        for i, (em, abund, err) in enumerate(zip(endmembers, abundances, errors)):
            self.results_tv.insert("", "end", values=(em, f"{abund:.4f}", f"{err:.4f}"))
            
        # Add total row if more than one end member
        if len(endmembers) > 1:
            self.results_tv.insert("", "end", values=("", "", ""))
            self.results_tv.insert("", "end", values=("TOTAL", f"{np.sum(abundances):.4f}", ""))
    
    def create_sto_table(self, parent, endmembers, abundances, norm_abundances, errors):    
        """Create a table for STO results"""
        # Create Treeview for table
        columns = ("end_member", "abundance", "normalized", "error")
        
        self.results_tv = tb.Treeview(
            parent,
            columns=columns,
            show="headings",
            bootstyle="info"
        )
        
        # Configure columns and headings
        self.results_tv.column("end_member", width=150, anchor="w")
        self.results_tv.column("abundance", width=100, anchor="center")
        self.results_tv.column("normalized", width=100, anchor="center")
        self.results_tv.column("error", width=100, anchor="center")
        
        self.results_tv.heading("end_member", text="End Member")
        self.results_tv.heading("abundance", text="Abundance")
        self.results_tv.heading("normalized", text="Normalized")
        self.results_tv.heading("error", text="Error")
        
        # Add scrollbars
        y_scrollbar = tb.Scrollbar(parent, orient="vertical", command=self.results_tv.yview)
        self.results_tv.configure(yscrollcommand=y_scrollbar.set)
        
        # Grid layout
        self.results_tv.pack(fill="both", expand=True, side="left")
        y_scrollbar.pack(fill="y", side="right")
        
        # Add data rows
        for i, (em, abund, norm, err) in enumerate(zip(endmembers, abundances, 
                                                       norm_abundances, errors)):
            self.results_tv.insert("", "end", 
                                 values=(em, f"{abund:.4f}", f"{norm:.4f}", f"{err:.4f}"))
            
        # Add total row
        self.results_tv.insert("", "end", values=("", "", "", ""))
        self.results_tv.insert("", "end", 
                             values=("TOTAL", f"{np.sum(abundances):.4f}", "1.0000", ""))
    
    def export_results(self):
        """Export results from currently selected tab"""
        # Check if we have results
        if len(self.results_notebook.tabs()) == 0 or \
           (len(self.results_notebook.tabs()) == 1 and 
            self.results_notebook.tab(0, "text") == "No Results"):
            messagebox.showwarning("Export", "No results available to export")
            return
            
        # Get current tab
        current_tab_id = self.results_notebook.select()
        if not current_tab_id:
            messagebox.showwarning("Export", "No results tab selected")
            return
        
        # Get tab name which contains algorithm and mineral name
        tab_text = self.results_notebook.tab(current_tab_id, "text")
        algorithm, mineral_name = tab_text.split("_", 1) if "_" in tab_text else (tab_text, "Unknown")
        
        # Prompt user for export format
        export_dialog = ExportDialog(self.frame.winfo_toplevel(), mineral_name, algorithm)
        export_options = export_dialog.show()
        
        if export_options:
            self.execute_export(mineral_name, algorithm, export_options['format'], 
                              export_options['include_spectra'])
    
    def execute_export(self, mineral_name, algorithm, export_format, include_spectra):
        """Execute the export operation with the selected options"""
        file_types = [
            ("CSV file", "*.csv"),
            ("Text file", "*.txt")
        ]
        
        file_extension = f".{export_format}"
        file_path = filedialog.asksaveasfilename(
            defaultextension=file_extension,
            filetypes=file_types,
            initialfile=f"{mineral_name}_{algorithm}_results"
        )
        
        if not file_path:
            return
        
        try:
            # Export simple results for now
            # In the full implementation, this would export all data including spectra
            with open(file_path, 'w') as f:
                f.write(f"Name: {mineral_name}\n")
                f.write(f"Algorithm: {algorithm}\n")
                f.write(f"Export successful\n")
            
            messagebox.showinfo("Success", f"Results saved to: {file_path}")
            self.update_status(f"Results exported to: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
            self.update_status("Export failed")


class ExportDialog:
    """Dialog for export options"""
    
    def __init__(self, parent, mineral_name, algorithm):
        self.parent = parent
        self.mineral_name = mineral_name
        self.algorithm = algorithm
        self.result = None
        
        self.dialog = tb.Toplevel(parent)
        self.dialog.title("Export Options")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        # Center content
        content_frame = tb.Frame(self.dialog)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tb.Label(content_frame, text="Select Export Options:", 
                font=("TkDefaultFont", 12)).pack(pady=10)
        
        # Export options
        self.format_var = tk.StringVar(value="csv")
        tb.Label(content_frame, text="File Format:").pack(anchor="w", pady=(10, 5))
        tb.Radiobutton(content_frame, text="CSV (.csv)", 
                      variable=self.format_var, value="csv").pack(anchor="w", padx=20)
        tb.Radiobutton(content_frame, text="Text (.txt)", 
                      variable=self.format_var, value="txt").pack(anchor="w", padx=20)
        
        # Advanced options
        self.include_spectra_var = tk.BooleanVar(value=True)
        tb.Checkbutton(content_frame, text="Include model and endmember spectra", 
                      variable=self.include_spectra_var).pack(anchor="w", pady=(10, 5))
        
        # Buttons
        button_frame = tb.Frame(content_frame)
        button_frame.pack(pady=15, fill="x")
        
        tb.Button(button_frame, text="Export", bootstyle="success", 
                 command=self.on_export).pack(side="left", padx=10)
        tb.Button(button_frame, text="Cancel", 
                 command=self.on_cancel).pack(side="right", padx=10)
        
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def on_export(self):
        """Handle export button click"""
        self.result = {
            'format': self.format_var.get(),
            'include_spectra': self.include_spectra_var.get()
        }
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel button click"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.parent.wait_window(self.dialog)
        return self.result
