"""
Enhanced Data manager class for handling spectral data with CSV and Excel support
"""

import os
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline


class DataManager:
    """Manages spectral data loading, preprocessing, and storage with enhanced file format support"""
    
    def __init__(self):
        self.end_member_list = self.get_preprocessed_files("spectral/spectral_library")
        self.mixed_list = self.get_preprocessed_files("spectral/mixed_pre_processed")
        self.mixed_pre_processed_folder = "spectral/mixed_pre_processed"
        
    
    def get_preprocessed_files(self, folder):
        """Get list of preprocessed files without extension"""
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            return []
        return [os.path.splitext(f)[0] for f in os.listdir(folder) if f.endswith(".txt")]
    
    def refresh_lists(self):
        """Refresh the lists of available files"""
        self.end_member_list = self.get_preprocessed_files("spectral/spectral_library")
        self.mixed_list = self.get_preprocessed_files("spectral/mixed_pre_processed")
    
    def validate_file_format(self, file_path):
        """
        Validate if the file is a genuine Excel file or CSV masquerading as Excel.
        Returns: 'excel', 'csv', 'csv_disguised_as_excel', or 'unknown'
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in ['.xlsx', '.xls']:
            try:
                # Try to read as Excel first
                pd.read_excel(file_path, nrows=5)
                return 'excel'
            except Exception as e:
                error_str = str(e)
                if ("Excel file format cannot be determined" in error_str or 
                    "CompDoc is not a recognised OLE file" in error_str or
                    "File contains an invalid specification" in error_str):
                    # This is likely a CSV with .xlsx extension
                    return 'csv_disguised_as_excel'
                else:
                    raise e
        elif file_extension == '.csv':
            return 'csv'
        elif file_extension == '.txt':
            return 'txt'
        else:
            return 'unknown'
    
    def read_csv_with_detection(self, file_path):
        """
        Read CSV file with automatic delimiter and encoding detection
        """
        # Common delimiters to try
        delimiters = [',', '\t', ';', '|']
        # Common encodings to try
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        best_df = None
        best_score = 0
        
        for delimiter in delimiters:
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
                    
                    # Score this attempt based on:
                    # 1. Number of columns (more is generally better for spectral data)
                    # 2. Number of rows with valid numeric data
                    # 3. Avoid single-column results (usually means wrong delimiter)
                    
                    if len(df.columns) < 2:
                        continue
                        
                    # Try to convert first few columns to numeric to test validity
                    numeric_cols = 0
                    for col in df.columns[:3]:  # Check first 3 columns
                        try:
                            pd.to_numeric(df[col].head(10), errors='raise')
                            numeric_cols += 1
                        except:
                            pass
                    
                    # Score: number of columns * numeric columns * rows
                    score = len(df.columns) * numeric_cols * len(df)
                    
                    if score > best_score:
                        best_score = score
                        best_df = df
                        
                except Exception:
                    continue
        
        if best_df is None:
            raise ValueError("Could not read CSV file with any common delimiter/encoding combination")
            
        return best_df
    
    def pre_process_spectra(self, file_path, output_path):
        """
        Unified preprocessing function for all spectra types.
        Enhanced to handle Excel, CSV, and text files with robust error handling.
        """
        try:
            # Validate and determine file format
            file_format = self.validate_file_format(file_path)
            print(f"Detected file format: {file_format}")
            
            # Read file based on detected format
            if file_format == 'excel':
                print(f"Reading {os.path.basename(file_path)} as an Excel file.")
                df_raw = pd.read_excel(file_path)
                
            elif file_format == 'csv' or file_format == 'csv_disguised_as_excel':
                if file_format == 'csv_disguised_as_excel':
                    print(f"Warning: {os.path.basename(file_path)} appears to be a CSV file with .xlsx extension.")
                print(f"Reading {os.path.basename(file_path)} as a CSV file.")
                df_raw = self.read_csv_with_detection(file_path)
                
            elif file_format == 'txt':
                print(f"Reading {os.path.basename(file_path)} as a text file.")
                # Try tab-delimited first, then comma-delimited
                try:
                    df_raw = pd.read_csv(file_path, delimiter='\t')
                except:
                    df_raw = pd.read_csv(file_path, delimiter=',')
                    
            else:
                raise ValueError(f"Unsupported file format. Please use .csv, .txt, .xlsx, or .xls files.")

            print(f"Successfully read {os.path.basename(file_path)}. Shape: {df_raw.shape}")
            print(f"Columns found: {list(df_raw.columns)}")

            # Validate minimum requirements
            if df_raw.empty:
                raise ValueError("File is empty")
            
            if len(df_raw.columns) < 2:
                raise ValueError("File must have at least 2 columns (wavenumber and emissivity)")

            # 2. Intelligently Identify Columns
            wavenumber_col, emissivity_col, uncertainty_col = None, None, None
            
            # Search for columns by keywords (case-insensitive)
            for col in df_raw.columns:
                col_lower = str(col).lower().strip()
                
                # Wavenumber column detection
                if wavenumber_col is None and any(keyword in col_lower for keyword in 
                    ['wavenumber', 'wave number', 'wavenum', 'frequency', 'freq', 'cm-1', 'cm^-1']):
                    wavenumber_col = col
                    
                # Emissivity column detection
                elif emissivity_col is None and any(keyword in col_lower for keyword in 
                    ['emissivity', 'emiss', 'emit', 'reflectance', 'refl', 'intensity', 'signal']):
                    emissivity_col = col
                    
                # Uncertainty column detection
                elif uncertainty_col is None and any(keyword in col_lower for keyword in 
                    ['uncertainty', 'error', 'uncert', 'std', 'sigma', 'deviation']):
                    uncertainty_col = col
            
            # 3. Fallback to column position if names are not found
            if wavenumber_col is None:
                wavenumber_col = df_raw.columns[0]
                print(f"No wavenumber column detected by name, using first column: '{wavenumber_col}'")
                
            if emissivity_col is None:
                emissivity_col = df_raw.columns[1]
                print(f"No emissivity column detected by name, using second column: '{emissivity_col}'")
                
            if uncertainty_col is None and len(df_raw.columns) > 2:
                uncertainty_col = df_raw.columns[2]
                print(f"No uncertainty column detected by name, using third column: '{uncertainty_col}'")

            print(f"Using columns - Wavenumber: '{wavenumber_col}', Emissivity: '{emissivity_col}', Uncertainty: '{uncertainty_col}'")

            # 4. Create a new, clean DataFrame with standardized column names
            clean_df = pd.DataFrame()
            
            # Convert wavenumber column
            try:
                clean_df['Wavenumber'] = pd.to_numeric(df_raw[wavenumber_col], errors='coerce')
            except Exception as e:
                raise ValueError(f"Could not convert wavenumber column '{wavenumber_col}' to numeric: {e}")
            
            # Convert emissivity column
            try:
                clean_df['Emissivity'] = pd.to_numeric(df_raw[emissivity_col], errors='coerce')
            except Exception as e:
                raise ValueError(f"Could not convert emissivity column '{emissivity_col}' to numeric: {e}")

            # 5. Handle uncertainty: use it if present, otherwise create it
            if uncertainty_col and uncertainty_col in df_raw.columns:
                try:
                    clean_df['Uncertainty'] = pd.to_numeric(df_raw[uncertainty_col], errors='coerce')
                    print("Using provided uncertainty values")
                except Exception as e:
                    print(f"Warning: Could not convert uncertainty column, generating default values: {e}")
                    clean_df['Uncertainty'] = 0.02 * np.abs(clean_df['Emissivity'])
            else:
                # If no uncertainty is provided, default to 2% relative uncertainty
                clean_df['Uncertainty'] = 0.02 * np.abs(clean_df['Emissivity'])
                print("No uncertainty column found, using 2% relative uncertainty")

            # 6. Data validation and cleaning
            initial_rows = len(clean_df)
            
            # Remove rows with invalid wavenumber or emissivity
            clean_df = clean_df.dropna(subset=['Wavenumber', 'Emissivity'])
            
            # Remove rows with non-positive wavenumbers (physically impossible)
            clean_df = clean_df[clean_df['Wavenumber'] > 0]
            
            # Remove rows with negative uncertainties
            clean_df = clean_df[clean_df['Uncertainty'] >= 0]
            
            final_rows = len(clean_df)
            if final_rows < initial_rows:
                print(f"Removed {initial_rows - final_rows} invalid rows during cleaning")
            
            if len(clean_df) == 0:
                raise ValueError("No valid data rows remaining after cleaning")

            # Sort by wavenumber to ensure monotonicity for interpolation and plotting
            clean_df = clean_df.sort_values(by='Wavenumber').reset_index(drop=True)
            
            # Check for duplicate wavenumbers
            duplicates = clean_df['Wavenumber'].duplicated().sum()
            if duplicates > 0:
                print(f"Warning: Found {duplicates} duplicate wavenumber values, keeping first occurrence")
                clean_df = clean_df.drop_duplicates(subset=['Wavenumber'], keep='first').reset_index(drop=True)


            # 8. Final validation
            if len(clean_df) < 10:
                print(f"Warning: Only {len(clean_df)} data points after processing. This may be insufficient for analysis.")

            # 9. Save the clean dataframe to the standardized txt output file
            clean_df.to_csv(output_path, sep='\t', index=False)
            
            print(f"Successfully processed {file_path} into {output_path}")
            print(f"Final data shape: {clean_df.shape}")
            print(f"Wavenumber range: {clean_df['Wavenumber'].min():.2f} - {clean_df['Wavenumber'].max():.2f}")
            print(f"Emissivity range: {clean_df['Emissivity'].min():.4f} - {clean_df['Emissivity'].max():.4f}")
            print("First few rows of processed data:")
            print(clean_df.head())
            
            return True

        except Exception as e:
            # Provide specific, actionable error messages
            error_str = str(e)
            
            if "Excel file format cannot be determined" in error_str or "CompDoc is not a recognised OLE file" in error_str:
                raise ValueError(
                    f"File '{os.path.basename(file_path)}' appears to be a CSV file saved with .xlsx extension.\n"
                    "To fix this:\n"
                    "1. Open the file in Excel\n"
                    "2. Go to File → Save As\n"
                    "3. Choose 'Excel Workbook (*.xlsx)' from dropdown\n"
                    "4. Save with a new name\n"
                    "Or rename the file to .csv extension and try again."
                )
            elif "No columns to parse from file" in error_str:
                raise ValueError(f"File '{os.path.basename(file_path)}' appears to be empty or has no readable data.")
            elif "File must have at least 2 columns" in error_str:
                raise ValueError(f"File '{os.path.basename(file_path)}' must contain at least wavenumber and emissivity columns.")
            else:
                raise ValueError(f"Spectra preprocessing failed: {error_str}")
    
    def load_spectrum(self, file_path):
        """Load a pre-processed spectrum file and return as DataFrame"""
        try:
            # Pre-processed files are always tab-separated with a header
            data_df = pd.read_csv(file_path, sep='\t')
            
            # Ensure required columns exist
            required_columns = ['Wavenumber', 'Emissivity', 'Uncertainty']
            missing_columns = [col for col in required_columns if col not in data_df.columns]
            
            if missing_columns:
                raise ValueError(f"File {file_path} is missing required columns: {missing_columns}")

            # Data should already be numeric, but check and clean just in case
            for col in required_columns:
                data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
            
            # Remove any rows that became NaN during conversion
            initial_rows = len(data_df)
            data_df = data_df.dropna()
            
            if len(data_df) < initial_rows:
                print(f"Warning: Removed {initial_rows - len(data_df)} invalid rows from {os.path.basename(file_path)}")
            
            if len(data_df) == 0:
                raise ValueError(f"No valid data in file {file_path}")
            
            # Data should already be sorted, but re-sorting is safe
            data_df = data_df.sort_values(by='Wavenumber').reset_index(drop=True)
            
            return data_df
            
        except Exception as e:
            raise ValueError(f"Failed to load spectrum from {file_path}: {str(e)}")
    
    def interpolate_spectrum(self, spectrum_df, target_wavenumbers):
        """Interpolate spectrum to match target wavenumbers without extrapolation."""
        source_wavenumbers = spectrum_df['Wavenumber'].values
        source_emissivity = spectrum_df['Emissivity'].values

        # Check if wavenumbers are identical
        if np.array_equal(source_wavenumbers, target_wavenumbers):
            return source_emissivity

        # Validate inputs
        if len(source_wavenumbers) != len(source_emissivity):
            raise ValueError("Wavenumber and emissivity arrays must have same length")
        
        if len(source_wavenumbers) < 2:
            raise ValueError("Need at least 2 data points for interpolation")

        # Check for overlapping ranges
        source_min, source_max = source_wavenumbers.min(), source_wavenumbers.max()
        target_min, target_max = target_wavenumbers.min(), target_wavenumbers.max()
        
        if target_min < source_min or target_max > source_max:
            print(f"Warning: Target range ({target_min:.1f}-{target_max:.1f}) extends beyond "
                  f"source range ({source_min:.1f}-{source_max:.1f}). Points outside range will be NaN.")

        try:
            # Use cubic spline interpolation, which will produce NaNs for points outside the original range
            cs = CubicSpline(source_wavenumbers, source_emissivity, extrapolate=False)
            interpolated_values = cs(target_wavenumbers)
            
            return interpolated_values
            
        except Exception as e:
            raise ValueError(f"Interpolation failed: {str(e)}")

    def get_file_info(self, file_path):
        """
        Get basic information about a spectral data file without fully processing it.
        Useful for file validation and preview.
        """
        try:
            file_format = self.validate_file_format(file_path)
            
            # Read first few rows to get basic info
            if file_format == 'excel':
                df_sample = pd.read_excel(file_path, nrows=10)
            elif file_format in ['csv', 'csv_disguised_as_excel']:
                df_sample = self.read_csv_with_detection(file_path)
                if len(df_sample) > 10:
                    df_sample = df_sample.head(10)
            elif file_format == 'txt':
                try:
                    df_sample = pd.read_csv(file_path, delimiter='\t', nrows=10)
                except:
                    df_sample = pd.read_csv(file_path, delimiter=',', nrows=10)
            else:
                return {"error": "Unsupported file format"}
            
            return {
                "format": file_format,
                "columns": list(df_sample.columns),
                "shape_preview": f"{len(df_sample)}+ rows, {len(df_sample.columns)} columns",
                "first_few_values": df_sample.head(3).to_dict('records') if not df_sample.empty else []
            }
            
        except Exception as e:
            return {"error": str(e)}
    
