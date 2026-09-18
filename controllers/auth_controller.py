import sqlite3
import time

import bcrypt
import psycopg
from logger import logger
from models.database import get_db_connection
from models.schemas import UserRegisterSchema
from pydantic import ValidationError


class AuthController:
    def __init__(self, db_name="hardware_inventory.db"):
        self.db_name = db_name
        self._failed_attempts = {}
        # persistent lock state is stored in DB (users.locked)

    def register_user(self, username, email, password, role='user'):
        try:
            validated = UserRegisterSchema(username=username, email=email, password=password, role=role)
        except ValidationError as e:
            logger.warning(f"Registration validation failed for '{username}': {e.errors()[0]['msg']}")
            return False, f"Validation error: {e.errors()[0]['msg']}"

        hashed_pw = bcrypt.hashpw(validated.password.encode('utf-8'), bcrypt.gensalt())

        try:
            # use context manager so connection is closed even on exceptions; increase timeout to reduce locking
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)", (validated.username, validated.email, hashed_pw.decode('utf-8'), validated.role))
                conn.commit()
            logger.info(f"Account created: '{validated.username}'")
            return True, "Registration successful! You may now log in."
        except (sqlite3.IntegrityError, psycopg.IntegrityError) as e:
            err = str(e).lower()
            # SQLite IntegrityError message often contains the column that violated UNIQUE constraint
            if 'email' in err or 'users.email' in err:
                return False, "Email already taken."
            if 'username' in err or 'users.username' in err:
                return False, "Username already taken."
            return False, "Username or email already taken."

    def get_lockout_remaining(self, username):
        # Return -1 if account is locked until password reset, 0 otherwise
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT locked FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

        if row and row[0] == 1:
            return -1
        return 0

    def _set_user_locked(self, username, locked=True):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET locked = ? WHERE username = ?", (1 if locked else 0, username))
            conn.commit()

    def is_user_locked(self, username):
        return self.get_lockout_remaining(username) < 0

    def reset_password(self, username, email, new_password):
        # Instead of immediately resetting the password, create a pending admin approval request
        try:
            validated = UserRegisterSchema(username=username, email=email, password=new_password)
        except ValidationError as e:
            logger.warning(f"Password reset validation failed for '{username}': {e.errors()[0]['msg']}")
            return False, f"Validation error: {e.errors()[0]['msg']}"

        hashed_pw = bcrypt.hashpw(validated.password.encode('utf-8'), bcrypt.gensalt())

        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ? AND email = ?", (validated.username, validated.email))
            row = cursor.fetchone()
            if not row:
                return False, "No account found matching that username and email."

            user_id = row[0]
            # Insert new password reset request as pending
            cursor.execute(
                "INSERT INTO password_reset_requests (user_id, new_password_hash, status, created_at) VALUES (?, ?, 'pending', ?)",
                (user_id, hashed_pw.decode('utf-8'), int(time.time()))
            )
            conn.commit()

        logger.info(f"Password reset request created for user '{username}'")
        return True, "Password reset request submitted. An admin must approve it before your account is unlocked."

    def list_pending_reset_requests(self):
        return self.list_reset_requests(status='pending')

    def list_reset_requests(self, status=None):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            if status is None:
                cursor.execute(
                    "SELECT r.id, u.username, u.email, r.created_at, r.status FROM password_reset_requests r JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC"
                )
            else:
                cursor.execute(
                    "SELECT r.id, u.username, u.email, r.created_at, r.status FROM password_reset_requests r JOIN users u ON r.user_id = u.id WHERE r.status = ? ORDER BY r.created_at DESC",
                    (status,)
                )
            rows = cursor.fetchall()
        return rows

    def approve_reset_request(self, request_id, approve=True):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, new_password_hash, status FROM password_reset_requests WHERE id = ?", (request_id,))
            req = cursor.fetchone()
            if not req:
                return False, "Request not found."
            user_id, new_pw_hash, status = req
            if status != 'pending':
                return False, "Request is not pending."

            if approve:
                # Update user's password and unlock account
                cursor.execute("UPDATE users SET password_hash = ?, locked = 0 WHERE id = ?", (new_pw_hash, user_id))
                cursor.execute("UPDATE password_reset_requests SET status = 'approved' WHERE id = ?", (request_id,))
                conn.commit()
                return True, "Request approved and password updated."
            else:
                cursor.execute("UPDATE password_reset_requests SET status = 'rejected' WHERE id = ?", (request_id,))
                conn.commit()
                return True, "Request rejected."

    def get_user_role(self, username):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
        return row[0] if row else None

    def get_user_info(self, username):
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, role, locked FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'role': row[3],
            'locked': bool(row[4])
        }

    def change_password(self, username, old_password, new_password):
        if not username or not old_password or not new_password:
            return False, "All password fields are required."

        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash, email, role FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return False, "User not found."
            user_id, pw_hash, email, role = row

        # verify old password
        if not bcrypt.checkpw(old_password.encode('utf-8'), pw_hash.encode('utf-8')):
            return False, "Current password is incorrect."

        # validate new password using schema
        try:
            validated = UserRegisterSchema(username=username, email=email, password=new_password, role=role or 'user')
        except ValidationError as e:
            logger.warning(f"Password change validation failed for '{username}': {e.errors()[0]['msg']}")
            return False, f"Validation error: {e.errors()[0]['msg']}"

        new_hashed = bcrypt.hashpw(validated.password.encode('utf-8'), bcrypt.gensalt())
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ?, locked = 0 WHERE id = ?", (new_hashed.decode('utf-8'), user_id))
            conn.commit()

        self._failed_attempts.pop(username, None)
        logger.info(f"Password changed for user '{username}'")
        return True, "Password changed successfully."

    def login_user(self, username, password):
        if not username or not password:
            return False, "Please enter both username and password."

        remaining = self.get_lockout_remaining(username)
        if remaining < 0:
            return False, "Account locked. Please reset your password." 

        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, locked FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

        if row and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
            # if user is locked in DB, disallow login until password reset
            if len(row) > 1 and row[1] == 1:
                return False, "Account locked. Please reset your password."
            self._failed_attempts.pop(username, None)
            logger.info(f"User '{username}' logged in.")
            return True, "Login successful!"

        count = self._failed_attempts.get(username, 0) + 1
        self._failed_attempts[username] = count

        if count >= 3:
            # Persistently lock account until user resets password
            try:
                self._set_user_locked(username, True)
            except Exception:
                logger.exception("Failed to set persistent lock for user %s", username)
            self._failed_attempts[username] = 0
            return False, "Too many failed attempts. Account locked. Please reset your password."

        attempts_left = 3 - count
        return False, f"Invalid username or password. {attempts_left} attempt(s) remaining before lockout."

    def submit_password_reset_request(self, username, email, new_password):
        return self.reset_password(username, email, new_password)

    def get_pending_resets(self):
        return self.list_pending_reset_requests()

    def process_bulk_resets(self, request_ids, approve=False):
        if not request_ids:
            return False, "Select at least one password reset request."
        results = [self.approve_reset_request(request_id, approve=approve) for request_id in request_ids]
        failures = [message for ok, message in results if not ok]
        return (False, failures[0]) if failures else (True, "Password reset requests processed successfully.")

    def change_password_direct(self, username, _email, old_password, new_password):
        return self.change_password(username, old_password, new_password)