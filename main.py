#!/usr/bin/env python3
"""
Mineral Spectra Analyzer - Main Application Entry Point
"""

import ttkbootstrap as tb
from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Create the main window with theme
    root = tb.Window(themename="superhero")
    root.title("Mineral Spectra Analyzer")
    
    # Initialize the application
    app = MainWindow(root)
    
    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    main()
