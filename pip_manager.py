import tkinter as tk
from tkinter import ttk, messagebox
import pkg_resources
import subprocess
import os
import threading

class PipPackageManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pip Package Manager")

        # Search bar
        self.search_label = tk.Label(root, text="Search for a package:")
        self.search_label.pack(pady=5)

        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.pack(pady=5)

        self.search_button = tk.Button(root, text="Search", command=self.search_packages)
        self.search_button.pack(pady=5)

        # Results list
        self.results_listbox = tk.Listbox(root, width=60, height=15)
        self.results_listbox.pack(pady=5)
        self.results_listbox.bind('<<ListboxSelect>>', self.display_package_info)

        # Action buttons
        self.uninstall_button = tk.Button(root, text="Uninstall Selected Package", command=self.uninstall_selected_package)
        self.uninstall_button.pack(pady=5)

        self.reinstall_button = tk.Button(root, text="Reinstall Selected Package", command=self.reinstall_selected_package)
        self.reinstall_button.pack(pady=5)

        self.open_path_button = tk.Button(root, text="Open Package File Path", command=self.open_package_path)
        self.open_path_button.pack(pady=5)

        # Package info
        self.package_info_label = tk.Label(root, text="Package Info:")
        self.package_info_label.pack(pady=5)

        self.package_info_text = tk.Text(root, height=10, wrap='word')
        self.package_info_text.pack(pady=5)

        # Status bar
        self.status_label = tk.Label(root, text="Status: Idle", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        self.installed_packages = {}
        self.load_installed_packages()

    def load_installed_packages(self):
        self.installed_packages = {pkg.project_name: pkg for pkg in pkg_resources.working_set}
        self.update_results_listbox()

    def update_results_listbox(self):
        self.results_listbox.delete(0, tk.END)
        for package_name in sorted(self.installed_packages.keys()):
            self.results_listbox.insert(tk.END, package_name)

    def search_packages(self):
        search_term = self.search_entry.get().lower()
        self.results_listbox.delete(0, tk.END)

        for package_name in sorted(self.installed_packages.keys()):
            if search_term in package_name.lower():
                self.results_listbox.insert(tk.END, package_name)

        if not self.results_listbox.size():
            messagebox.showinfo("No Results", "No packages found matching your search.")

    def display_package_info(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            package_name = event.widget.get(index)
            package = self.installed_packages.get(package_name)

            self.package_info_text.delete(1.0, tk.END)
            if package:
                self.package_info_text.insert(tk.END, f"Name: {package.project_name}\n")
                self.package_info_text.insert(tk.END, f"Version: {package.version}\n")
                self.package_info_text.insert(tk.END, f"Location: {package.location}\n")
            else:
                self.package_info_text.insert(tk.END, "Package not found.")

    def uninstall_selected_package(self):
        selected_package = self.results_listbox.get(tk.ACTIVE)
        if selected_package:
            self.status_label.config(text=f"Uninstalling {selected_package}...")
            threading.Thread(target=self.uninstall_package, args=(selected_package,)).start()
        else:
            messagebox.showwarning("Selection Error", "Please select a package to uninstall.")

    def uninstall_package(self, package_name):
        command = ["pip", "uninstall", "-y", package_name]
        try:
            subprocess.check_call(command)
            self.status_label.config(text=f"Successfully uninstalled {package_name}.")
            self.load_installed_packages()  # Refresh the package list
        except subprocess.CalledProcessError:
            self.status_label.config(text=f"Failed to uninstall {package_name}.")

    def reinstall_selected_package(self):
        selected_package = self.results_listbox.get(tk.ACTIVE)
        if selected_package:
            self.status_label.config(text=f"Reinstalling {selected_package}...")
            threading.Thread(target=self.reinstall_package, args=(selected_package,)).start()
        else:
            messagebox.showwarning("Selection Error", "Please select a package to reinstall.")

    def reinstall_package(self, package_name):
        command = ["pip", "install", "--force-reinstall", package_name]
        try:
            subprocess.check_call(command)
            self.status_label.config(text=f"Successfully reinstalled {package_name}.")
        except subprocess.CalledProcessError:
            self.status_label.config(text=f"Failed to reinstall {package_name}.")

    def open_package_path(self):
        selected_package = self.results_listbox.get(tk.ACTIVE)
        if selected_package:
            package = self.installed_packages.get(selected_package)
            if package:
                package_path = package.location
                os.startfile(package_path)  # Open the package file path
            else:
                messagebox.showwarning("Selection Error", "Package not found.")
        else:
            messagebox.showwarning("Selection Error", "Please select a package to open its path.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PipPackageManagerGUI(root)
    root.mainloop()
