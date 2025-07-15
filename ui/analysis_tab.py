"""
Analysis tab for the Mineral Spectra Analyzer
"""

import os
import tkinter as tk
from tkinter import messagebox
import numpy as np
import pandas as pd
import ttkbootstrap as tb

from core.spectral_algorithms import SpectralAlgorithms


class AnalysisTab:
    """Analysis tab implementation"""
    
    def __init__(self, parent, data_manager, status_callback):
        self.parent = parent
        self.data_manager = data_manager
        self.update_status = status_callback
        self.results_tab = None
        
        # Create main frame
        self.frame = tb.Frame(parent)
        self.setup_ui()
    
    def set_results_tab(self, results_tab):
        """Set reference to results tab"""
        self.results_tab = results_tab
    
    def setup_ui(self):
        """Setup the analysis tab UI"""
        # Split into left (parameters) and right (selection) panels
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - Analysis Parameters
        left_frame = tb.Labelframe(self.frame, text="Analysis Parameters", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Algorithm selection
        algorithm_frame = tb.Frame(left_frame)
        algorithm_frame.pack(fill="x", pady=10)
        
        tb.Label(algorithm_frame, text="Algorithm:").pack(side="left", padx=5)
        self.algorithm_var = tk.StringVar(value="WLS")
        tb.Radiobutton(algorithm_frame, text="Weighted Least Squares (WLS)", 
                      variable=self.algorithm_var, value="WLS").pack(anchor="w", padx=20)
        tb.Radiobutton(algorithm_frame, text="Sum-to-One (STO)", 
                      variable=self.algorithm_var, value="STO").pack(anchor="w", padx=20)
        
        # Wavelength filtering with validation
        filter_frame = tb.Labelframe(left_frame, text="Wavelength Filtering", padding=10)
        filter_frame.pack(fill="x", pady=10)
        
        self.slice_var = tk.BooleanVar(value=False)
        slice_cb = tb.Checkbutton(filter_frame, text="Cut spectrum at maximum wavelength", 
                                variable=self.slice_var, 
                                command=self.toggle_max_wavelength)
        slice_cb.pack(anchor="w", pady=5)
        
        # Max wavelength control with validation
        max_wl_frame = tb.Frame(filter_frame)
        max_wl_frame.pack(fill="x", pady=5)
        
        tb.Label(max_wl_frame, text="Max wavelength (μm):").pack(side="left", padx=5)
        self.max_wl_var = tk.DoubleVar(value=25.0)
        self.max_wl_entry = tb.Entry(max_wl_frame, textvariable=self.max_wl_var, width=10)
        self.max_wl_entry.pack(side="left", padx=5)
        self.max_wl_entry.configure(state="disabled")
        
        # Validation indicator for wavelength
        self.wl_status_label = tb.Label(max_wl_frame, text="", width=15)
        self.wl_status_label.pack(side="left", padx=5)
        
        # Bind validation to wavelength entry
        self.max_wl_var.trace_add("write", self.validate_wavelength)
        
        # Analysis description
        description_frame = tb.Labelframe(left_frame, text="Algorithm Description")
        description_frame.pack(fill="both", expand=True, pady=10)
        
        self.algorithm_description = tb.Text(description_frame, wrap="word", height=10, 
                                           font=("TkDefaultFont", 10))
        self.algorithm_description.pack(fill="both", expand=True, padx=5, pady=5)
        self.algorithm_description.insert("1.0", 
            "WLS (Weighted Least Squares) algorithm performs spectral unmixing by " +
            "minimizing the weighted residuals between the mixed spectrum and a " +
            "linear combination of end-member spectra. Weights are based on " +
            "measurement uncertainties.")
        self.algorithm_description.configure(state="disabled")
        
        # Algorithm selection callback
        self.algorithm_var.trace_add("write", self.update_algorithm_description)
        
        # Validation status panel
        validation_frame = tb.Labelframe(left_frame, text="Analysis Status", padding=10)
        validation_frame.pack(fill="x", pady=10)
        
        self.validation_vars = {
            'mixed': tk.StringVar(value="⚠ No mixed spectrum selected"),
            'endmembers': tk.StringVar(value=" No end-members selected"),
            'parameters': tk.StringVar(value=" Parameters valid"),
            'overall': tk.StringVar(value=" Analysis not ready")
        }
        
        for key, var in self.validation_vars.items():
            label = tb.Label(validation_frame, textvariable=var, font=("TkDefaultFont", 9))
            label.pack(anchor="w", pady=2)
        
        # Run button with validation state
        run_frame = tb.Frame(left_frame)
        run_frame.pack(fill="x", pady=10)
        
        self.run_button = tb.Button(run_frame, text="Run Analysis", bootstyle="success", 
                                  command=self.run_analysis_from_ui, state="disabled")
        self.run_button.pack(fill="x", ipady=10)
        
        # Add tooltip for disabled button
        self.run_tooltip = tb.Label(run_frame, text="Select spectra to enable analysis", 
                                  bootstyle="secondary", font=("TkDefaultFont", 8))
        self.run_tooltip.pack(pady=2)
        
        # Right panel - Spectra Selection
        right_frame = tb.Labelframe(self.frame, text="Spectra Selection", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_rowconfigure(3, weight=1)
        
        # Mixed spectra selection
        tb.Label(right_frame, text="Select Mixed Spectrum:").grid(row=0, column=0, sticky="w")
        self.mixed_selection_tv = tb.Treeview(
            right_frame,
            columns=("name",),
            show="headings",
            height=5,
            selectmode="browse"
        )
        self.mixed_selection_tv.heading("name", text="Name")
        self.mixed_selection_tv.column("name", width=500)
        self.mixed_selection_tv.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # End-member spectra selection
        tb.Label(right_frame, text="Select End-Member Spectra:").grid(row=2, column=0, 
                                                                     sticky="w", pady=(10, 0))
        self.em_selection_tv = tb.Treeview(
            right_frame,
            columns=("name",),
            show="headings",
            height=10,
            selectmode="extended"
        )
        self.em_selection_tv.heading("name", text="Name")
        self.em_selection_tv.column("name", width=500)
        self.em_selection_tv.grid(row=3, column=0, sticky="nsew", pady=5)
        
        # Add scroll bars
        mixed_scrollbar = tb.Scrollbar(right_frame, orient="vertical", 
                                     command=self.mixed_selection_tv.yview)
        mixed_scrollbar.grid(row=1, column=1, sticky="ns")
        self.mixed_selection_tv.configure(yscrollcommand=mixed_scrollbar.set)
        
        em_scrollbar = tb.Scrollbar(right_frame, orient="vertical", 
                                  command=self.em_selection_tv.yview)
        em_scrollbar.grid(row=3, column=1, sticky="ns")
        self.em_selection_tv.configure(yscrollcommand=em_scrollbar.set)
        
        # Bind selection events for validation
        self.mixed_selection_tv.bind("<<TreeviewSelect>>", self.validate_selections)
        self.em_selection_tv.bind("<<TreeviewSelect>>", self.validate_selections)
        
        # Populate selection treeviews
        self.populate_selection_treeviews()
        
        # Bind focus event to refresh data when tab becomes visible
        self.frame.bind("<Visibility>", self.on_tab_visible)
        
        # Initial validation
        self.validate_all_parameters()
    
    def populate_selection_treeviews(self):
        """Populate the selection treeviews in the analysis tab"""
        # Clear existing items
        for tv in [self.mixed_selection_tv, self.em_selection_tv]:
            for i in tv.get_children():
                tv.delete(i)
        
        # Populate mixed spectra
        for item in self.data_manager.mixed_list:
            self.mixed_selection_tv.insert("", "end", values=(item,))
        
        # Populate end-member spectra
        for item in self.data_manager.end_member_list:
            self.em_selection_tv.insert("", "end", values=(item,))
    
    def on_tab_visible(self, event=None):
        """Called when the analysis tab becomes visible to refresh data"""
        # Refresh data manager lists and repopulate treeviews
        self.data_manager.refresh_lists()
        self.populate_selection_treeviews()
    
    def select_mixed_spectrum(self, spectrum_name):
        """Select a specific mixed spectrum in the treeview"""
        for item_id in self.mixed_selection_tv.get_children():
            if self.mixed_selection_tv.item(item_id, "values")[0] == spectrum_name:
                self.mixed_selection_tv.selection_set(item_id)
                self.mixed_selection_tv.see(item_id)
                break
    
    def update_algorithm_description(self, *args):
        """Update algorithm description when selection changes"""
        # Enable text widget for editing
        self.algorithm_description.configure(state="normal")
        # Clear current content
        self.algorithm_description.delete("1.0", "end")
        
        # Insert new description based on selected algorithm
        if self.algorithm_var.get() == "WLS":
            description = """WLS (Weighted Least Squares) algorithm performs spectral unmixing by minimizing the weighted residuals between the mixed spectrum and a linear combination of end-member spectra. Weights are based on measurement uncertainties.

Key features:
- Removes end-members with negative abundances
- Calculates abundance errors
- Produces lower RMS errors than non-weighted algorithms"""
        else:  # STO
            description = """STO (Sum-to-One) algorithm performs spectral unmixing by constraining the sum of abundances to equal 1, providing a physically meaningful result for mineral mixtures.

Key features:
- Enforces abundance sum = 1 constraint
- Removes end-members with negative abundances
- Calculates normalized abundances
- Good for closed mineral systems"""
        
        self.algorithm_description.insert("1.0", description)
        # Disable editing
        self.algorithm_description.configure(state="disabled")
    
    def toggle_max_wavelength(self):
        """Enable/disable max wavelength entry based on checkbox"""
        if self.slice_var.get():
            self.max_wl_entry.configure(state="normal")
        else:
            self.max_wl_entry.configure(state="disabled")
        
        # Update validation status
        self.validate_wavelength()
        # Trigger overall validation
        if hasattr(self, 'validation_vars'):  # Only if UI is fully initialized
            self.validate_all_parameters()
    
    def validate_wavelength(self, *args):
        """Validate wavelength parameter"""
        if not self.slice_var.get():
            self.wl_status_label.configure(text="Disabled", bootstyle="secondary")
            return True
        
        try:
            wl_value = self.max_wl_var.get()
            if wl_value <= 0:
                self.wl_status_label.configure(text="Must be > 0", bootstyle="danger")
                return False
            elif wl_value > 100:
                self.wl_status_label.configure(text="Too large", bootstyle="warning") 
                return False
            else:
                self.wl_status_label.configure(text="✓ Valid", bootstyle="success")
                return True
        except (ValueError, tk.TclError):
            self.wl_status_label.configure(text="Invalid number", bootstyle="danger")
            return False
        finally:
            # Only trigger overall validation if UI is fully initialized and not during trace events
            if hasattr(self, 'validation_vars') and len(args) == 0:
                self.validate_all_parameters()
    
    def validate_selections(self, event=None):
        """Validate spectrum selections"""
        mixed_valid = len(self.mixed_selection_tv.selection()) > 0
        em_valid = len(self.em_selection_tv.selection()) > 0
        
        # Update validation status
        if mixed_valid:
            self.validation_vars['mixed'].set("✓ Mixed spectrum selected")
        else:
            self.validation_vars['mixed'].set("⚠ No mixed spectrum selected")
        
        if em_valid:
            em_count = len(self.em_selection_tv.selection())
            self.validation_vars['endmembers'].set(f"✓ {em_count} end-member(s) selected")
        else:
            self.validation_vars['endmembers'].set("⚠ No end-members selected")
        
        # Only call validate_all_parameters if this is triggered by an event (user interaction)
        # Not during initialization
        if event is not None:
            self.validate_all_parameters()
        
        return mixed_valid and em_valid
    
    def validate_parameters(self):
        """Validate analysis parameters"""
        # Check wavelength validation without calling validate_wavelength to avoid recursion
        if not self.slice_var.get():
            self.validation_vars['parameters'].set("✓ Parameters valid")
            return True
        
        try:
            wl_value = self.max_wl_var.get()
            wl_valid = 0 < wl_value <= 100
        except (ValueError, tk.TclError):
            wl_valid = False
        
        if wl_valid:
            self.validation_vars['parameters'].set("✓ Parameters valid")
        else:
            self.validation_vars['parameters'].set("❌ Invalid parameters")
        
        return wl_valid
    
    def validate_all_parameters(self):
        """Validate all parameters and update UI state"""
        selections_valid = self.validate_selections()
        params_valid = self.validate_parameters()
        
        # Overall validation
        overall_valid = selections_valid and params_valid
        
        if overall_valid:
            self.validation_vars['overall'].set("✓ Ready to run analysis")
            self.run_button.configure(state="normal", bootstyle="success")
            self.run_tooltip.configure(text="All parameters valid - ready to analyze")
        else:
            self.validation_vars['overall'].set("❌ Analysis not ready")
            self.run_button.configure(state="disabled", bootstyle="secondary")
            
            # Provide specific guidance
            if not selections_valid:
                self.run_tooltip.configure(text="Select mixed spectrum and end-members")
            elif not params_valid:
                self.run_tooltip.configure(text="Fix parameter validation errors")
            else:
                self.run_tooltip.configure(text="Check validation status above")
        
        return overall_valid
    
    def run_analysis_with_params(self, algorithm):
        """Run analysis with specified algorithm"""
        self.algorithm_var.set(algorithm)
        self.run_analysis_from_ui()
    
    def run_analysis_from_ui(self):
        """Run analysis with parameters from UI"""
        # Validate all parameters before proceeding
        if not self.validate_all_parameters():
            messagebox.showwarning("Validation Error", 
                                 "Please fix all validation errors before running analysis.")
            return
        
        # Get selected mixed spectrum
        mixed_selection = self.mixed_selection_tv.selection()
        if not mixed_selection:
            messagebox.showwarning("Error", "Select a mixed spectrum")
            return
            
        # Get selected end members
        endmember_selection = self.em_selection_tv.selection()
        if not endmember_selection:
            messagebox.showwarning("Error", "Select at least one end-member spectrum")
            return
            
        # Get selected parameters
        algorithm = self.algorithm_var.get()
        slicewl = self.slice_var.get()
        maxwl = self.max_wl_var.get() if slicewl else None
        
        try:
            # Get selected values
            mixed_item = self.mixed_selection_tv.item(mixed_selection[0], 'values')[0]
            endmembers = [self.em_selection_tv.item(item, 'values')[0] 
                         for item in endmember_selection]
            
            # Update status
            self.update_status(f"Running {algorithm} analysis...")
            
            # Load the mixed sample spectra
            mixed_file = os.path.join(self.data_manager.mixed_pre_processed_folder, 
                                    f"{mixed_item}.txt")
            mixed_df = self.data_manager.load_spectrum(mixed_file)
            
            wavenumber = mixed_df['Wavenumber'].values
            
            # Apply wavelength filter if requested
            if slicewl and maxwl is not None:
                wavelength = 10000 / wavenumber
                valid_indices = wavelength <= maxwl
                wavenumber = wavenumber[valid_indices]
                mixed_df = mixed_df.iloc[valid_indices]
            
            # Create data structures for analysis
            M = mixed_df['Emissivity'].values
            measurerr = mixed_df['Uncertainty'].values
            W = np.diag(1/measurerr**2)  # Weight matrix
            
            # Load end member spectra
            EMdat = []
            for endmember in endmembers:
                em_file = os.path.join("spectral/spectral_library", f"{endmember}.txt")
                em_df = self.data_manager.load_spectrum(em_file)
                
                # Interpolate if needed
                em_values = self.data_manager.interpolate_spectrum(em_df, wavenumber)
                EMdat.append(em_values)
            
            EMdat = np.array(EMdat)

            # --- START OF FIX: DATA CLEANING ---
            # After interpolation, end-members might have NaN values if the
            # mixed spectrum's wavenumber range extends beyond their own.
            # We must remove these spectral channels from all data before analysis.

            # Find any channel (column) where at least one end-member has a NaN
            # or the mixed spectrum itself has a NaN.
            invalid_channels_mask = np.isnan(EMdat).any(axis=0) | np.isnan(M)

            if np.any(invalid_channels_mask):
                # Create a mask for channels that are valid (not invalid)
                valid_channels_mask = ~invalid_channels_mask
                
                # Filter all data arrays to keep only the valid channels
                wavenumber = wavenumber[valid_channels_mask]
                M = M[valid_channels_mask]
                measurerr = measurerr[valid_channels_mask]
                EMdat = EMdat[:, valid_channels_mask]
                
                # Check if any data remains after filtering
                if M.size == 0 or EMdat.size == 0:
                    raise ValueError("No overlapping spectral range found between the mixed spectrum and all selected end-members.")

            # Re-create the weight matrix with the filtered uncertainty data.
            # Add a small epsilon to avoid division by zero if uncertainty is 0.
            W = np.diag(1 / (measurerr**2 + 1e-12))
            # --- END OF FIX ---
            # --- DEBUGGING PRINT STATEMENTS ---
            print("\n" + "="*25 + " DEBUGGING DATA " + "="*25)
            print(f"File: analysis_tab.py, Function: run_analysis_from_ui")
            print(f"Data check before calling '{algorithm}' algorithm:")
            
            # Check for shape alignment
            print(f"  - Shape of M (mixed spectrum): {M.shape}")
            print(f"  - Shape of EMdat (end-members): {EMdat.shape}")
            print(f"  - Shape of wavenumber: {wavenumber.shape}")

            # *** The most important check: Look for NaN values ***
            contains_nan_in_emdat = np.isnan(EMdat).any()
            contains_nan_in_m = np.isnan(M).any()
            
            print(f"  - Does EMdat contain any NaN values? -> {contains_nan_in_emdat}")
            print(f"  - Does M contain any NaN values? -> {contains_nan_in_m}")

            if contains_nan_in_emdat:
                print("  - DETECTED NaN VALUES IN EMDAT. This is likely the cause of the error.")
            
            print("="*70 + "\n")
            # --- END OF DEBUGGING ---
            
            # Run the selected algorithm
            if algorithm == 'WLS':
                WLSfit, WLSresidual, WLSendmembers, WLSA, WLSaberror, WLSrms = \
                    SpectralAlgorithms.run_WLS(EMdat, M, W, np.array(endmembers))
                
                # Create results tab with all spectral data
                if self.results_tab:
                    self.results_tab.create_results_tab(
                        algorithm, mixed_item, WLSendmembers, WLSA, WLSaberror, 
                        WLSfit, WLSresidual, M, measurerr, wavenumber, WLSrms, maxwl,
                        all_selected_endmembers=endmembers, mixed_spectrum_data=mixed_df, 
                        endmember_spectral_data=EMdat)
                
            else:  # STO
                STOfit, STOresidual, STOendmembers, STOA, STOaberror, STOnorm, STOrms = \
                    SpectralAlgorithms.run_STO(EMdat, M, W, np.array(endmembers))
                
                # Create results tab with all spectral data
                if self.results_tab:
                    self.results_tab.create_results_tab(
                        algorithm, mixed_item, STOendmembers, STOA, STOaberror, 
                        STOfit, STOresidual, M, measurerr, wavenumber, STOrms, maxwl, 
                        normalized_abundances=STOnorm, all_selected_endmembers=endmembers,
                        mixed_spectrum_data=mixed_df, endmember_spectral_data=EMdat)
            
            # Switch to results tab
            notebook = self.frame.master
            notebook.select(2)  # Index 2 is the results tab
            
            # Update status
            self.update_status(f"Analysis complete: {algorithm} on {mixed_item}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            self.update_status("Analysis failed")
            import traceback
            traceback.print_exc()
