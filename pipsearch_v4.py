import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import subprocess
import threading
from bs4 import BeautifulSoup
import ast

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

        # Python version filter
        self.python_version_label = tk.Label(root, text="Filter by Python version:")
        self.python_version_label.pack(pady=5)

        self.python_version_combobox = ttk.Combobox(root, values=["Any", "3.7", "3.8", "3.9", "3.10"])
        self.python_version_combobox.set("Any")
        self.python_version_combobox.pack(pady=5)

        # Results list
        self.results_listbox = tk.Listbox(root, width=60, height=15)
        self.results_listbox.pack(pady=5)
        self.results_listbox.bind('<<ListboxSelect>>', self.display_package_info)

        # Version selection
        self.version_label = tk.Label(root, text="Select version (optional):")
        self.version_label.pack(pady=5)

        self.version_combobox = ttk.Combobox(root, values=[])
        self.version_combobox.pack(pady=5)

        # Install button
        self.install_button = tk.Button(root, text="Install Selected Package", command=self.install_selected_package)
        self.install_button.pack(pady=5)

        # Detailed package info
        self.package_info_label = tk.Label(root, text="Package Info:")
        self.package_info_label.pack(pady=5)

        self.package_info_text = tk.Text(root, height=10, wrap='word')
        self.package_info_text.pack(pady=5)

        # Dependencies info
        self.dependencies_label = tk.Label(root, text="Dependencies:")
        self.dependencies_label.pack(pady=5)

        self.dependencies_listbox = tk.Listbox(root, width=60, height=5)
        self.dependencies_listbox.pack(pady=5)
        self.dependencies_listbox.bind('<<ListboxSelect>>', self.search_dependency_in_main)

        # Status bar
        self.status_label = tk.Label(root, text="Status: Idle", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        # Directory selection for download
        self.download_dir_label = tk.Label(root, text="Select download directory:")
        self.download_dir_label.pack(pady=5)

        self.download_dir_button = tk.Button(root, text="Browse", command=self.select_directory)
        self.download_dir_button.pack(pady=5)

        self.download_dir = ""
        self.package_data = {}

        # Button to select a .py file
        self.select_file_button = tk.Button(root, text="Select .py File", command=self.select_python_file)
        self.select_file_button.pack(pady=5)

    def search_packages(self):
        search_term = self.search_entry.get()
        python_version = self.python_version_combobox.get()

        if search_term:
            self.status_label.config(text="Searching...")
            threading.Thread(target=self.perform_search, args=(search_term, python_version)).start()
        else:
            messagebox.showwarning("Input Error", "Please enter a package name.")

    def perform_search(self, search_term, python_version):
        url = f"https://pypi.org/pypi?%3Aaction=search&term={search_term}&submit=search"
        response = requests.get(url)

        self.results_listbox.delete(0, tk.END)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.find_all('a', class_='package-snippet')

            for project in search_results:
                package_name = project.find('span', class_='package-snippet__name').text.strip()
                summary_element = project.find('span', class_='package-snippet__description')
                summary = summary_element.text.strip() if summary_element else "No summary available"

                self.results_listbox.insert(tk.END, package_name)
                self.package_data[package_name] = {
                    'url': project['href'],
                    'summary': summary
                }

            self.status_label.config(text=f"Found {len(search_results)} packages.")
        else:
            self.status_label.config(text="No package found.")

    def select_directory(self):
        self.download_dir = filedialog.askdirectory()
        if self.download_dir:
            self.status_label.config(text=f"Download directory: {self.download_dir}")

    def select_python_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file_path:
            dependencies = self.get_imports(file_path)
            self.dependencies_listbox.delete(0, tk.END)
            for dep in dependencies:
                self.dependencies_listbox.insert(tk.END, dep)

    def get_imports(self, file_path):
        with open(file_path, 'r') as file:
            node = ast.parse(file.read(), filename=file_path)
            imports = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Import):
                    for alias in n.names:
                        imports.add(alias.name)  # Use 'name' instead of 'id'
                elif isinstance(n, ast.ImportFrom):
                    imports.add(n.module)  # Add the module name for 'from ... import ...'
                    for alias in n.names:
                        imports.add(alias.name)  # Use 'name' instead of 'id'
            return imports

    def install_selected_package(self):
        selected_package = self.results_listbox.get(tk.ACTIVE)
        if not selected_package:
            selected_package = self.search_entry.get().strip()

        if selected_package:
            self.status_label.config(text=f"Installing {selected_package}...")
            threading.Thread(target=self.install_package, args=(selected_package,)).start()
        else:
            messagebox.showwarning("Selection Error", "Please select a package.")

    def install_package(self, package_name):
        version = self.version_combobox.get().strip()

        if version:
            package_name = f"{package_name}=={version}"

        command = ["pip", "install", package_name]

        if self.download_dir:
            command.extend(["--target", self.download_dir])

        try:
            subprocess.check_call(command)
            self.status_label.config(text=f"Successfully installed {package_name}")
            self.fetch_dependencies(package_name)
        except subprocess.CalledProcessError:
            self.status_label.config(text=f"Failed to install {package_name}")

    def display_package_info(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            package_name = event.widget.get(index)
            package_info = self.package_data.get(package_name, {})

            self.package_info_text.delete(1.0, tk.END)
            self.package_info_text.insert(tk.END, f"Name: {package_name}\n")
            self.package_info_text.insert(tk.END, f"Summary: {package_info.get('summary', 'No summary available')}\n")
            self.package_info_text.insert(tk.END, f"URL: {package_info.get('url')}\n")

            self.fetch_available_versions(package_name)

    def fetch_available_versions(self, package_name):
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)

        if response.status_code == 200:
            versions = response.json().get('releases', {}).keys()
            self.version_combobox['values'] = sorted(versions)
            self.version_combobox.set("")  # Reset the selection
        else:
            self.version_combobox['values'] = []
            messagebox.showerror("Error", "Could not fetch available versions.")

    def fetch_dependencies(self, package_name):
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)

        if response.status_code == 200:
            dependencies = response.json().get('info', {}).get('requires_dist', [])
            self.dependencies_listbox.delete(0, tk.END)
            for dep in dependencies:
                self.dependencies_listbox.insert(tk.END, dep)
        else:
            messagebox.showerror("Error", "Could not fetch dependencies.")

    def search_dependency_in_main(self, event):
        selection = event.widget.curselection()
        if selection:
            dependency = event.widget.get(selection[0])
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, dependency)
            self.search_packages()

if __name__ == "__main__":
    root = tk.Tk()
    app = PipSearchGUI(root)
    root.mainloop()
