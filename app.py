# ==========================================================
# CAMPUS HARDWARE INVENTORY SYSTEM
# Flask Web Application
# ==========================================================
#
# This file connects the web browser to the existing
# main.py.
#
# The original database and controller functions are reused.
# ==========================================================

# ==========================================================
# 1. IMPORT FLASK TOOLS
# ==========================================================
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
    Response
)

# Used to create login/admin protection decorators.
from functools import wraps

# Used for environment variables and file paths.
import os
from datetime import date
from flask_wtf.csrf import CSRFProtect

# ==========================================================
# 2. ENVIRONMENT / DATABASE SETUP
# ==========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    print("Using PostgreSQL connection from DATABASE_URL.")
else:
    print("DATABASE_URL not set; falling back to local SQLite database.")

# We reuse the existing database and controllers.
from models.database import init_db
from controllers.auth_controller import AuthController as AuthControllerClass
from controllers.tracker_controller import TrackerController

# The app controllers currently use SQLite by default.
# If DATABASE_URL is configured, the app startup is explicit about it.
AuthController = AuthControllerClass(db_name="hardware_inventory.db")
InventoryController = TrackerController(db_name="hardware_inventory.db")

# ==========================================================
# 3. CREATE THE FLASK APPLICATION
# ==========================================================

app = Flask(__name__, template_folder="html")

# Secret key is required for Flask sessions.
app.secret_key = os.environ["SECRET_KEY"]
app.config.update(
    SESSION_COOKIE_SECURE=bool(DATABASE_URL),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
csrf = CSRFProtect(app)
init_db()
# ==========================================================
# 4. LOGIN REQUIRED DECORATOR
# ==========================================================
#
# This checks if the user is logged in before accessing
# protected pages.
# ==========================================================
def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        # If there is no username in the session,
        # the user is not logged in.
        if "username" not in session:

            flash(
                "Please log in first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return view(*args, **kwargs)

    return wrapped
# ==========================================================
# 5. ADMIN REQUIRED DECORATOR
# ==========================================================
#
# This allows only ADMIN accounts to access admin functions.
# ==========================================================
def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        # Check the user's role.
        if session.get("role") != "ADMIN":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return view(*args, **kwargs)

    return wrapped


# ==========================================================
# 6. HOME / INDEX ROUTE
# ==========================================================
#
# "/" is the starting address of the web application.
# ==========================================================
@app.route("/")
def index():

    # If the user is already logged in,
    # go to the dashboard.
    if "username" in session:

        return redirect(
            url_for("dashboard")
        )

    # Otherwise, show the login page.
    return redirect(
        url_for("login")
    )
# ==========================================================
# 7. LOGIN ROUTE
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # GET = display the login page.
    # POST = process the login form.
    if request.method == "POST":

        # Get the values entered by the user.
        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # Make sure both fields have values.
        if not username or not password:

            flash(
                "Username and password are required.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # Use the existing authentication controller.
        ok, msg = (
            AuthController.login_user(
                username,
                password
            )
        )

        # Login successful.
        if ok:

            # Remove any previous session data.
            session.clear()

            # Save the user's information in the session.
            session["username"] = username
            user_info = AuthController.get_user_info(username) or {}
            session["role"] = str(user_info.get("role", "USER")).upper()
            session["email"] = user_info.get("email", "")

            flash(
                msg,
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        # Login failed.
        flash(
            msg,
            "danger"
        )

        is_locked = AuthController.is_user_locked(username)

        # Return to the login page.
        return render_template(
            "login.html",
            locked=is_locked,
            locked_username=username
        )

    # Display the login page.
    return render_template(
        "login.html"
    )
# ==========================================================
# 8. REGISTRATION ROUTE
# ==========================================================
@app.route("/register", methods=["GET", "POST"])
def register():

    # GET = display registration page.
    if request.method == "GET":

        return render_template(
            "register.html"
        )

    # Get registration information.
    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    role = "USER"

    # Check required fields.
    if not username or not email or not password:

        flash(
            "All registration fields are required.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # Use the original registration function.
    ok, msg = AuthController.register_user(
        username,
        email,
        password,
        role=role
    )

    # Show the result.
    flash(
        msg,
        "success" if ok else "warning"
    )

    return redirect(
        url_for("login")
    )
# ==========================================================
# 9. PASSWORD RESET REQUEST
# ==========================================================
@app.route(
    "/reset-request",
    methods=["GET", "POST"]
)
def reset_request():

    # GET = display reset page.
    if request.method == "GET":

        return render_template(
            "reset.html"
        )

    # Get reset information.
    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    new_password = request.form.get(
        "new_password",
        ""
    ).strip()

    confirm_password = request.form.get(
        "confirm_password",
        ""
    ).strip()

    # Check required fields.
    if (
        not username
        or not email
        or not new_password
        or not confirm_password
    ):

        flash(
            "All reset fields are required.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # Check if passwords match.
    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # Use the original password reset function.
    ok, msg = (
        AuthController.submit_password_reset_request(
            username,
            email,
            new_password
        )
    )

    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(
        url_for("login")
    )
# ==========================================================
# 10. DASHBOARD ROUTE
# ==========================================================
@app.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    if role == "ADMIN":
        pending_borrows = InventoryController.get_request_summaries(
            statuses=("Pending", "PENDING_BORROW")
        )
        pending_returns = InventoryController.get_request_summaries(
            statuses=("RETURN_PENDING",)
        )
        history = InventoryController.get_request_summaries()
        pending_resets = AuthController.get_pending_resets()
        active_loans = [
            request for request in history
            if request["status"] in ("Approved", "BORROWED")
        ]
        pending_borrow_requests = pending_borrows
        user_pending_returns = []
    else:
        active_loans = InventoryController.get_request_summaries(
            username=session["username"],
            statuses=("Approved", "BORROWED")
        )
        pending_borrow_requests = InventoryController.get_request_summaries(
            username=session["username"],
            statuses=("Pending", "PENDING_BORROW")
        )
        user_pending_returns = InventoryController.get_request_summaries(
            username=session["username"],
            statuses=("RETURN_PENDING",)
        )
        history = InventoryController.get_request_summaries(
            username=session["username"]
        )
        pending_borrows = []
        pending_returns = user_pending_returns
        pending_resets = []

    all_items = InventoryController.get_all_items(search_text="", category="ALL")
    borrowed_items = sum(
        item["quantity"]
        for request in active_loans
        for item in request["items"]
    )
    total_stocks = sum(item[3] for item in all_items)

    return render_template(
        "dashboard.html",
        total_stocks=total_stocks,
        borrowed_items=borrowed_items,
        pending_borrows=pending_borrows,
        pending_borrow_requests=pending_borrow_requests,
        pending_returns=pending_returns,
        pending_resets=pending_resets,
        history=history,
        user_pending_returns=user_pending_returns,
    )


@app.route("/hardware-catalog")
@login_required
def hardware_catalog():

    # Get search text from the browser.
    search = request.args.get(
        "search",
        ""
    ).strip()

    # Get selected category.
    category = request.args.get(
        "category",
        "ALL"
    )

    # Use ALL when no category was selected.
    if not category:

        category = "ALL"

    # Get inventory based on search/filter.
    items = InventoryController.get_all_items(
        search_text=search,
        category=category
    )

    # Get all available categories.
    categories = InventoryController.get_categories()
    # ======================================================
    # TOTAL STOCKS
    # ======================================================
    #
    # Get ALL inventory records so that Total Stocks
    # is not affected by the search box or category filter.
    # ======================================================
    all_items_for_total = (
        InventoryController.get_all_items(
            search_text="",
            category="ALL"
        )
    )

    # Add all stock quantities.
    total_stocks = sum(
        item[3]
        for item in all_items_for_total
    )
    # ======================================================
    # CREATE EMPTY DATA LISTS
    # ======================================================

    active_loans = []
    history = []
    pending_returns = []
    pending_borrows = []
    pending_borrow_requests = []
    all_loans = []
    pending_resets = []
    # ======================================================
    # USER DATA
    # ======================================================
    if session["role"] == "USER":

        # Items currently borrowed by the user.
        active_loans = (
            InventoryController.get_user_active_loans(
                session["username"]
            )
        )

        # Borrow requests waiting for admin approval.
        pending_borrow_requests = (
            InventoryController.get_user_pending_borrows(
                session["username"]
            )
        )

        # User's borrowing history.
        history = (
            InventoryController.get_user_loan_history(
                session["username"]
            )
        )
    # ======================================================
    # ADMIN DATA
    # ======================================================
    else:

        # Returns waiting for admin approval.
        pending_returns = (
            InventoryController.get_pending_returns()
        )

        # Borrow requests waiting for approval.
        pending_borrows = (
            InventoryController.get_pending_borrows()
        )

        # Complete borrowing history.
        all_loans = (
            InventoryController.get_all_loans_history()
        )

        # Password reset requests.
        pending_resets = (
            AuthController.get_pending_resets()
        )
    # ======================================================
    # SEND DATA TO dashboard.html
    # ======================================================

    return render_template(
        "catalog.html",

        items=items,

        categories=categories,

        search=search,

        selected_category=category,

        total_stocks=total_stocks,

        active_loans=active_loans,

        history=history,

        pending_returns=pending_returns,

        pending_borrows=pending_borrows,

        pending_borrow_requests=(
            pending_borrow_requests
        ),

        all_loans=all_loans,

        pending_resets=pending_resets
    )


@app.route("/hardware-management")
@admin_required
def hardware_management():
    items = InventoryController.get_all_items(search_text="", category="ALL")
    return render_template("hardware_management.html", items=items)


@app.route("/borrowing-returns")
@login_required
def borrowing_returns():
    if session["role"] == "ADMIN":
        return render_template(
            "borrowing_returns.html",
            admin=True,
            pending_borrows=InventoryController.get_request_summaries(statuses=("Pending", "PENDING_BORROW")),
            pending_returns=InventoryController.get_request_summaries(statuses=("RETURN_PENDING",)),
            history=InventoryController.get_request_summaries(),
        )
    return render_template(
        "borrowing_returns.html",
        admin=False,
        items=InventoryController.get_all_items(search_text="", category="ALL"),
        active_loans=InventoryController.get_request_summaries(username=session["username"], statuses=("Approved", "BORROWED")),
        pending_borrow_requests=InventoryController.get_request_summaries(username=session["username"], statuses=("Pending", "PENDING_BORROW")),
        history=InventoryController.get_request_summaries(username=session["username"]),
    )


@app.route("/borrowing-returns/<int:borrow_id>")
@admin_required
def borrowing_return_detail(borrow_id):
    request_summary = InventoryController.get_request_summary(borrow_id)
    if not request_summary:
        flash("Borrowing request not found.", "warning")
        return redirect(url_for("borrowing_returns"))
    return render_template("borrowing_return_detail.html", request_summary=request_summary)


@app.route("/password-reset-requests")
@admin_required
def password_reset_requests():
    return render_template("password_reset_requests.html", pending_resets=AuthController.get_pending_resets())


@app.route("/my-account")
@login_required
def my_account():
    return render_template("account.html")
# ==========================================================
# 11. BORROW ITEM
# ==========================================================
@app.route(
    "/borrow",
    methods=["POST"]
)
@login_required
def borrow():

    if session["role"] != "USER":
        flash("Only USER accounts can borrow equipment.", "danger")
        return redirect(url_for("borrowing_returns"))

    items = []
    try:
        for raw_item_id in request.form.getlist("item_ids"):
            item_id = int(raw_item_id)
            quantity = int(request.form.get(f"quantity_{item_id}", ""))
            if quantity < 1:
                raise ValueError
            items.append((item_id, quantity))
    except ValueError:
        items = []

    if not items:

        flash(
            "Select at least one hardware item and enter a valid quantity.",
            "danger"
        )

        return redirect(url_for("borrowing_returns"))

    ok, msg = InventoryController.borrow_items(
        session["username"],
        session["username"],
        request.form.get("borrow_date", "") or date.today().isoformat(),
        "Inventory request",
        "Web",
        "Web",
        items,
        requested_by=session["username"],
    )

    # Display the result.
    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(url_for("borrowing_returns"))
# ==========================================================
# 12. REQUEST RETURN
# ==========================================================
@app.route(
    "/return-request",
    methods=["POST"]
)
@login_required
def return_request():

    # Get selected loan IDs.
    raw_ids = request.form.getlist("request_ids") or request.form.getlist("loan_ids")

    try:

        loan_ids = [
            int(x)
            for x in raw_ids
        ]

    except ValueError:

        loan_ids = []

    # Only USER accounts can request returns.
    if session["role"] != "USER":

        flash(
            "Only USER accounts can request returns.",
            "danger"
        )

        return redirect(url_for("borrowing_returns"))

    # Use the existing return function.
    ok, msg = (
        InventoryController.request_bulk_item_returns(
            loan_ids,
            username=session["username"]
        )
    )

    flash(
        msg,
        "success" if ok else "warning"
    )

    return redirect(url_for("borrowing_returns"))
# ==========================================================
# 13. CHANGE PASSWORD
# ==========================================================
@app.route(
    "/change-password",
    methods=["POST"]
)
@login_required
def change_password():

    # Get current and new passwords.
    old_password = request.form.get(
        "old_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    # Both fields are required.
    if not old_password or not new_password:

        flash(
            "Both current and new passwords are required.",
            "danger"
        )

        return redirect(url_for("my_account"))

    # Use the existing password function.
    ok, msg = AuthController.change_password_direct(
        session["username"],
        session.get("email", ""),
        old_password,
        new_password
    )

    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(url_for("my_account"))
# ==========================================================
# 14. ADMIN - ADD HARDWARE
# ==========================================================
@app.route(
    "/admin/add",
    methods=["POST"]
)
@admin_required
def admin_add():

    # Get hardware information.
    try:

        name = request.form.get(
            "item_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        quantity = int(
            request.form.get(
                "quantity",
                ""
            )
        )

        unit_price = float(
            request.form.get(
                "unit_price",
                ""
            )
        )

    except ValueError:

        flash(
            "Quantity must be an integer and unit price must be numeric.",
            "danger"
        )

        return redirect(url_for("hardware_management"))

    # Use the original add_item function.
    ok, msg = InventoryController.add_item(
        name,
        category,
        quantity,
        unit_price
    )

    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(url_for("hardware_management"))

@app.route("/admin/edit/<int:item_id>", methods=["POST"])
@admin_required
def admin_edit(item_id):
    try:
        name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        quantity = int(request.form.get("quantity", ""))
        unit_price = float(request.form.get("unit_price", ""))
    except ValueError:
        flash("Quantity must be an integer and unit price must be numeric.", "danger")
        return redirect(url_for("hardware_management"))

    ok, msg = InventoryController.update_item(
        item_id, name, category, quantity, unit_price
    )
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("hardware_management"))

# ==========================================================
# 15. ADMIN - DELETE HARDWARE
# ==========================================================
@app.route(
    "/admin/delete",
    methods=["POST"]
)
@admin_required
def admin_delete():

    # Get selected hardware IDs.
    raw_ids = request.form.getlist(
        "item_ids"
    )

    try:

        item_ids = [
            int(x)
            for x in raw_ids
        ]

    except ValueError:

        item_ids = []

    # Delete selected items.
    ok, msg = InventoryController.delete_bulk_items(
        item_ids
    )

    flash(
        msg,
        "success" if ok else "warning"
    )

    return redirect(url_for("hardware_management"))
# ==========================================================
# 16. ADMIN - BORROW APPROVAL
# ==========================================================
@app.route(
    "/admin/borrow-action",
    methods=["POST"]
)
@admin_required
def admin_borrow_action():

    # Get selected borrow request IDs.
    raw_ids = request.form.getlist("request_ids") or request.form.getlist("loan_ids")

    # Approve when the form action is "approve".
    approve = (
        request.form.get("action")
        == "approve"
    )

    try:

        loan_ids = [
            int(x)
            for x in raw_ids
        ]

    except ValueError:

        loan_ids = []

    # Process the borrow requests.
    ok, msg = (
        InventoryController.process_bulk_borrows(
            loan_ids,
            approve=approve
        )
    )

    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(url_for("borrowing_returns"))
# ==========================================================
# 17. ADMIN - RETURN APPROVAL
# ==========================================================
@app.route(
    "/admin/return-action",
    methods=["POST"]
)
@admin_required
def admin_return_action():

    # Get selected return request IDs.
    raw_ids = request.form.getlist("request_ids") or request.form.getlist("loan_ids")

    # Check whether Admin approved the return.
    approve = (
        request.form.get("action")
        == "approve"
    )

    try:

        loan_ids = [
            int(x)
            for x in raw_ids
        ]

    except ValueError:

        loan_ids = []

    # Process return requests.
    ok, msg = (
        InventoryController.process_bulk_returns(
            loan_ids,
            approve=approve
        )
    )

    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(url_for("borrowing_returns"))
# ==========================================================
# 18. ADMIN - PASSWORD RESET APPROVAL
# ==========================================================
@app.route(
    "/admin/reset-action",
    methods=["POST"]
)
@admin_required
def admin_reset_action():

    # Get selected reset request IDs.
    raw_ids = request.form.getlist(
        "request_ids"
    )

    # Check whether Admin approved the reset.
    approve = (
        request.form.get("action")
        == "approve"
    )

    try:

        request_ids = [
            int(x)
            for x in raw_ids
        ]

    except ValueError:

        request_ids = []

    # Process reset requests.
    ok, msg = (
        AuthController.process_bulk_resets(
            request_ids,
            approve=approve
        )
    )

    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(url_for("password_reset_requests"))
# ==========================================================
# 19. EXPORT INVENTORY REPORT
# ==========================================================
@app.route("/export")
@login_required
def export():
    ok, content = InventoryController.export_to_csv_content()
    if not ok:
        flash(content, "danger")
        return redirect(url_for("dashboard"))
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_report.csv"},
    )
# ==========================================================
# 20. LOGOUT
# ==========================================================
@app.route("/logout")
def logout():

    # Remove the user's session.
    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )
# ==========================================================
# 21. START THE FLASK WEB SERVER
# ==========================================================
if __name__ == "__main__":
    print()
    print("=" * 58)
    print(" CAMPUS HARDWARE INVENTORY - WEB PORTAL")
    print("=" * 58)
    print()

    print(" Open Google Chrome and go to:")
    print(" http://127.0.0.1:5000")

    print()
    print(" Press CTRL+C to stop the server.")
    print("=" * 58)
    print()

    # Start Flask.
    app.run()
