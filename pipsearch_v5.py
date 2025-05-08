import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import subprocess
import threading
from bs4 import BeautifulSoup
import ast
import sys
import io

class OutputRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.config(state=tk.NORMAL)  # Enable the widget for writing
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Scroll to the end
        self.text_widget.config(state=tk.DISABLED)  # Disable it again

    def flush(self):
        pass  # Needed for Python 3 compatibility

class PipSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pip Package Search Engine")

        # Redirect output
        self.output_text = tk.Text(root, height=10, wrap='word', state=tk.NORMAL)
        self.output_text.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky='nsew')
        sys.stdout = OutputRedirector(self.output_text)

        # Make console output read-only
        self.output_text.config(state=tk.DISABLED)

        # Configure grid
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Search bar
        self.search_label = tk.Label(root, text="Search for a package:")
        self.search_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        self.search_entry = tk.Entry(root, width=40)
        self.search_entry.grid(row=1, column=1, padx=5, pady=5)

        self.search_button = tk.Button(root, text="Search", command=self.search_packages)
        self.search_button.grid(row=1, column=2, padx=5, pady=5)

        # Python version filter
        self.python_version_label = tk.Label(root, text="Filter by Python version:")
        self.python_version_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')

        self.python_version_combobox = ttk.Combobox(root, values=["Any", "3.7", "3.8", "3.9", "3.10"], width=20)
        self.python_version_combobox.set("Any")
        self.python_version_combobox.grid(row=2, column=1, padx=5, pady=5)

        # Results list
        self.results_listbox = tk.Listbox(root, width=60, height=10)
        self.results_listbox.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        self.results_listbox.bind('<<ListboxSelect>>', self.display_package_info)

        # Version selection
        self.version_label = tk.Label(root, text="Select version (optional):")
        self.version_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')

        self.version_combobox = ttk.Combobox(root, values=[], width=20)
        self.version_combobox.grid(row=4, column=1, padx=5, pady=5)

        # Install button
        self.install_button = tk.Button(root, text="Install Selected Package", command=self.install_selected_package)
        self.install_button.grid(row=4, column=2, padx=5, pady=5)

        # Install all dependencies button
        self.install_all_button = tk.Button(root, text="Install All Dependencies", command=self.install_all_dependencies)
        self.install_all_button.grid(row=5, column=2, padx=5, pady=5)

        # Detailed package info
        self.package_info_label = tk.Label(root, text="Package Info:")
        self.package_info_label.grid(row=6, column=0, padx=5, pady=5, sticky='w')

        self.package_info_text = tk.Text(root, height=5, wrap='word')
        self.package_info_text.grid(row=6, column=1, columnspan=2, padx=10, pady=5)

        # Dependencies info
        self.dependencies_label = tk.Label(root, text="Dependencies:")
        self.dependencies_label.grid(row=7, column=0, padx=5, pady=5, sticky='w')

        self.dependencies_listbox = tk.Listbox(root, width=60, height=5)
        self.dependencies_listbox.grid(row=7, column=1, columnspan=2, padx=10, pady=5)
        self.dependencies_listbox.bind('<<ListboxSelect>>', self.search_dependency_in_main)

        # Status bar
        self.status_label = tk.Label(root, text="Status: Idle", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=8, column=0, columnspan=3, sticky='ew')

        # Directory selection for download
        self.download_dir_label = tk.Label(root, text="Select download directory:")
        self.download_dir_label.grid(row=9, column=0, padx=5, pady=5, sticky='w')

        self.download_dir_button = tk.Button(root, text="Browse", command=self.select_directory)
        self.download_dir_button.grid(row=9, column=1, padx=5, pady=5)

        self.download_dir = ""
        self.package_data = {}
        self.all_dependencies = []  # Store all dependencies found

        # Button to select a .py file
        self.select_file_button = tk.Button(root, text="Select .py File", command=self.select_python_file)
        self.select_file_button.grid(row=9, column=2, padx=5, pady=5)

        # Adjust grid weights
        for i in range(10):
            root.grid_rowconfigure(i, weight=1)

    def search_packages(self):
        search_term = self.search_entry.get()
        python_version = self.python_version_combobox.get()

        if search_term:
            self.status_label.config(text="Searching...")
            print("Searching for packages...")
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

            print(f"Found {len(search_results)} packages.")
            self.status_label.config(text=f"Found {len(search_results)} packages.")
        else:
            print("No package found.")
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
            self.all_dependencies = dependencies  # Store dependencies
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
                    imports.add(n.module)
            return imports

    def install_selected_package(self):
        selection = self.results_listbox.curselection()
        if selection:
            package_name = self.results_listbox.get(selection[0])
            version = self.version_combobox.get()
            if version:
                package_name = f"{package_name}=={version}"

            threading.Thread(target=self.install_package, args=(package_name,)).start()
        else:
            messagebox.showwarning("Selection Error", "Please select a package to install.")

    def install_all_dependencies(self):
        if not self.all_dependencies:
            messagebox.showwarning("No Dependencies", "No dependencies found to install.")
            return

        for dep in self.all_dependencies:
            threading.Thread(target=self.install_package, args=(dep,)).start()

    def install_package(self, package_name):
        self.status_label.config(text=f"Installing {package_name}...")
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--target", self.download_dir])
            self.status_label.config(text=f"Successfully installed {package_name}")
            self.fetch_available_versions(package_name)  # Refresh versions after installation
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e.output}")
            self.status_label.config(text=f"Failed to install {package_name}")

    def display_package_info(self, event):
        selection = event.widget.curselection()
        if selection:
            package_name = event.widget.get(selection[0])
            info = self.package_data.get(package_name)
            self.package_info_text.delete(1.0, tk.END)

            if info:
                self.package_info_text.insert(tk.END, f"Name: {package_name}\n")
                self.package_info_text.insert(tk.END, f"Summary: {info['summary']}\n")
                self.package_info_text.insert(tk.END, f"URL: {info['url']}\n")
                self.fetch_dependencies(package_name)
                self.fetch_available_versions(package_name)  # Fetch versions when package info is displayed
            else:
                self.package_info_text.insert(tk.END, "No additional information available.")

    def fetch_dependencies(self, package_name):
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)

        if response.status_code == 200:
            dependencies = response.json().get('info', {}).get('requires_dist', [])
            if dependencies is None:  # Check if dependencies are None
                dependencies = []  # Set to an empty list if None
            self.dependencies_listbox.delete(0, tk.END)
            for dep in dependencies:
                self.dependencies_listbox.insert(tk.END, dep)
        else:
            print("Could not fetch dependencies.")
            messagebox.showerror("Error", "Could not fetch dependencies.")

    def fetch_available_versions(self, package_name):
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)

        if response.status_code == 200:
            versions = sorted(response.json().get('releases', {}).keys(), key=lambda x: list(map(int, x.split('.'))), reverse=True)
            self.version_combobox['values'] = versions
            if versions:
                self.version_combobox.current(0)  # Set to the newest version by default
        else:
            print("Could not fetch versions.")
            messagebox.showerror("Error", "Could not fetch versions.")

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
