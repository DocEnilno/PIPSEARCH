import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import subprocess
import threading
import os

class PipSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pip Package Search Engine")

        # Search bar
        self.search_label = tk.Label(root, text="Search for a package:")
        self.search_label.pack(pady=5)

        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.pack(pady=5)

        self.search_button = tk.Button(root, text="Search", command=self.search_packages)
        self.search_button.pack(pady=5)

        # Python version filter (you can add dynamic options)
        self.python_version_label = tk.Label(root, text="Filter by Python version:")
        self.python_version_label.pack(pady=5)

        self.python_version_combobox = ttk.Combobox(root, values=["Any", "3.7", "3.8", "3.9", "3.10"])
        self.python_version_combobox.set("Any")
        self.python_version_combobox.pack(pady=5)

        # Results list
        self.results_listbox = tk.Listbox(root, width=60, height=15)
        self.results_listbox.pack(pady=5)

        # Install button
        self.install_button = tk.Button(root, text="Install Selected Package", command=self.install_selected_package)
        self.install_button.pack(pady=5)

        # Status bar
        self.status_label = tk.Label(root, text="Status: Idle", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        # Directory selection for download
        self.download_dir_label = tk.Label(root, text="Select download directory:")
        self.download_dir_label.pack(pady=5)

        self.download_dir_button = tk.Button(root, text="Browse", command=self.select_directory)
        self.download_dir_button.pack(pady=5)

        self.download_dir = ""

    def search_packages(self):
        search_term = self.search_entry.get()
        python_version = self.python_version_combobox.get()

        if search_term:
            self.status_label.config(text="Searching...")
            threading.Thread(target=self.perform_search, args=(search_term, python_version)).start()
        else:
            messagebox.showwarning("Input Error", "Please enter a package name.")

    def perform_search(self, search_term, python_version):
        # Use the PyPI API to search for packages
        url = f"https://pypi.org/pypi/{search_term}/json"
        response = requests.get(url)

        self.results_listbox.delete(0, tk.END)

        if response.status_code == 200:
            package_data = response.json()
            package_name = package_data['info']['name']
            self.results_listbox.insert(tk.END, package_name)
            self.status_label.config(text=f"Found {package_name}.")
        else:
            self.status_label.config(text="No package found.")

    def select_directory(self):
        self.download_dir = filedialog.askdirectory()
        if self.download_dir:
            self.status_label.config(text=f"Download directory: {self.download_dir}")

    def install_selected_package(self):
        selected_package = self.results_listbox.get(tk.ACTIVE)
        if selected_package and self.download_dir:
            self.status_label.config(text=f"Installing {selected_package}...")
            threading.Thread(target=self.install_package, args=(selected_package,)).start()
        else:
            messagebox.showwarning("Selection Error", "Please select a package and download directory.")

    def install_package(self, package_name):
        command = [
            "pip", "install", package_name, 
            "--target", self.download_dir
        ]
        try:
            subprocess.check_call(command)
            self.status_label.config(text=f"Successfully installed {package_name}")
        except subprocess.CalledProcessError:
            self.status_label.config(text=f"Failed to install {package_name}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PipSearchGUI(root)
    root.mainloop()
