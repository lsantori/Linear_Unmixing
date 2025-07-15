"""
Data management tab for the Mineral Spectra Analyzer
"""

import os
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import pandas as pd
import numpy as np
import ttkbootstrap as tb
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.spectrum_viewer import SpectrumViewer
from ui.multi_spectrum_viewer import MultiSpectrumViewer


class DataTab:
    """Data management tab implementation"""
    
    def __init__(self, parent, data_manager, status_callback):
        self.parent = parent
        self.data_manager = data_manager
        self.update_status = status_callback
        self.analysis_tab = None  # Reference to analysis tab for refresh notifications
        
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
    
    def set_analysis_tab(self, analysis_tab):
        """Set reference to analysis tab for refresh notifications"""
        self.analysis_tab = analysis_tab
    
    def setup_ui(self):
        """Setup the data management tab UI with preview panel"""
        # Configure grid - three columns: end-member, mixed, preview
        self.frame.grid_columnconfigure(0, weight=2)  # End-member list
        self.frame.grid_columnconfigure(1, weight=2)  # Mixed spectra list
        self.frame.grid_columnconfigure(2, weight=3)  # Preview panel
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Title frames for data lists
        end_member_frame = tb.Labelframe(self.frame, text="End-Member Spectra", padding=10)
        end_member_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        mixed_frame = tb.Labelframe(self.frame, text="Mixed Spectra", padding=10)
        mixed_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Preview panel
        preview_frame = tb.Labelframe(self.frame, text="Spectrum Preview", padding=10)
        preview_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Action buttons for end members
        tb.Button(end_member_frame, text="Import", bootstyle="success", 
                 command=lambda: self.add_spectra("end_member")).pack(side="left", padx=5)
        tb.Button(end_member_frame, text="Delete Selected", bootstyle="danger",
                 command=lambda: self.delete_spectra(self.spectral_tv)).pack(side="left", padx=5)
        
        # Action buttons for mixed spectra
        tb.Button(mixed_frame, text="Import", bootstyle="success",
                 command=lambda: self.add_spectra("unmix")).pack(side="left", padx=5)
        tb.Button(mixed_frame, text="Delete Selected", bootstyle="danger",
                 command=lambda: self.delete_spectra(self.mixed_tv)).pack(side="left", padx=5)
        
        # Data display frames
        self.create_data_treeview(self.frame, 1, 0, "end_member")
        self.create_data_treeview(self.frame, 1, 1, "mixed")
        
        # Create preview panel
        self.create_preview_panel(preview_frame)
    
    def create_data_treeview(self, parent, row, col, data_type):
        """Create a treeview for displaying data files with metadata"""
        # Frame for treeview
        frame = tb.Frame(parent)
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Create the treeview with appropriate columns
        columns = ("name", "date", "size", "status")
        if data_type == "end_member":
            self.spectral_tv = tv = tb.Treeview(
                frame,
                columns=columns,
                show="headings",
                bootstyle="info"
            )
        else:
            self.mixed_tv = tv = tb.Treeview(
                frame, 
                columns=columns,
                show="headings",
                bootstyle="info"
            )
        
        # Configure columns
        tv.column("name", width=150, stretch=True)
        tv.column("date", width=100)
        tv.column("size", width=80)
        tv.column("status", width=100)
        
        # Configure headings
        tv.heading("name", text="Name", anchor="w")
        tv.heading("date", text="Date Modified", anchor="w")
        tv.heading("size", text="Size", anchor="w")
        tv.heading("status", text="Status", anchor="w")
        
        # Add scrollbars
        x_scrollbar = tb.Scrollbar(frame, orient="horizontal", command=tv.xview)
        y_scrollbar = tb.Scrollbar(frame, orient="vertical", command=tv.yview)
        tv.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        
        # Grid layout
        tv.grid(row=0, column=0, sticky="nsew")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Populate with data
        self.populate_treeview(tv, data_type)
        
        # Add right-click menu
        self.add_context_menu(tv, data_type)
        
        # Bind selection event for preview
        tv.bind("<<TreeviewSelect>>", lambda e: self.on_spectrum_select(tv, data_type))
        
        return tv
    
    def populate_treeview(self, tv, data_type):
        """Populate treeview with file data"""
        # Clear existing items
        for i in tv.get_children():
            tv.delete(i)
        
        # Determine which folder to use
        if data_type == "end_member":
            folder = "spectral/spectral_library"
            items = self.data_manager.end_member_list
        else:
            folder = "spectral/mixed_pre_processed"
            items = self.data_manager.mixed_list
        
        # Add items
        for item in items:
            file_path = os.path.join(folder, f"{item}.txt")
            try:
                # Get file info
                file_stat = os.stat(file_path)
                file_size = f"{file_stat.st_size / 1024:.1f} KB"
                file_date = pd.Timestamp(file_stat.st_mtime, unit='s').strftime('%Y-%m-%d')
                
                # Insert into treeview
                tv.insert("", "end", values=(item, file_date, file_size, "Ready"))
            except Exception as e:
                tv.insert("", "end", values=(item, "Unknown", "Error", "Error"))
    
    def add_context_menu(self, tv, data_type):
        """Add right-click context menu to treeview"""
        context_menu = tk.Menu(tv, tearoff=0)
        
        if data_type == "end_member":
            context_menu.add_command(label="View Spectrum", 
                                   command=lambda: self.view_spectrum(tv, "end_member"))
            context_menu.add_separator()
            context_menu.add_command(label="Compare Multiple Spectra", 
                                   command=self.open_multi_spectrum_viewer)
            context_menu.add_separator()
            context_menu.add_command(label="Rename", 
                                   command=lambda: self.rename_item(tv, "end_member"))
            context_menu.add_command(label="Delete", 
                                   command=lambda: self.delete_spectra(tv))
        else:
            context_menu.add_command(label="View Spectrum", 
                                   command=lambda: self.view_spectrum(tv, "mixed"))
            context_menu.add_command(label="Analyze", 
                                   command=lambda: self.prepare_analysis(tv))
            context_menu.add_separator()
            context_menu.add_command(label="Compare Multiple Spectra", 
                                   command=self.open_multi_spectrum_viewer)
            context_menu.add_separator()
            context_menu.add_command(label="Rename", 
                                   command=lambda: self.rename_item(tv, "mixed"))
            context_menu.add_command(label="Delete", 
                                   command=lambda: self.delete_spectra(tv))
        
        def show_context_menu(event):
            if tv.identify_row(event.y):
                # Select the item under the cursor
                tv.selection_set(tv.identify_row(event.y))
                context_menu.post(event.x_root, event.y_root)
        
        tv.bind("<Button-3>", show_context_menu)
    
    def create_preview_panel(self, parent):
        """Create the spectrum preview panel"""
        # Configure the frame
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Create matplotlib figure with transparent background
        self.preview_fig = Figure(figsize=(6, 4), facecolor='none', edgecolor='none')
        self.preview_ax = self.preview_fig.add_subplot(111)
        self.preview_ax.set_facecolor('none')
        
        # Create canvas
        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, master=parent)
        self.preview_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Info panel below the plot
        info_frame = tb.Frame(parent)
        info_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Spectrum info labels
        self.info_vars = {
            'name': tk.StringVar(value="No spectrum selected"),
            'points': tk.StringVar(value=""),
            'range': tk.StringVar(value=""),
            'mean': tk.StringVar(value="")
        }
        
        tb.Label(info_frame, textvariable=self.info_vars['name'], 
                font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        tb.Label(info_frame, textvariable=self.info_vars['points']).pack(anchor="w")
        tb.Label(info_frame, textvariable=self.info_vars['range']).pack(anchor="w")
        tb.Label(info_frame, textvariable=self.info_vars['mean']).pack(anchor="w")
        
        # Initialize empty plot
        self.show_empty_preview()
    
    def show_empty_preview(self):
        """Show empty preview panel"""
        self.preview_ax.clear()
        self.preview_ax.text(0.5, 0.5, 'Select a spectrum to preview', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.preview_ax.transAxes, fontsize=12, 
                           color='gray', style='italic')
        self.preview_ax.set_xticks([])
        self.preview_ax.set_yticks([])
        self.preview_canvas.draw()
        
        # Clear info
        self.info_vars['name'].set("No spectrum selected")
        for key in ['points', 'range', 'mean']:
            self.info_vars[key].set("")
    
    def on_spectrum_select(self, tv, data_type):
        """Handle spectrum selection for preview"""
        selection = tv.selection()
        if not selection:
            self.show_empty_preview()
            return
        
        try:
            # Get selected item name
            item_name = tv.item(selection[0], "values")[0]
            
            # Determine folder
            folder = "spectral/spectral_library" if data_type == "end_member" else "spectral/mixed_pre_processed"
            
            # Load spectrum
            file_path = os.path.join(folder, f"{item_name}.txt")
            spectrum_df = self.data_manager.load_spectrum(file_path)
            
            # Update preview
            self.update_preview(item_name, spectrum_df, data_type)
            
        except Exception as e:
            # Show error in preview
            self.preview_ax.clear()
            self.preview_ax.text(0.5, 0.5, f'Error loading spectrum:\n{str(e)}', 
                               horizontalalignment='center', verticalalignment='center',
                               transform=self.preview_ax.transAxes, fontsize=10, 
                               color='red')
            self.preview_ax.set_xticks([])
            self.preview_ax.set_yticks([])
            self.preview_canvas.draw()
    
    def update_preview(self, name, spectrum_df, data_type):
        """Update the preview panel with spectrum data"""
        # Clear previous plot
        self.preview_ax.clear()
        
        # Get theme colors
        theme_colors = self.get_theme_colors()
        
        # Extract data
        wavenumber = spectrum_df['Wavenumber'].values
        wavelength = 10000 / wavenumber
        emissivity = spectrum_df['Emissivity'].values
        uncertainty = spectrum_df['Uncertainty'].values
        
        # Plot spectrum
        color = 'blue' if data_type == 'end_member' else 'red'
        self.preview_ax.plot(wavelength, emissivity, color=color, linewidth=2, label=name)
        self.preview_ax.fill_between(wavelength, emissivity - uncertainty, 
                                   emissivity + uncertainty, alpha=0.2, color=color)
        
        # Apply theme-aware styling
        self.preview_ax.set_xlabel('Wavelength (μm)', fontsize=10, color=theme_colors['text'])
        self.preview_ax.set_ylabel('Emissivity', fontsize=10, color=theme_colors['text'])
        self.preview_ax.grid(True, alpha=0.3, color=theme_colors['grid'])
        self.preview_ax.tick_params(colors=theme_colors['text'])
        
        # Add title based on data type
        title = f"End-Member: {name}" if data_type == 'end_member' else f"Mixed Spectrum: {name}"
        self.preview_ax.set_title(title, fontsize=11, fontweight='bold', color=theme_colors['text'])
        
        # Update canvas
        self.preview_fig.tight_layout()
        self.preview_canvas.draw()
        
        # Update info panel
        self.info_vars['name'].set(name)
        self.info_vars['points'].set(f"Data points: {len(emissivity)}")
        self.info_vars['range'].set(f"Wavelength: {wavelength.min():.2f} - {wavelength.max():.2f} μm")
        self.info_vars['mean'].set(f"Mean emissivity: {emissivity.mean():.4f} ± {uncertainty.mean():.4f}")
    
    def add_spectra(self, spectra_type=None):
        """Add new spectra files to the system with improved UI"""
        if spectra_type is None:
            # Ask for type if not provided
            types = ["end_member", "unmix"]
            type_dialog = tb.Toplevel(self.frame.winfo_toplevel())
            type_dialog.title("Select Spectra Type")
            type_dialog.geometry("300x150")
            type_dialog.resizable(False, False)
            
            # Center content
            content_frame = tb.Frame(type_dialog)
            content_frame.place(relx=0.5, rely=0.5, anchor="center")
            
            tb.Label(content_frame, text="Select spectra type:").pack(pady=5)
            
            type_var = tk.StringVar()
            for t in types:
                tb.Radiobutton(content_frame, text=t.replace("_", "-").title(), 
                              variable=type_var, value=t).pack(anchor="w", padx=20)
            
            def on_ok():
                nonlocal spectra_type
                spectra_type = type_var.get()
                type_dialog.destroy()
                if spectra_type:
                    self.process_spectra_file(spectra_type)
            
            def on_cancel():
                type_dialog.destroy()
            
            button_frame = tb.Frame(content_frame)
            button_frame.pack(pady=10, fill="x")
            
            tb.Button(button_frame, text="OK", command=on_ok).pack(side="left", padx=10)
            tb.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=10)
            
            type_dialog.transient(self.frame.winfo_toplevel())
            type_dialog.grab_set()
            self.frame.wait_window(type_dialog)
        else:
            self.process_spectra_file(spectra_type)
    
    def process_spectra_file(self, spectra_type):
        """Process a single spectra file"""
        # File dialog title based on type
        title = "Select End-Member File" if spectra_type == "end_member" else "Select Mixed Spectrum File"
        
        file_path = filedialog.askopenfilename(
            title=title,filetypes=[
            ("Supported Spectra Files", "*.xlsx *.xls *.csv *.txt"),
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")]
            )

        if not file_path:
            return
        
        # Create name entry dialog
        name_dialog = tb.Toplevel(self.frame.winfo_toplevel())
        name_dialog.title("Enter Name")
        name_dialog.geometry("400x150")
        name_dialog.resizable(False, False)
        
        # Default name from filename
        default_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Center content
        content_frame = tb.Frame(name_dialog)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tb.Label(content_frame, text="Enter name for preprocessed file:").pack(pady=5)
        
        name_var = tk.StringVar(value=default_name)
        name_entry = tb.Entry(content_frame, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.select_range(0, "end")
        name_entry.focus()
        
        def on_ok():
            pp_name = name_var.get().strip()
            name_dialog.destroy()
            
            if not pp_name:
                messagebox.showwarning("Error", "Name cannot be empty")
                return
            
            try:
                # Determine destination based on type
                if spectra_type == "end_member":
                    dest_folder = "spectral/end-member_raw_files"
                    output_folder = "spectral/spectral_library"
                    file_list = self.data_manager.end_member_list
                    tv = self.spectral_tv
                else:  # unmix
                    dest_folder = "spectral/mixed_raw_files"
                    output_folder = "spectral/mixed_pre_processed"
                    file_list = self.data_manager.mixed_list
                    tv = self.mixed_tv
                
                # Check for duplicate names
                if pp_name in file_list:
                    if not messagebox.askyesno("Warning", 
                                             f"File '{pp_name}' already exists. Overwrite?"):
                        return
                
                # Copy raw file
                os.makedirs(dest_folder, exist_ok=True)
                shutil.copy2(file_path, dest_folder)
                
                # Process file
                output_path = os.path.join(output_folder, f"{pp_name}.txt")
                
                # Status update
                self.update_status(f"Processing {os.path.basename(file_path)}...")
                
                # Process the file
                self.data_manager.pre_process_spectra(file_path, output_path)
                
                # Update lists and UI
                self.data_manager.refresh_lists()
                
                # Refresh treeview
                self.populate_treeview(tv, spectra_type)
                
                # Notify analysis tab to refresh its data lists
                if self.analysis_tab:
                    self.analysis_tab.populate_selection_treeviews()
                
                # Status update
                self.update_status(f"Added {pp_name} to {spectra_type} library")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed processing file: {str(e)}")
                self.update_status("Error processing file")
        
        def on_cancel():
            name_dialog.destroy()
        
        button_frame = tb.Frame(content_frame)
        button_frame.pack(pady=10, fill="x")
        
        tb.Button(button_frame, text="OK", command=on_ok).pack(side="left", padx=10)
        tb.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=10)
        
        # Key bindings
        name_entry.bind("<Return>", lambda e: on_ok())
        name_entry.bind("<Escape>", lambda e: on_cancel())
        
        name_dialog.transient(self.frame.winfo_toplevel())
        name_dialog.grab_set()
        self.frame.wait_window(name_dialog)
    
    def delete_spectra(self, tv):
        """Delete selected spectra from system"""
        # Check if any items are selected
        selection = tv.selection()
        if not selection:
            messagebox.showwarning("Error", "No items selected")
            return
        
        # Determine which data we're working with
        if tv == self.spectral_tv:
            folder = "spectral/spectral_library"
            items = self.data_manager.end_member_list
        else:
            folder = "spectral/mixed_pre_processed"
            items = self.data_manager.mixed_list
        
        # Confirm deletion
        item_count = len(selection)
        if not messagebox.askyesno("Confirm", 
                                  f"Delete {item_count} selected item{'s' if item_count > 1 else ''}?"):
            return
        
        # Delete selected items
        deleted_count = 0
        for item_id in selection:
            try:
                # Get the displayed text
                item_text = tv.item(item_id, "values")[0]
                # Remove from filesystem
                file_path = os.path.join(folder, f"{item_text}.txt")
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Remove from treeview
                tv.delete(item_id)
                deleted_count += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {item_text}: {str(e)}")
        
        # Update data manager
        self.data_manager.refresh_lists()
        
        # Notify analysis tab to refresh its data lists
        if self.analysis_tab:
            self.analysis_tab.populate_selection_treeviews()
        
        # Update status
        self.update_status(f"Deleted {deleted_count} item{'s' if deleted_count > 1 else ''}")
    
    def rename_item(self, tv, data_type):
        """Rename selected item"""
        # Check if an item is selected
        selection = tv.selection()
        if not selection or len(selection) != 1:
            messagebox.showwarning("Error", "Select one item to rename")
            return
        
        # Get current name
        item_id = selection[0]
        current_name = tv.item(item_id, "values")[0]
        
        # Determine which folder to use
        if data_type == "end_member":
            folder = "spectral/spectral_library"
            items = self.data_manager.end_member_list
        else:
            folder = "spectral/mixed_pre_processed"
            items = self.data_manager.mixed_list
        
        # Create rename dialog
        rename_dialog = tb.Toplevel(self.frame.winfo_toplevel())
        rename_dialog.title("Rename Item")
        rename_dialog.geometry("400x150")
        rename_dialog.resizable(False, False)
        
        # Center content
        content_frame = tb.Frame(rename_dialog)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tb.Label(content_frame, text=f"Current name: {current_name}").pack(pady=5)
        tb.Label(content_frame, text="Enter new name:").pack(pady=5)
        
        new_name_var = tk.StringVar(value=current_name)
        name_entry = tb.Entry(content_frame, textvariable=new_name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.select_range(0, "end")
        name_entry.focus()
        
        def on_rename():
            new_name = new_name_var.get().strip()
            rename_dialog.destroy()
            
            if not new_name:
                messagebox.showwarning("Error", "Name cannot be empty")
                return
                
            if new_name == current_name:
                return
                
            if new_name in items:
                messagebox.showwarning("Error", f"Name '{new_name}' already exists")
                return
                
            try:
                # Rename file
                old_path = os.path.join(folder, f"{current_name}.txt")
                new_path = os.path.join(folder, f"{new_name}.txt")
                os.rename(old_path, new_path)
                
                # Update data manager
                self.data_manager.refresh_lists()
                
                # Update treeview
                tv.item(item_id, values=(new_name,) + tv.item(item_id, "values")[1:])
                
                # Notify analysis tab to refresh its data lists
                if self.analysis_tab:
                    self.analysis_tab.populate_selection_treeviews()
                
                # Update status
                self.update_status(f"Renamed {current_name} to {new_name}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename: {str(e)}")
        
        def on_cancel():
            rename_dialog.destroy()
        
        button_frame = tb.Frame(content_frame)
        button_frame.pack(pady=10, fill="x")
        
        tb.Button(button_frame, text="Rename", command=on_rename).pack(side="left", padx=10)
        tb.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=10)
        
        # Key bindings
        name_entry.bind("<Return>", lambda e: on_rename())
        name_entry.bind("<Escape>", lambda e: on_cancel())
        
        rename_dialog.transient(self.frame.winfo_toplevel())
        rename_dialog.grab_set()
        self.frame.wait_window(rename_dialog)
    
    def view_spectrum(self, tv, data_type):
        """View spectrum in plot window"""
        # Check if an item is selected
        selection = tv.selection()
        if not selection or len(selection) != 1:
            messagebox.showwarning("Error", "Select one item to view")
            return
        
        # Get selected item
        item_name = tv.item(selection[0], "values")[0]
        
        # Determine which folder to use
        if data_type == "end_member":
            folder = "spectral/spectral_library"
        else:
            folder = "spectral/mixed_pre_processed"
        
        try:
            # Load spectrum data
            file_path = os.path.join(folder, f"{item_name}.txt")
            spectrum_df = self.data_manager.load_spectrum(file_path)
            
            # Create spectrum viewer
            viewer = SpectrumViewer(self.frame.winfo_toplevel(), item_name, spectrum_df)
            viewer.show()
            
            # Update status
            self.update_status(f"Viewing spectrum: {item_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view spectrum: {str(e)}")
            self.update_status("Error viewing spectrum")
    
    def prepare_analysis(self, tv=None):
        """Prepare for analysis from selected mixed spectrum"""
        # If called from context menu, get selected item
        if tv is not None:
            selection = tv.selection()
            if not selection or len(selection) != 1:
                messagebox.showwarning("Error", "Select one mixed spectrum")
                return
                
            # Get selected item name
            mixed_item = tv.item(selection[0], "values")[0]
            
            # Switch to analysis tab and select this item
            # Get the notebook from parent hierarchy
            notebook = self.frame.master
            notebook.select(1)  # Switch to analysis tab
            
            # Get analysis tab and select the item
            # The parent should have a reference to all tabs
            main_window = self.frame.winfo_toplevel()
            for widget_name, widget in main_window.children.items():
                if hasattr(widget, 'analysis_tab'):
                    widget.analysis_tab.select_mixed_spectrum(mixed_item)
                    break
    
    def open_multi_spectrum_viewer(self):
        """Open the multi-spectrum comparison viewer"""
        try:
            viewer = MultiSpectrumViewer(self.frame.winfo_toplevel(), self.data_manager)
            viewer.show()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open multi-spectrum viewer: {str(e)}")