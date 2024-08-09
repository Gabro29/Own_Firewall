import psutil
import os
import platform
from tkinter import Tk, Frame, Button, Entry, Scrollbar, messagebox, StringVar
from tkinter.ttk import Treeview, Style


class NetworkProcessController:
    def __init__(self, master):
        self.master = master
        self.master.title("Network Process Controller")

        self.master.configure(bg="#2e2e2e")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        self.main_frame = Frame(self.master, bg="#2e2e2e")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.button_frame = Frame(self.main_frame, bg="#2e2e2e")
        self.button_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        button_style = {
            "fg": "white",
            "bg": "#5a5a5a",
            "activebackground": "#4a4a4a",
            "font": ("Lucida Console", 12, "bold"),
            "relief": "raised",
            "borderwidth": 3
        }

        self.search_var = StringVar()
        self.search_var.trace("w", self.update_listbox)

        self.search_entry = Entry(self.button_frame, textvariable=self.search_var, font=("Lucida Console", 12))
        self.search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.refresh_button = Button(self.button_frame, text="Refresh", command=self.refresh_processes, **button_style)
        self.refresh_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.block_button = Button(self.button_frame, text="Block Internet", command=self.on_block, **button_style)
        self.block_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.unblock_button = Button(self.button_frame, text="Unblock Internet", command=self.on_unblock, **button_style)
        self.unblock_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.columnconfigure(2, weight=1)
        self.button_frame.columnconfigure(3, weight=1)

        self.process_frame = Frame(self.main_frame, bg="#2e2e2e")
        self.process_frame.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")
        self.process_frame.rowconfigure(0, weight=1)
        self.process_frame.columnconfigure(0, weight=1)

        self.style = Style()
        self.style.configure("Treeview", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e", font=("Lucida Console", 12))
        self.style.map("Treeview", background=[("selected", "#4a4a4a")], foreground=[("selected", "white")])

        self.tree = Treeview(self.process_frame, columns=("PID", "Path"), show="headings")
        self.tree.heading("PID", text="PID")
        self.tree.heading("Path", text="Executable Path")
        self.tree.column("PID", width=100, anchor="center")
        self.tree.column("Path", anchor="w")

        self.scrollbar = Scrollbar(self.process_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.refresh_processes()

    def get_processes(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def filter_network_processes(self, processes):
        network_processes = []
        for proc in processes:
            try:
                connections = psutil.Process(proc['pid']).connections(kind='inet')
                if connections:
                    network_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return network_processes

    def block_internet(self, pid, exe):
        system = platform.system()
        if system == 'Windows':
            os.system(f'netsh advfirewall firewall add rule name="Block {exe}" dir=out action=block program="{exe}" enable=yes')
        elif system == 'Linux':
            os.system(f'sudo iptables -A OUTPUT -p tcp -m owner --pid-owner {pid} -j REJECT')
        else:
            messagebox.showerror("Unsupported OS", "This script supports only Windows and Linux.")

    def unblock_internet(self, pid, exe):
        system = platform.system()
        if system == 'Windows':
            os.system(f'netsh advfirewall firewall delete rule name="Block {exe}" program="{exe}"')
        elif system == 'Linux':
            os.system(f'sudo iptables -D OUTPUT -p tcp -m owner --pid-owner {pid} -j REJECT')
        else:
            messagebox.showerror("Unsupported OS", "This script supports only Windows and Linux.")

    def on_block(self):
        try:
            selected_item = self.tree.selection()[0]
            selected = self.tree.item(selected_item)['values']
            selected_pid = selected[0]
            selected_exe = selected[1]
            self.block_internet(selected_pid, selected_exe)
            messagebox.showinfo("Success", f"Blocked internet for PID {selected_pid}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_unblock(self):
        try:
            selected_item = self.tree.selection()[0]
            selected = self.tree.item(selected_item)['values']
            selected_pid = selected[0]
            selected_exe = selected[1]
            self.unblock_internet(selected_pid, selected_exe)
            messagebox.showinfo("Success", f"Unblocked internet for PID {selected_pid}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_processes(self):
        self.tree.delete(*self.tree.get_children())
        self.processes = self.get_processes()
        self.network_processes = self.filter_network_processes(self.processes)
        self.update_listbox()

    def update_listbox(self, *args):
        search_term = self.search_var.get().lower()
        filtered_processes = [proc for proc in self.network_processes if search_term in str(proc['name']).lower() or search_term in str(proc['exe']).lower()]
        self.tree.delete(*self.tree.get_children())
        for i, proc in enumerate(filtered_processes):
            if i % 2 == 0:
                self.tree.insert('', 'end', values=(proc['pid'], proc['exe']), tags=('evenrow',))
            else:
                self.tree.insert('', 'end', values=(proc['pid'], proc['exe']), tags=('oddrow',))
        self.tree.tag_configure('evenrow', background='#1e1e1e')
        self.tree.tag_configure('oddrow', background='#2e2e2e')


def main():
    root = Tk()
    app = NetworkProcessController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
