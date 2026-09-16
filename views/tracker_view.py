import os
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    tk = None
    messagebox = None
    ttk = None
    TKINTER_AVAILABLE = False
from datetime import date
from logger import logger
from controllers.tracker_controller import TrackerController
from controllers.auth_controller import AuthController
import time

class TrackerWindow:
    def __init__(self, root, username="", on_logout=None):
        self.root = root
        self.controller = TrackerController()
        self.on_logout = on_logout
        self.username = username

        self.root.title("Campus Hardware Inventory System")
        self.root.geometry("1200x620")

        header_frame = tk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(header_frame, text="Hardware Inventory Dashboard", font=("Arial", 16, "bold")).pack(side="left")
        self.lbl_total_value = tk.Label(header_frame, text="Total Inventory Value: $0.00", font=("Arial", 12, "bold"))
        self.lbl_total_value.pack(side="left", padx=20)

        if self.username:
            tk.Label(header_frame, text=f"Signed in as: {self.username}", font=("Arial", 10, "italic")).pack(side="left", padx=20)

        # show admin approvals button only for admins
        self.auth = AuthController()
        try:
            role = self.auth.get_user_role(self.username) if self.username else None
        except Exception:
            role = None
        self.is_admin = str(role).strip().lower() == 'admin'
        if self.is_admin:
            btn_admin = tk.Button(header_frame, text="Admin Approvals", command=self.open_admin_approvals, bg="#607D8B", fg="white", width=14)
            btn_admin.pack(side="right", padx=5)

        # My Profile & Security available to all logged-in users
        if self.username:
            btn_profile = tk.Button(header_frame, text="My Profile & Security", command=self.open_profile, bg="#455A64", fg="white", width=18)
            btn_profile.pack(side="right", padx=5)

        btn_logout = tk.Button(header_frame, text="Logout", command=self.logout, bg="#f44336", fg="white", width=12)
        btn_logout.pack(side="right")


        # Search and filter controls
        filter_frame = tk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=(0,5))

        tk.Label(filter_frame, text="Search:").pack(side="left", padx=(4,2))
        self.search_var = tk.StringVar()
        self.entry_search = tk.Entry(filter_frame, textvariable=self.search_var, width=30)
        self.entry_search.pack(side="left", padx=(0,6))
        self.entry_search.bind('<Return>', lambda e: self.load_data())

        tk.Label(filter_frame, text="Category:").pack(side="left", padx=(6,2))
        self.category_var = tk.StringVar(value='All')
        categories = ['All'] + self.controller.get_categories()
        self.category_menu = tk.OptionMenu(filter_frame, self.category_var, *categories)
        self.category_menu.pack(side="left", padx=(0,6))

        tk.Label(filter_frame, text="Status:").pack(side="left", padx=(6,2))
        self.status_var = tk.StringVar(value='All')
        self.status_menu = tk.OptionMenu(filter_frame, self.status_var, 'All', 'In Stock', 'Low Stock', 'Out of Stock')
        self.status_menu.pack(side="left", padx=(0,6))

        tk.Button(filter_frame, text="Filter", command=self.load_data, bg="#2196F3", fg="white").pack(side="left", padx=4)

        filter_spacer = tk.Frame(filter_frame)
        filter_spacer.pack(side="left", fill="x", expand=True)
        tk.Button(filter_frame, text="Transaction History", command=self.open_borrow_records, bg="#795548", fg="white", width=17).pack(side="right", padx=5)
        tk.Button(filter_frame, text="Borrow Items", command=self.open_borrow_dialog, bg="#4CAF50", fg="white", width=13).pack(side="right", padx=5)
        
        if self.is_admin:
            frame_form = tk.LabelFrame(self.root, text="Add New Item", padx=10, pady=10)
            frame_form.pack(padx=10, pady=5, fill="x")

            tk.Label(frame_form, text="Item Name:").grid(row=0, column=0, sticky="e")
            self.entry_item = tk.Entry(frame_form, width=25)
            self.entry_item.grid(row=0, column=1, padx=5, pady=5)

            tk.Label(frame_form, text="Category:").grid(row=0, column=2, sticky="e")
            self.entry_category = tk.Entry(frame_form, width=25)
            self.entry_category.grid(row=0, column=3, padx=5, pady=5)

            tk.Label(frame_form, text="Quantity:").grid(row=0, column=4, sticky="e")
            self.entry_quantity = tk.Entry(frame_form, width=25)
            self.entry_quantity.grid(row=0, column=5, padx=5, pady=5)

            tk.Label(frame_form, text="Unit Price ($):").grid(row=0, column=6, sticky="e")
            self.entry_price = tk.Entry(frame_form, width=25)
            self.entry_price.grid(row=0, column=7, padx=5, pady=5)

            btn_add = tk.Button(frame_form, text="Save Item", command=self.add_item, bg="#4CAF50", fg="white")
            btn_add.grid(row=0, column=8, padx=5, pady=1, sticky="ew")

        btn_export = tk.Button(self.root, text="Export Inventory to CSV Report", command=self.export_inventory, bg="#2196F3", fg="white")
        btn_export.pack(padx=10, pady=5, anchor="e")

        frame_table = tk.LabelFrame(self.root)
        frame_table.pack(padx=10, pady=5, fill="both", expand=True)

        scroll_y = tk.Scrollbar(frame_table, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(
            frame_table,
            columns=("ID", "Name", "Category", "Qty", "Price ($)", "Status"),
            show="headings",
            yscrollcommand=scroll_y.set,
        )
        scroll_y.config(command=self.tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Qty", text="Qty")
        self.tree.heading("Price ($)", text="Price ($)")
        self.tree.heading("Status", text="Status")

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Name", width=250)
        self.tree.column("Category", width=150)
        self.tree.column("Qty", width=90, anchor="center")
        self.tree.column("Price ($)", width=100, anchor="center")
        self.tree.column("Status", width=120, anchor="center")

        self.tree.tag_configure("out_of_stock", background="#ffcdd2")
        self.tree.tag_configure("low_stock", background="#fff9c4")
        self.tree.tag_configure("in_stock", background="#c8e6c9")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.show_item_quantity_details)

        if self.is_admin:
            frame_update = tk.LabelFrame(self.root, text="Update Selected Item", padx=10, pady=5)
            frame_update.pack(padx=10, pady=5, fill="x")

            tk.Label(frame_update, text="New Quantity:").grid(row=0, column=0, padx=5, pady=5)
            self.entry_update_quantity = tk.Entry(frame_update, width=25)
            self.entry_update_quantity.grid(row=0, column=1, padx=5, pady=5)

            btn_update_quantity = tk.Button(frame_update, text="Update Quantity", command=self.update_quantity, bg="#2196F3", fg="white")
            btn_update_quantity.grid(row=0, column=2, padx=10, pady=5)

            tk.Label(frame_update, text="New Unit Price ($):").grid(row=0, column=3, padx=5, pady=5)
            self.entry_update_price = tk.Entry(frame_update, width=25)
            self.entry_update_price.grid(row=0, column=4, padx=5, pady=5)

            btn_update_price = tk.Button(frame_update, text="Update Price", command=self.update_price, bg="#2196F3", fg="white")
            btn_update_price.grid(row=0, column=5, padx=10, pady=5)

            btn_delete = tk.Button(self.root, text="Delete Selected Item", command=self.delete_item, bg="#f44336", fg="white")
            btn_delete.pack(pady=10, fill="x", padx=10)

        self.load_data()
        self.auto_refresh()

    def logout(self):
        if self.on_logout:
            logger.info(f"User '{self.username}' logged out.")
            self.on_logout()

    def add_item(self):
        item_name = self.entry_item.get().strip()
        category = self.entry_category.get().strip() or "Uncategorized"
        quantity = self.entry_quantity.get().strip()
        unit_price = self.entry_price.get().strip()

        try:
            q = int(quantity) if quantity else 0
        except ValueError:
            logger.warning("Add item validation failed: Quantity must be an integer.")
            messagebox.showerror("Type Error", "Quantity must be an integer.")
            return

        try:
            p = float(unit_price) if unit_price else 0.0
        except ValueError:
            logger.warning("Add item validation failed: Price must be numeric.")
            messagebox.showerror("Type Error", "Price must be numeric.")
            return

        success, msg = self.controller.add_item(item_name, category, q, p)
        if not success:
            messagebox.showerror("Input Error", msg)
            return

        self.entry_item.delete(0, tk.END)
        self.entry_category.delete(0, tk.END)
        self.entry_quantity.delete(0, tk.END)
        self.entry_price.delete(0, tk.END)
        self.load_data()
        messagebox.showinfo("Success", msg)

    def update_quantity(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a row from the table to update.")
            return

        item_values = self.tree.item(selected[0], "values")
        item_id = item_values[0]
        new_quantity = self.entry_update_quantity.get().strip()

        try:
            q = int(new_quantity)
        except ValueError:
            logger.warning("Update quantity validation failed: Quantity must be an integer.")
            messagebox.showerror("Type Error", "Quantity must be an integer.")
            return

        success, msg = self.controller.update_quantity(item_id, q)
        if not success:
            messagebox.showerror("Update Error", msg)
            return

        self.load_data()
        messagebox.showinfo("Success", msg)

    def update_price(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a row from the table to update.")
            return

        item_values = self.tree.item(selected[0], "values")
        item_id = item_values[0]
        new_price = self.entry_update_price.get().strip()

        try:
            p = float(new_price)
        except ValueError:
            logger.warning("Update price validation failed: Price must be numeric.")
            messagebox.showerror("Type Error", "Price must be numeric.")
            return

        success, msg = self.controller.update_price(item_id, p)
        if not success:
            messagebox.showerror("Update Error", msg)
            return

        self.load_data()
        messagebox.showinfo("Success", msg)

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a row to delete.")
            return

        item_values = self.tree.item(selected[0], "values")
        item_id = item_values[0]

        success, msg = self.controller.delete_item(item_id)
        if not success:
            messagebox.showerror("Delete Error", msg)
            return

        self.load_data()
        messagebox.showinfo("Deleted", msg)

    def show_item_quantity_details(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        item_id = self.tree.item(selected[0], "values")[0]
        details = self.controller.get_item_quantity_details(item_id)
        if not details:
            messagebox.showerror("Item Error", "The selected item could not be found.")
            return
        item_name, available_quantity, borrowed_quantity, total_quantity = details
        messagebox.showinfo(
            "Item Quantity Details",
            f"Item: {item_name}\n\n"
            f"Available Quantity: {available_quantity}\n"
            f"Borrowed Quantity: {borrowed_quantity}\n"
            f"Total Quantity: {total_quantity}",
        )

    def export_inventory(self):
        csv_path = os.path.abspath("inventory_report.csv")
        success, result = self.controller.export_to_csv(csv_path)
        if success:
            messagebox.showinfo("Export Successful", f"Inventory exported to '{result}'.")
        else:
            messagebox.showerror("Export Failed", result)

    def open_borrow_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Borrow Items")
        dialog.geometry("720x620")
        dialog.transient(self.root)

        details = tk.LabelFrame(dialog, text="Borrower and Usage Details", padx=10, pady=8)
        details.pack(fill="x", padx=10, pady=8)
        fields = [
            ("Student Name", "student_name"), ("Student ID", "student_id"),
            ("Date", "borrow_date"), ("Class", "class_name"),
            ("Schedule", "schedule"), ("Room", "room"),
        ]
        entries = {}
        for index, (label, key) in enumerate(fields):
            row, column = divmod(index, 2)
            tk.Label(details, text=f"{label}:").grid(row=row, column=column * 2, sticky="e", padx=5, pady=5)
            entry = tk.Entry(details, width=25)
            entry.grid(row=row, column=column * 2 + 1, sticky="w", padx=5, pady=5)
            if key == "borrow_date":
                entry.insert(0, date.today().isoformat())
            entries[key] = entry

        item_frame = tk.LabelFrame(dialog, text="Items and Quantity", padx=10, pady=8)
        item_frame.pack(fill="both", expand=True, padx=10, pady=5)
        tk.Label(item_frame, text="Select", width=10, anchor="w").grid(row=0, column=0, sticky="w")
        tk.Label(item_frame, text="Item", width=30, anchor="w").grid(row=0, column=1, sticky="w")
        tk.Label(item_frame, text="Available", width=12, anchor="w").grid(row=0, column=2, sticky="w")
        tk.Label(item_frame, text="Borrow Qty", width=12, anchor="w").grid(row=0, column=3, sticky="w")
        item_controls = []
        row_index = 1
        for item in self.controller.fetch_all_items():
            item_id, item_name, _, available, _, _ = item
            if available <= 0:
                continue
            selected = tk.BooleanVar(value=False)
            quantity = tk.Entry(item_frame, width=12)
            tk.Checkbutton(item_frame, variable=selected).grid(row=row_index, column=0)
            tk.Label(item_frame, text=item_name).grid(row=row_index, column=1, sticky="w")
            tk.Label(item_frame, text=str(available)).grid(row=row_index, column=2, sticky="w")
            quantity.grid(row=row_index, column=3, sticky="w")
            item_controls.append((item_id, item_name, available, selected, quantity))
            row_index += 1

        def save_borrow():
            selected_items = []
            try:
                for item_id, item_name, available, selected, quantity in item_controls:
                    if selected.get():
                        requested_quantity = int(quantity.get().strip())
                        if requested_quantity > available:
                            messagebox.showerror(
                                "Quantity Error",
                                f"The requested quantity for '{item_name}' exceeds available stock ({available}).",
                                parent=dialog,
                            )
                            return
                        selected_items.append((item_id, requested_quantity))
            except ValueError:
                messagebox.showerror("Input Error", "Borrow quantities must be whole numbers.", parent=dialog)
                return
            values = {key: entry.get().strip() for key, entry in entries.items()}
            ok, msg = self.controller.borrow_items(
                values["student_name"], values["student_id"], values["borrow_date"],
                values["class_name"], values["schedule"], values["room"], selected_items, self.username
            )
            if not ok:
                messagebox.showerror("Borrow Error", msg, parent=dialog)
                return
            dialog.destroy()
            self.load_data()
            messagebox.showinfo("Borrow Successful", msg)

        tk.Button(dialog, text="Submit Transaction Request", command=save_borrow, bg="#4CAF50", fg="white").pack(side="left", padx=10, pady=10)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side="right", padx=10, pady=10)

    def open_borrow_records(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Transaction History")
        dialog.geometry("1180x430")
        columns = ("ID", "Student Name", "Student ID", "Date", "Class", "Schedule", "Room", "Status", "Returned At")
        tree = ttk.Treeview(dialog, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=110, anchor="center")
        tree.column("Student Name", width=150)
        tree.column("Schedule", width=140)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def load_records():
            for child in tree.get_children():
                tree.delete(child)
            for record in self.controller.fetch_borrow_records(is_admin=self.is_admin):
                tree.insert("", tk.END, values=record)

        def show_items(_event=None):
            selected = tree.selection()
            if not selected:
                return
            borrow_id = tree.item(selected[0], "values")[0]
            items = self.controller.get_borrow_items(borrow_id)
            messagebox.showinfo("Transaction Items", "\n".join(f"{name}: {quantity}" for name, quantity in items), parent=dialog)

        def update_selected(action):
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Selection Error", "Select a transaction first.", parent=dialog)
                return
            values = tree.item(selected[0], "values")
            action_text = {"approve": "approve", "decline": "decline", "return": "process the return"}[action]
            if not messagebox.askyesno("Confirm Transaction", f"Are you sure you want to {action_text} transaction #{values[0]}?", parent=dialog):
                return
            operation = {
                "approve": lambda: self.controller.approve_borrow(values[0], self.is_admin),
                "decline": lambda: self.controller.decline_borrow(values[0], self.is_admin),
                "return": lambda: self.controller.return_borrow(values[0], self.is_admin),
            }[action]
            ok, msg = operation()
            if ok:
                self.load_data()
                load_records()
                messagebox.showinfo("Transaction Updated", msg, parent=dialog)
            else:
                messagebox.showerror("Transaction Error", msg, parent=dialog)

        tree.bind("<Double-1>", show_items)
        buttons = tk.Frame(dialog)
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        if self.is_admin:
            tk.Button(buttons, text="Accept", command=lambda: update_selected("approve"), bg="#4CAF50", fg="white").pack(side="left")
            tk.Button(buttons, text="Deny", command=lambda: update_selected("decline"), bg="#f44336", fg="white").pack(side="left", padx=6)
            tk.Button(buttons, text="Return", command=lambda: update_selected("return"), bg="#FF9800", fg="white").pack(side="left")
        tk.Button(buttons, text="Refresh", command=load_records).pack(side="left", padx=6)
        tk.Button(buttons, text="Close", command=dialog.destroy).pack(side="right")
        load_records()

    def load_data(self):
        # read current filters
        q = self.search_var.get().strip() if getattr(self, 'search_var', None) else None
        cat = self.category_var.get() if getattr(self, 'category_var', None) else None
        stat = self.status_var.get() if getattr(self, 'status_var', None) else None

        for row in self.tree.get_children():
            self.tree.delete(row)

        if q or (cat and cat != 'All') or (stat and stat != 'All'):
            rows = self.controller.search_items(query=q or None, category=(cat if cat != 'All' else None), status=(stat if stat != 'All' else None))
        else:
            rows = self.controller.fetch_all_items()
        for row in rows:
            status = row[5]
            tag = "in_stock"
            if status == "Out of Stock":
                tag = "out_of_stock"
            elif status == "Low Stock":
                tag = "low_stock"
            self.tree.insert("", tk.END, values=row, tags=(tag,))

        total_value = self.controller.total_inventory_value()
        self.lbl_total_value.config(text=f"Total Inventory Value: ${total_value:,.2f}")

    def auto_refresh(self):
        self.load_data()
        self.root.after(2000, self.auto_refresh)

    def open_admin_approvals(self):
        approvals_win = tk.Toplevel(self.root)
        approvals_win.title("Admin Approvals - Password Reset Requests")
        approvals_win.geometry("600x400")

        cols = ("Request ID", "Username", "Email", "Created At", "Status")
        tree = ttk.Treeview(approvals_win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # allow viewing all requests (not only pending)
        def load_requests():
            for r in tree.get_children():
                tree.delete(r)
            rows = self.auth.list_reset_requests(status=None)
            for row in rows:
                # row: id, username, email, created_at, status
                req_id, username, email, created_at, status = row
                try:
                    created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at))
                except Exception:
                    created = str(created_at)
                tree.insert("", tk.END, values=(req_id, username, email, created, status))

        def approve_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Select Request", "Please select a request to approve.")
                return
            req_id = tree.item(sel[0], "values")[0]
            ok, msg = self.auth.approve_reset_request(req_id, approve=True)
            if ok:
                messagebox.showinfo("Approved", msg)
            else:
                messagebox.showerror("Error", msg)
            load_requests()

        def reject_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Select Request", "Please select a request to reject.")
                return
            req_id = tree.item(sel[0], "values")[0]
            ok, msg = self.auth.approve_reset_request(req_id, approve=False)
            if ok:
                messagebox.showinfo("Rejected", msg)
            else:
                messagebox.showerror("Error", msg)
            load_requests()

        btn_frame = tk.Frame(approvals_win)
        btn_frame.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_frame, text="Approve", command=approve_selected, bg="#4CAF50", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Reject", command=reject_selected, bg="#f44336", fg="white").pack(side="left", padx=5)

        load_requests()

    def open_profile(self):
        info = self.auth.get_user_info(self.username)
        if not info:
            messagebox.showerror("Error", "User info not found.")
            return

        prof = tk.Toplevel(self.root)
        prof.title("My Profile & Security")
        prof.geometry("420x320")

        tk.Label(prof, text="Account Information", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(prof, text=f"Username: {info['username']}").pack(anchor="w", padx=20)
        tk.Label(prof, text=f"Email: {info['email']}").pack(anchor="w", padx=20)
        tk.Label(prof, text=f"Role: {info['role']}").pack(anchor="w", padx=20)

        tk.Label(prof, text="", pady=6).pack()
        tk.Label(prof, text="Change Password", font=("Arial", 12, "bold")).pack(pady=6)

        tk.Label(prof, text="Current Password:").pack(anchor="w", padx=20)
        cur_frame = tk.Frame(prof)
        cur_frame.pack(padx=20, fill="x")
        entry_cur = tk.Entry(cur_frame, show="*", width=30)
        entry_cur.pack(side="left", fill="x", expand=True)
        show_cur_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cur_frame, text="Show", variable=show_cur_var, command=lambda: entry_cur.config(show="" if show_cur_var.get() else "*")).pack(side="right", padx=(8,0))

        tk.Label(prof, text="New Password:").pack(anchor="w", padx=20)
        new_frame = tk.Frame(prof)
        new_frame.pack(padx=20, fill="x")
        entry_new = tk.Entry(new_frame, show="*", width=30)
        entry_new.pack(side="left", fill="x", expand=True)
        show_new_var = tk.BooleanVar(value=False)
        tk.Checkbutton(new_frame, text="Show", variable=show_new_var, command=lambda: entry_new.config(show="" if show_new_var.get() else "*")).pack(side="right", padx=(8,0))

        tk.Label(prof, text="Confirm New Password:").pack(anchor="w", padx=20)
        conf_frame = tk.Frame(prof)
        conf_frame.pack(padx=20, fill="x")
        entry_conf = tk.Entry(conf_frame, show="*", width=30)
        entry_conf.pack(side="left", fill="x", expand=True)
        show_conf_var = tk.BooleanVar(value=False)
        tk.Checkbutton(conf_frame, text="Show", variable=show_conf_var, command=lambda: entry_conf.config(show="" if show_conf_var.get() else "*")).pack(side="right", padx=(8,0))

        def do_change():
            old = entry_cur.get().strip()
            new = entry_new.get().strip()
            conf = entry_conf.get().strip()
            if not old or not new or not conf:
                messagebox.showerror("Error", "Please fill in all password fields.")
                return
            if new != conf:
                messagebox.showerror("Error", "New passwords do not match.")
                return
            ok, msg = self.auth.change_password(self.username, old, new)
            if ok:
                messagebox.showinfo("Success", msg)
                prof.destroy()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(prof, text="Change Password", command=do_change, bg="#4CAF50", fg="white").pack(pady=12)

    def _toggle_profile_passwords(self, e1, e2, e3, var):
        if var.get():
            e1.config(show="")
            e2.config(show="")
            e3.config(show="")
        else:
            e1.config(show="*")
            e2.config(show="*")
            e3.config(show="*")