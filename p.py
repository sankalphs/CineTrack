import customtkinter as ctk
from tkinter import ttk, messagebox, PhotoImage, filedialog
import mysql.connector
import csv
import re
import os
import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")    # IMDB-like effect

# Connect to DB
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="qwerty1234",
    database="cinetrack"
)
cursor = conn.cursor(buffered=True)

# Theme/Style constants
IMDB_YELLOW = "#F5C518"
IMDB_DARK_BG = "#181818"
IMDB_GRAY = "#232323"
FONT_HEADER = ("Arial Black", 22)
FONT_SUBHEADER = ("Arial", 15, "bold")
FONT_NORMAL = ("Arial", 13)

def imdb_heading(master, text):
    ctk.CTkLabel(
        master,
        text=text,
        font=FONT_HEADER,
        text_color=IMDB_YELLOW,
        bg_color=IMDB_DARK_BG
    ).pack(anchor="w", pady=(18,3), padx=(20,0))

def imdb_subheading(master, text):
    ctk.CTkLabel(
        master,
        text=text,
        font=FONT_SUBHEADER,
        text_color="white",
        bg_color=IMDB_DARK_BG
    ).pack(anchor="w", padx=(20,0))

class CineTrackIMDB(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.configure(bg_color=IMDB_DARK_BG)
        self.title("CineTrack")
        self.geometry("1400x860")
        self.sidebar = None
        self.page = None
        # currently logged in user as tuple (user_id, username)
        self.current_user = None

        # Top header styled like IMDB and left compact nav
        self.create_header()
        self.show_home()

        # Import dataset CSV if exists
        if os.path.exists("cinetrack_dataset.csv"):
            self.import_all_csv_from_path("cinetrack_dataset.csv")

    # ========== TOP HEADER ==========
    def create_header(self):
        # Top IMDB-like header bar
        header = ctk.CTkFrame(self, height=72, fg_color=IMDB_GRAY)
        header.pack(side="top", fill="x")

        # Logo (left)
        logo = ctk.CTkLabel(header, text="CineTrack", font=("Arial Black", 24), text_color=IMDB_YELLOW, bg_color=IMDB_GRAY)
        logo.pack(side="left", padx=(18,12))

        # Navigation (center)
        nav_frame = ctk.CTkFrame(header, fg_color=IMDB_GRAY)
        nav_frame.pack(side="left", padx=12)
        nav_items = [
            ("Home", self.show_home),
            ("Movies", self.show_movies),
            ("Cast", self.show_cast),
            ("TV", self.show_series),
            ("Login", self.show_account_page),
            ("Users", self.show_users),
            ("Studios", self.show_studios),
            ("Watchlist", self.show_watchlist),
            ("Donations", self.show_donations),
        ]
        for txt, fn in nav_items:
            btn = ctk.CTkButton(nav_frame, text=txt, corner_radius=8, font=("Arial", 12, "bold"), fg_color=IMDB_GRAY,
                text_color="white", hover_color=IMDB_YELLOW, command=fn, width=90, height=30)
            btn.pack(side="left", padx=6)
        # Search box (right)
        search_entry = ctk.CTkEntry(header, width=360, placeholder_text="Search movies, cast, keywords...", font=("Arial", 12))
        search_entry.pack(side="right", padx=18)
        # Pressing Enter in the header search opens the Search page and runs the query
        search_entry.bind('<Return>', lambda e, q=search_entry: self._header_search_trigger(q.get()))
        # Account / Login button (right) - opens a full page login/register UI
        self.account_btn = ctk.CTkButton(header, text="Account", width=120, fg_color=IMDB_GRAY, command=self.show_account_page)
        self.account_btn.pack(side="right", padx=(0,12))

    def clear_page(self):
        if self.page:
            self.page.destroy()
        self.page = ctk.CTkFrame(self, fg_color=IMDB_DARK_BG)
        self.page.pack(side="right", fill="both", expand=True)

    def _style_treeview(self, tree, heading_font=FONT_SUBHEADER, cell_font=FONT_NORMAL, rowheight=26):
        """Apply a consistent, IMDB-like style to a ttk.Treeview widget.

        - heading_font: font tuple for header text
        - cell_font: font tuple for cell text
        - rowheight: integer pixel height for rows
        """
        style = ttk.Style()
        # Create a custom style name so we don't conflict with other widgets
        style_name = 'CTk.Treeview'
        heading_name = style_name + '.Heading'

        # Configure the treeview look
        try:
            style.configure(style_name, background=IMDB_DARK_BG, fieldbackground=IMDB_DARK_BG,
                            foreground='white', rowheight=rowheight, font=cell_font)
            style.configure(heading_name, background=IMDB_GRAY, foreground=IMDB_YELLOW, font=heading_font)
        except Exception:
            # fallback: some ttk themes ignore certain options
            pass

        tree.configure(style=style_name)

        # Alternating row colors and font
        try:
            tree.tag_configure('even', background=IMDB_DARK_BG, foreground='white', font=cell_font)
            tree.tag_configure('odd', background=IMDB_GRAY, foreground='white', font=cell_font)
        except Exception:
            pass

    def _attach_treeview_tooltip(self, tree, col_index=0, wrap=400):
        """Attach a hover tooltip to a ttk.Treeview showing the full text of a column.

        - tree: the Treeview widget
        - col_index: 0-based column index to show in the tooltip
        """
        tooltip = None

        def motion(event):
            nonlocal tooltip
            rowid = tree.identify_row(event.y)
            if not rowid:
                if tooltip:
                    tooltip.destroy()
                    tooltip = None
                return
            try:
                vals = tree.item(rowid, 'values')
                text = vals[col_index] if len(vals) > col_index else ''
            except Exception:
                text = ''
            if not text:
                if tooltip:
                    tooltip.destroy()
                    tooltip = None
                return
            if tooltip:
                try:
                    lbl = tooltip.children.get('!label')
                    if lbl:
                        lbl.configure(text=text)
                except Exception:
                    pass
            else:
                tooltip = ctk.CTkToplevel(self)
                tooltip.overrideredirect(True)
                lbl = ctk.CTkLabel(tooltip, text=text, wraplength=wrap, bg_color=IMDB_GRAY, text_color='white')
                lbl.pack()
            x = tree.winfo_rootx() + event.x + 12
            y = tree.winfo_rooty() + event.y + 12
            try:
                tooltip.geometry(f'+{x}+{y}')
            except Exception:
                pass

        def leave(event):
            nonlocal tooltip
            if tooltip:
                try:
                    tooltip.destroy()
                except Exception:
                    pass
                tooltip = None

        tree.bind('<Motion>', motion)
        tree.bind('<Leave>', leave)

    def _header_search_trigger(self, query_text):
        """Check if the header query looks like a cast name; route to search page accordingly."""
        q = (query_text or '').strip()
        if not q:
            # just open search page
            self.show_search()
            return
        try:
            cursor.execute("SELECT 1 FROM cast_members WHERE name LIKE %s LIMIT 1", (f"%{q}%",))
            found = cursor.fetchone()
        except Exception:
            found = None
        self.show_search(initial_query=q, initial_cast=bool(found))

    # ========== HOME PAGE ==========
    def show_home(self):
        self.clear_page()
        imdb_heading(self.page, "Welcome to CineTrack")
        imdb_subheading(self.page, "Your personalized movie, series, and cast database")

        # Show 5 random highlighted movies
        cursor.execute("SELECT movie_id, movie_name, release_date, language, description FROM movies ORDER BY RAND() LIMIT 5")
        rows = cursor.fetchall()
        ctk.CTkLabel(self.page, text="Hot Trending Movies:", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20, pady=(18,7))

        cards = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        cards.pack(anchor="w", padx=20)
        for r in rows:
            self._movie_card(cards, r)

    # ========== AUTH / USER MANAGEMENT ==========
    def open_auth_dialog(self):
        # simple modal for login/register
        dlg = ctk.CTkToplevel(self)
        dlg.title("Account")
        dlg.geometry("420x280")
        ctk.CTkLabel(dlg, text="Login or Register", font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack(pady=(12,6))

        frame = ctk.CTkFrame(dlg)
        frame.pack(padx=12, pady=6, fill='both', expand=True)

        ctk.CTkLabel(frame, text="Username:").grid(row=0, column=0, sticky='w')
        username_e = ctk.CTkEntry(frame, width=260)
        username_e.grid(row=0, column=1, pady=6)

        ctk.CTkLabel(frame, text="Email (register):").grid(row=1, column=0, sticky='w')
        email_e = ctk.CTkEntry(frame, width=260)
        email_e.grid(row=1, column=1, pady=6)

        ctk.CTkLabel(frame, text="Password:").grid(row=2, column=0, sticky='w')
        pwd_e = ctk.CTkEntry(frame, width=260, show='*')
        pwd_e.grid(row=2, column=1, pady=6)

        status_lbl = ctk.CTkLabel(frame, text="", text_color='white')
        status_lbl.grid(row=3, column=0, columnspan=2, pady=(6,0))

        def do_login():
            uname = username_e.get().strip()
            pwd = pwd_e.get().strip()
            if not uname or not pwd:
                status_lbl.configure(text='Enter username and password')
                return
            cursor.execute("SELECT user_id, username, password FROM users WHERE username=%s", (uname,))
            r = cursor.fetchone()
            if not r or not r[2] or r[2] != pwd:
                status_lbl.configure(text='Invalid credentials')
                return
            self.current_user = (r[0], r[1])
            self.account_btn.configure(text=r[1])
            status_lbl.configure(text='Logged in')
            dlg.destroy()

        def do_register():
            uname = username_e.get().strip()
            email = email_e.get().strip() or None
            pwd = pwd_e.get().strip()
            if not uname or not pwd:
                status_lbl.configure(text='Enter username and password')
                return
            cursor.execute("SELECT user_id FROM users WHERE username=%s", (uname,))
            if cursor.fetchone():
                status_lbl.configure(text='Username taken')
                return
            try:
                cursor.execute("INSERT INTO users (username, email, password) VALUES (%s,%s,%s)", (uname, email, pwd))
                conn.commit()
            except Exception as e:
                conn.rollback()
                status_lbl.configure(text=f'Error: {e}')
                return
            cursor.execute("SELECT user_id FROM users WHERE username=%s", (uname,))
            uid = cursor.fetchone()[0]
            self.current_user = (uid, uname)
            self.account_btn.configure(text=uname)
            dlg.destroy()

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=12)
        ctk.CTkButton(btn_frame, text='Login', fg_color=IMDB_YELLOW, command=do_login, width=120).pack(side='left', padx=6)
        ctk.CTkButton(btn_frame, text='Register', fg_color=IMDB_YELLOW, command=do_register, width=120).pack(side='left', padx=6)

    def logout(self):
        self.current_user = None
        self.account_btn.configure(text='Account')

    def show_account_page(self):
        """Full-page account management: Login | Register | Logout"""
        self.clear_page()
        imdb_heading(self.page, 'Account')
        imdb_subheading(self.page, 'Login or create an account')

        frame = ctk.CTkFrame(self.page)
        frame.pack(padx=20, pady=12)

        # Login column
        login_col = ctk.CTkFrame(frame)
        login_col.grid(row=0, column=0, padx=12, pady=6)
        ctk.CTkLabel(login_col, text='Login', font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack(pady=(6,8))
        ctk.CTkLabel(login_col, text='Username:').pack(anchor='w')
        login_user = ctk.CTkEntry(login_col, width=260)
        login_user.pack()
        ctk.CTkLabel(login_col, text='Password:').pack(anchor='w', pady=(6,0))
        login_pwd = ctk.CTkEntry(login_col, width=260, show='*')
        login_pwd.pack()

        def do_login_page():
            uname = login_user.get().strip()
            pwd = login_pwd.get().strip()
            if not uname or not pwd:
                messagebox.showerror('Input', 'Enter username and password')
                return
            cursor.execute('SELECT user_id, username, password FROM users WHERE username=%s', (uname,))
            r = cursor.fetchone()
            if not r or not r[2] or r[2] != pwd:
                messagebox.showerror('Auth', 'Invalid credentials')
                return
            self.current_user = (r[0], r[1])
            self.account_btn.configure(text=r[1])
            messagebox.showinfo('Login', 'Logged in')
            self.show_home()

        ctk.CTkButton(login_col, text='Login', fg_color=IMDB_YELLOW, command=do_login_page, width=140).pack(pady=(8,6))

        # Register column
        reg_col = ctk.CTkFrame(frame)
        reg_col.grid(row=0, column=1, padx=12, pady=6)
        ctk.CTkLabel(reg_col, text='Register', font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack(pady=(6,8))
        ctk.CTkLabel(reg_col, text='Username:').pack(anchor='w')
        reg_user = ctk.CTkEntry(reg_col, width=260)
        reg_user.pack()
        ctk.CTkLabel(reg_col, text='Email:').pack(anchor='w', pady=(6,0))
        reg_email = ctk.CTkEntry(reg_col, width=260)
        reg_email.pack()
        ctk.CTkLabel(reg_col, text='Password:').pack(anchor='w', pady=(6,0))
        reg_pwd = ctk.CTkEntry(reg_col, width=260, show='*')
        reg_pwd.pack()

        def do_register_page():
            uname = reg_user.get().strip()
            email = reg_email.get().strip() or None
            pwd = reg_pwd.get().strip()
            if not uname or not pwd:
                messagebox.showerror('Input', 'Enter username and password')
                return
            cursor.execute('SELECT user_id FROM users WHERE username=%s', (uname,))
            if cursor.fetchone():
                messagebox.showerror('Register', 'Username already exists')
                return
            try:
                cursor.execute('INSERT INTO users (username, email, password) VALUES (%s,%s,%s)', (uname, email, pwd))
                conn.commit()
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')
                return
            cursor.execute('SELECT user_id FROM users WHERE username=%s', (uname,))
            uid = cursor.fetchone()[0]
            self.current_user = (uid, uname)
            self.account_btn.configure(text=uname)
            messagebox.showinfo('Register', 'Account created and logged in')
            self.show_home()

        ctk.CTkButton(reg_col, text='Register', fg_color=IMDB_YELLOW, command=do_register_page, width=140).pack(pady=(8,6))

        # If logged in show logout and profile quick info
        if self.current_user:
            acctf = ctk.CTkFrame(self.page)
            acctf.pack(anchor='e', padx=20, pady=10)
            ctk.CTkLabel(acctf, text=f'Logged in as {self.current_user[1]}', font=FONT_NORMAL, text_color='white').pack(side='left', padx=(0,12))
            ctk.CTkButton(acctf, text='Logout', fg_color=IMDB_YELLOW, command=lambda: (self.logout(), messagebox.showinfo('Logout','Logged out'), self.show_home()), width=140).pack(side='left')

    # ========== USERS & FOLLOW ==========
    def show_users(self):
        self.clear_page()
        imdb_heading(self.page, 'Users')
        imdb_subheading(self.page, 'Browse and follow users')

        frame = ctk.CTkFrame(self.page)
        frame.pack(fill='both', padx=20, pady=12)

        cols = ('Username', 'Email', 'Follow')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center', width=200)
        self._style_treeview(tree)
        scr = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scr.set)
        scr.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        cursor.execute("SELECT user_id, username, email FROM users ORDER BY username")
        users = cursor.fetchall()
        for i, u in enumerate(users):
            tag = 'even' if i%2==0 else 'odd'
            tree.insert('', 'end', iid=str(u[0]), values=(u[1], u[2] or ''), tags=(tag,))

        # follow/unfollow buttons
        btns = ctk.CTkFrame(self.page)
        btns.pack(pady=(8,0))

        def on_view():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo('Select', 'Select a user to view')
                return
            uid = int(sel[0])
            self.show_user_profile(uid)

        def on_follow():
            if not self.current_user:
                messagebox.showerror('Auth', 'Login to follow users')
                return
            sel = tree.selection()
            if not sel:
                messagebox.showinfo('Select', 'Select a user to follow')
                return
            target = int(sel[0])
            if target == self.current_user[0]:
                messagebox.showinfo('Follow', 'Cannot follow yourself')
                return
            try:
                cursor.execute('INSERT INTO user_follow (follower_id, followed_id) VALUES (%s,%s)', (self.current_user[0], target))
                conn.commit()
                messagebox.showinfo('Follow', 'Now following')
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        def on_unfollow():
            if not self.current_user:
                messagebox.showerror('Auth', 'Login to unfollow users')
                return
            sel = tree.selection()
            if not sel:
                messagebox.showinfo('Select', 'Select a user to unfollow')
                return
            target = int(sel[0])
            try:
                cursor.execute('DELETE FROM user_follow WHERE follower_id=%s AND followed_id=%s', (self.current_user[0], target))
                conn.commit()
                messagebox.showinfo('Unfollow', 'Unfollowed')
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        ctk.CTkButton(btns, text='View Profile', fg_color=IMDB_YELLOW, command=on_view, width=140).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Follow', fg_color=IMDB_YELLOW, command=on_follow, width=140).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Unfollow', fg_color=IMDB_YELLOW, command=on_unfollow, width=140).pack(side='left', padx=6)

    def show_user_profile(self, user_id):
        self.clear_page()
        cursor.execute('SELECT username, email FROM users WHERE user_id=%s', (user_id,))
        r = cursor.fetchone()
        if not r:
            imdb_heading(self.page, 'User not found')
            return
        imdb_heading(self.page, r[0])
        imdb_subheading(self.page, f"Email: {r[1] or 'N/A'}")

        # followers / following
        cursor.execute('SELECT u.username FROM user_follow uf JOIN users u ON uf.follower_id=u.user_id WHERE uf.followed_id=%s', (user_id,))
        followers = [x[0] for x in cursor.fetchall()]
        cursor.execute('SELECT u.username FROM user_follow uf JOIN users u ON uf.followed_id=u.user_id WHERE uf.follower_id=%s', (user_id,))
        following = [x[0] for x in cursor.fetchall()]

        ctk.CTkLabel(self.page, text=f"Followers ({len(followers)}): " + (', '.join(followers) if followers else 'None'), font=FONT_NORMAL, text_color='white', bg_color=IMDB_DARK_BG).pack(anchor='w', padx=20, pady=(12,0))
        ctk.CTkLabel(self.page, text=f"Following ({len(following)}): " + (', '.join(following) if following else 'None'), font=FONT_NORMAL, text_color='white', bg_color=IMDB_DARK_BG).pack(anchor='w', padx=20, pady=(6,12))

    # ========== STUDIOS ==========
    def show_studios(self):
        self.clear_page()
        imdb_heading(self.page, 'Studios')
        imdb_subheading(self.page, 'View and add production studios')

        frame = ctk.CTkFrame(self.page)
        frame.pack(fill='both', padx=20, pady=12)
        cols = ('Studio', 'Country', 'Movies Produced')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center', width=300)
        self._style_treeview(tree)
        scr = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scr.set)
        scr.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        cursor.execute('SELECT s.studio_id, s.studio_name, s.country, COUNT(ms.movie_id) FROM studios s LEFT JOIN movie_studio ms ON s.studio_id=ms.studio_id GROUP BY s.studio_id ORDER BY s.studio_name')
        rows = cursor.fetchall()
        for i, r in enumerate(rows):
            tag = 'even' if i%2==0 else 'odd'
            tree.insert('', 'end', iid=str(r[0]), values=(r[1], r[2] or '', r[3]), tags=(tag,))

        ctrl = ctk.CTkFrame(self.page)
        ctrl.pack(pady=(8,0))

        def on_view_movies():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo('Select', 'Select a studio')
                return
            sid = int(sel[0])
            self.clear_page()
            cursor.execute('SELECT studio_name FROM studios WHERE studio_id=%s', (sid,))
            nm = cursor.fetchone()[0]
            imdb_heading(self.page, nm)
            imdb_subheading(self.page, 'Movies by this studio')
            tf = ctk.CTkFrame(self.page)
            tf.pack(fill='both', padx=20)
            cols2 = ('Movie', 'Year')
            t2 = ttk.Treeview(tf, columns=cols2, show='headings')
            for c in cols2:
                t2.heading(c, text=c)
                t2.column(c, anchor='center', width=400)
            self._style_treeview(t2)
            sc = ttk.Scrollbar(tf, orient='vertical', command=t2.yview)
            t2.configure(yscrollcommand=sc.set)
            sc.pack(side='right', fill='y')
            t2.pack(fill='both', expand=True)
            cursor.execute('SELECT m.movie_name, YEAR(m.release_date) FROM movie_studio ms JOIN movies m ON ms.movie_id=m.movie_id WHERE ms.studio_id=%s ORDER BY m.release_date DESC', (sid,))
            for i, mv in enumerate(cursor.fetchall()):
                tag = 'even' if i%2==0 else 'odd'
                t2.insert('', 'end', values=mv, tags=(tag,))

        def on_add_studio():
            dlg = ctk.CTkToplevel(self)
            dlg.title('Add Studio')
            dlg.geometry('420x180')
            ctk.CTkLabel(dlg, text='Add Studio', font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack(pady=(12,6))
            fr = ctk.CTkFrame(dlg)
            fr.pack(padx=12, pady=6)
            ctk.CTkLabel(fr, text='Studio Name:').grid(row=0, column=0, sticky='w')
            name_e = ctk.CTkEntry(fr, width=260)
            name_e.grid(row=0, column=1, pady=6)
            ctk.CTkLabel(fr, text='Country:').grid(row=1, column=0, sticky='w')
            country_e = ctk.CTkEntry(fr, width=260)
            country_e.grid(row=1, column=1, pady=6)

            def submit():
                nm = name_e.get().strip()
                cnt = country_e.get().strip() or None
                if not nm:
                    messagebox.showerror('Input', 'Enter studio name')
                    return
                try:
                    cursor.execute('INSERT INTO studios (studio_name, country) VALUES (%s,%s)', (nm, cnt))
                    conn.commit()
                    messagebox.showinfo('Added', 'Studio added')
                    dlg.destroy()
                    self.show_studios()
                except Exception as e:
                    conn.rollback()
                    messagebox.showerror('DB', f'Failed: {e}')

            ctk.CTkButton(fr, text='Add', fg_color=IMDB_YELLOW, command=submit).grid(row=2, column=0, columnspan=2, pady=8)

        ctk.CTkButton(ctrl, text='View Movies', fg_color=IMDB_YELLOW, command=on_view_movies, width=140).pack(side='left', padx=6)
        ctk.CTkButton(ctrl, text='Add Studio', fg_color=IMDB_YELLOW, command=on_add_studio, width=140).pack(side='left', padx=6)

    # ========== WATCHLIST ==========
    def _ensure_watchlist_table(self):
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_watchlist (
                    watchlist_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    movie_id INT NOT NULL,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY ux_user_movie (user_id, movie_id)
                ) ENGINE=InnoDB
            ''')
            conn.commit()
        except Exception:
            conn.rollback()

    def show_watchlist(self):
        if not self.current_user:
            messagebox.showerror('Auth', 'Login to view your watchlist')
            return
        self._ensure_watchlist_table()
        self.clear_page()
        imdb_heading(self.page, f"{self.current_user[1]}'s Watchlist")
        frame = ctk.CTkFrame(self.page)
        frame.pack(fill='both', padx=20, pady=12)
        cols = ('Movie', 'Added')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=18)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center', width=400)
        self._style_treeview(tree)
        scr = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scr.set)
        scr.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        cursor.execute('SELECT m.movie_id, m.movie_name, uw.added_date FROM user_watchlist uw JOIN movies m ON uw.movie_id=m.movie_id WHERE uw.user_id=%s ORDER BY uw.added_date DESC', (self.current_user[0],))
        for i, r in enumerate(cursor.fetchall()):
            tag = 'even' if i%2==0 else 'odd'
            tree.insert('', 'end', iid=str(r[0]), values=(r[1], r[2]), tags=(tag,))

        def remove_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo('Select', 'Select a movie to remove')
                return
            mid = int(sel[0])
            try:
                cursor.execute('DELETE FROM user_watchlist WHERE user_id=%s AND movie_id=%s', (self.current_user[0], mid))
                conn.commit()
                self.show_watchlist()
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        btnf = ctk.CTkFrame(self.page)
        btnf.pack(pady=(8,0))
        ctk.CTkButton(btnf, text='Open Movie', fg_color=IMDB_YELLOW, command=lambda: self.show_movie_detail(int(tree.selection()[0])) if tree.selection() else None, width=140).pack(side='left', padx=6)
        ctk.CTkButton(btnf, text='Remove', fg_color=IMDB_YELLOW, command=remove_selected, width=140).pack(side='left', padx=6)

    # ========== AUDIT PANEL ==========
    def show_audit(self):
        # basic admin view for ratings_audit
        self.clear_page()
        imdb_heading(self.page, 'Ratings Audit')
        imdb_subheading(self.page, 'Audit trail of rating changes')

        frame = ctk.CTkFrame(self.page)
        frame.pack(fill='both', padx=20, pady=12)
        cols = ('Audit ID', 'Rating ID', 'Old', 'New', 'Changed By', 'When')
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=20)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center', width=160)
        self._style_treeview(tree)
        scr = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scr.set)
        scr.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        try:
            cursor.execute('SELECT audit_id, rating_id, old_rating, new_rating, changed_by, changed_at FROM ratings_audit ORDER BY changed_at DESC')
            for i, r in enumerate(cursor.fetchall()):
                tag = 'even' if i%2==0 else 'odd'
                tree.insert('', 'end', values=r, tags=(tag,))
        except Exception:
            messagebox.showerror('DB', 'ratings_audit table not available')


    # ========== MOVIES ==========
    def show_movies(self):
        self.clear_page()
        imdb_heading(self.page, "Movies Library")
        # Card grid for movies (IMDB-style posters)
        self._movie_card_grid()

    def import_movies_csv(self):
        """Open a CSV file and bulk-insert movies.

        Expected minimal CSV headers: title (or movie_name), release_date (YYYY-MM-DD or YYYY), language, description, genres (comma/|/; separated)
        The function will:
        - skip rows missing title or release_date
        - skip movies that already exist (same title + release_date)
        - create missing genres and link them via movie_genre
        """
        file_path = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        inserted = 0
        skipped = 0
        failed = 0

        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # flexible header names
                    title = (row.get('title') or row.get('movie_name') or row.get('name') or '').strip()
                    release_date = (row.get('release_date') or row.get('date') or row.get('year') or '').strip()
                    language = (row.get('language') or '').strip()
                    description = (row.get('description') or row.get('summary') or '').strip()
                    genres_raw = (row.get('genres') or row.get('genre') or '').strip()

                    if not title or not release_date:
                        skipped += 1
                        continue

                    # If year-only provided, convert to YYYY-01-01
                    if re.fullmatch(r"\d{4}$", release_date):
                        release_date = release_date + "-01-01"

                    try:
                        # avoid duplicates (same title + release_date)
                        cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s AND release_date=%s", (title, release_date))
                        if cursor.fetchone():
                            skipped += 1
                            continue

                        cursor.execute(
                            "INSERT INTO movies (movie_name, release_date, language, description) VALUES (%s,%s,%s,%s)",
                            (title, release_date, language or None, description or None)
                        )
                        movie_id = cursor.lastrowid

                        # handle genres
                        if genres_raw:
                            parts = [p.strip() for p in re.split(r'[,|;]', genres_raw) if p.strip()]
                            for g in parts:
                                cursor.execute("SELECT genre_id FROM genres WHERE genre_name=%s", (g,))
                                res = cursor.fetchone()
                                if res:
                                    gid = res[0]
                                else:
                                    cursor.execute("INSERT INTO genres (genre_name) VALUES (%s)", (g,))
                                    gid = cursor.lastrowid
                                # link
                                try:
                                    cursor.execute("INSERT INTO movie_genre (movie_id, genre_id) VALUES (%s,%s)", (movie_id, gid))
                                except Exception:
                                    # ignore duplicate links                                    python -m pip install customtkinter mysql-connector-python
                                    pass

                        inserted += 1
                    except Exception as e:
                        failed += 1
                        print("Error importing row:", e)

            conn.commit()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import CSV: {e}")
            return

        messagebox.showinfo("Import Complete", f"Inserted: {inserted}\nSkipped: {skipped}\nFailed: {failed}")

    def import_all_csv(self):
        """Open a CSV file and import rows into the full database.

        The CSV must include a required 'type' column which indicates which
        table/record the row represents. Supported types (case-insensitive):
        user, movie, genre, cast, studio, platform, episode, review,
        movie_genre, movie_cast, movie_studio, movie_platform,
        distribution, follow, donation, contains_episode

        Each type accepts flexible column names. See the project README or
        the specification printed by the function (messagebox) for expected
        column names for each type.
        """
        file_path = filedialog.askopenfilename(title="Select full-database CSV", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        inserted, skipped, failed = self.import_all_csv_from_path(file_path)
        messagebox.showinfo("Import Complete", f"Inserted: {inserted}\nSkipped: {skipped}\nFailed: {failed}")

    def import_all_csv_from_path(self, file_path):
        """Helper to import a CSV where each row has a 'type' column.

        Returns (inserted, skipped, failed).
        """
        def parse_date(date_str):
            if not date_str:
                return None
            date_str = date_str.strip()
            if re.fullmatch(r"\d{4}$", date_str):
                return date_str + "-01-01"
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except:
                return None

        inserted = skipped = failed = 0
        error_rows = []
        row_num = 0
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_num += 1
                    typ = (row.get('type') or row.get('record_type') or '').strip().lower()
                    if not typ:
                        skipped += 1
                        continue

                    try:
                        if typ in ('user', 'users'):
                            username = (row.get('username') or row.get('user') or '').strip()
                            email = (row.get('email') or '').strip() or None
                            password = (row.get('password') or '').strip() or 'changeme'
                            if not username:
                                skipped += 1
                                continue
                            cursor.execute("SELECT user_id FROM users WHERE username=%s", (username,))
                            if cursor.fetchone():
                                skipped += 1
                                continue
                            if email:
                                cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
                                if cursor.fetchone():
                                    skipped += 1
                                    continue
                            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s,%s,%s)", (username, email, password))
                            inserted += 1

                        elif typ in ('movie', 'movies'):
                            title = (row.get('title') or row.get('movie_name') or row.get('name') or '').strip()
                            release_date = parse_date(row.get('release_date') or row.get('date') or row.get('year') or '')
                            language = (row.get('language') or '').strip() or None
                            description = (row.get('description') or row.get('summary') or '').strip() or None
                            if not title:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s AND (release_date=%s OR %s IS NULL)", (title, release_date, release_date))
                            if cursor.fetchone():
                                skipped += 1
                                continue
                            cursor.execute("INSERT INTO movies (movie_name, release_date, language, description) VALUES (%s,%s,%s,%s)", (title, release_date, language, description))
                            inserted += 1

                        elif typ in ('genre', 'genres'):
                            gname = (row.get('genre_name') or row.get('name') or row.get('genre') or '').strip()
                            if not gname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT genre_id FROM genres WHERE genre_name=%s", (gname,))
                            if cursor.fetchone():
                                skipped += 1
                                continue
                            cursor.execute("INSERT INTO genres (genre_name) VALUES (%s)", (gname,))
                            inserted += 1

                        elif typ in ('cast', 'cast_member', 'cast_members'):
                            name = (row.get('name') or row.get('actor') or '').strip()
                            dob = parse_date(row.get('dob') or row.get('birthdate') or '')
                            bio = (row.get('bio') or row.get('biography') or '').strip() or None
                            age = row.get('age') or None
                            if not name:
                                skipped += 1
                                continue
                            cursor.execute("SELECT cast_id FROM cast_members WHERE name=%s", (name,))
                            if cursor.fetchone():
                                skipped += 1
                                continue
                            cursor.execute("INSERT INTO cast_members (name, dob, bio, age) VALUES (%s,%s,%s,%s)", (name, dob, bio, age))
                            inserted += 1

                        elif typ in ('studio', 'studios'):
                            sname = (row.get('studio_name') or row.get('name') or '').strip()
                            country = (row.get('country') or '').strip() or None
                            if not sname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT studio_id FROM studios WHERE studio_name=%s", (sname,))
                            if cursor.fetchone():
                                skipped += 1
                                continue
                            cursor.execute("INSERT INTO studios (studio_name, country) VALUES (%s,%s)", (sname, country))
                            inserted += 1

                        elif typ in ('platform', 'streaming_platform', 'streaming_platforms'):
                            pname = (row.get('platform_name') or row.get('name') or '').strip()
                            sub = (row.get('subscription_type') or row.get('subscription') or '').strip() or None
                            if not pname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT platform_id FROM streaming_platforms WHERE platform_name=%s", (pname,))
                            if cursor.fetchone():
                                skipped += 1
                                continue
                            cursor.execute("INSERT INTO streaming_platforms (platform_name, subscription_type) VALUES (%s,%s)", (pname, sub))
                            inserted += 1

                        elif typ in ('episode', 'episodes'):
                            series_title = (row.get('series_title') or row.get('title') or row.get('movie_name') or '').strip()
                            season_raw = (row.get('season') or row.get('season_number') or '').strip()
                            ep_raw = (row.get('episode') or row.get('episode_number') or '').strip()
                            ep_title = (row.get('episode_title') or row.get('episode_title') or row.get('ep_title') or row.get('title') or '').strip() or None
                            release_date = parse_date(row.get('release_date') or row.get('air_date') or row.get('date') or '')
                            try:
                                season = int(season_raw) if season_raw else 1
                            except:
                                season = 1
                            try:
                                episode_number = int(ep_raw) if ep_raw else None
                            except:
                                episode_number = None
                            if not series_title:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (series_title,))
                            res = cursor.fetchone()
                            if res:
                                movie_id = res[0]
                            else:
                                cursor.execute("INSERT INTO movies (movie_name, release_date) VALUES (%s,%s)", (series_title, release_date))
                                movie_id = cursor.lastrowid

                            if episode_number is not None:
                                cursor.execute("SELECT episode_id FROM episodes WHERE movie_id=%s AND season_number=%s AND episode_number=%s", (movie_id, season, episode_number))
                                if cursor.fetchone():
                                    skipped += 1
                                    continue

                            # use column names compatible with the rest of the app
                            cursor.execute("INSERT INTO episodes (movie_id, season_number, episode_title, episode_number, release_date) VALUES (%s,%s,%s,%s,%s)", (movie_id, season, ep_title or None, episode_number, release_date or None))
                            inserted += 1

                        elif typ in ('review', 'reviews', 'rating', 'ratings'):
                            uname = (row.get('username') or row.get('user') or '').strip()
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            raw_rating = row.get('rating') or ''
                            # normalize rating to DB DECIMAL(2,1). Accept formats: 8, 8.5, 80, 8/10, 80%, etc.
                            rating = None
                            if raw_rating is not None and str(raw_rating).strip() != '':
                                try:
                                    s = str(raw_rating).strip()
                                    if '/' in s:
                                        a, b = s.split('/')[:2]
                                        num = float(a)
                                        den = float(b) if b else 10.0
                                        val = (num / den) * 10.0
                                    elif s.endswith('%'):
                                        val = float(s.rstrip('%')) / 10.0
                                    else:
                                        val = float(s)
                                        if val > 10 and val <= 100:
                                            val = val / 10.0
                                    # clamp and round to one decimal place
                                    val = round(max(0.0, min(9.9, val)), 1)
                                    rating = val
                                except Exception:
                                    rating = None
                            comment = (row.get('comment') or row.get('review') or '').strip() or None
                            if not uname or not title:
                                skipped += 1
                                continue
                            cursor.execute("SELECT user_id FROM users WHERE username=%s", (uname,))
                            ures = cursor.fetchone()
                            if not ures:
                                # create minimal user
                                cursor.execute("INSERT INTO users (username, password) VALUES (%s,%s)", (uname, 'changeme'))
                                uid = cursor.lastrowid
                            else:
                                uid = ures[0]
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            cursor.execute("INSERT INTO reviews_ratings (user_id, movie_id, rating, comment) VALUES (%s,%s,%s,%s)", (uid, mid, rating, comment))
                            inserted += 1

                        elif typ in ('movie_genre',):
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            gname = (row.get('genre') or row.get('genre_name') or '').strip()
                            if not title or not gname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            cursor.execute("SELECT genre_id FROM genres WHERE genre_name=%s", (gname,))
                            gres = cursor.fetchone()
                            if not gres:
                                cursor.execute("INSERT INTO genres (genre_name) VALUES (%s)", (gname,))
                                gid = cursor.lastrowid
                            else:
                                gid = gres[0]
                            # avoid duplicate junction inserts
                            cursor.execute("SELECT 1 FROM movie_genre WHERE movie_id=%s AND genre_id=%s", (mid, gid))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO movie_genre (movie_id, genre_id) VALUES (%s,%s)", (mid, gid))
                            inserted += 1

                        elif typ in ('movie_cast',):
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            actor = (row.get('actor') or row.get('name') or '').strip()
                            role = (row.get('role') or '').strip() or None
                            char = (row.get('character_name') or row.get('character') or '').strip() or None
                            if not title or not actor:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            cursor.execute("SELECT cast_id FROM cast_members WHERE name=%s", (actor,))
                            cres = cursor.fetchone()
                            if not cres:
                                cursor.execute("INSERT INTO cast_members (name) VALUES (%s)", (actor,))
                                cid = cursor.lastrowid
                            else:
                                cid = cres[0]
                            # avoid duplicate movie_cast
                            cursor.execute("SELECT 1 FROM movie_cast WHERE movie_id=%s AND cast_id=%s", (mid, cid))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO movie_cast (movie_id, cast_id, role, character_name) VALUES (%s,%s,%s,%s)", (mid, cid, role, char))
                            inserted += 1

                        elif typ in ('movie_studio',):
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            sname = (row.get('studio_name') or row.get('studio') or '').strip()
                            if not title or not sname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            cursor.execute("SELECT studio_id FROM studios WHERE studio_name=%s", (sname,))
                            sres = cursor.fetchone()
                            if not sres:
                                cursor.execute("INSERT INTO studios (studio_name) VALUES (%s)", (sname,))
                                sid = cursor.lastrowid
                            else:
                                sid = sres[0]
                            cursor.execute("SELECT 1 FROM movie_studio WHERE movie_id=%s AND studio_id=%s", (mid, sid))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO movie_studio (movie_id, studio_id) VALUES (%s,%s)", (mid, sid))
                            inserted += 1

                        elif typ in ('movie_platform',):
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            pname = (row.get('platform_name') or row.get('platform') or '').strip()
                            avail = parse_date(row.get('availability_date') or row.get('availability') or '')
                            if not title or not pname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            cursor.execute("SELECT platform_id FROM streaming_platforms WHERE platform_name=%s", (pname,))
                            pres = cursor.fetchone()
                            if not pres:
                                cursor.execute("INSERT INTO streaming_platforms (platform_name) VALUES (%s)", (pname,))
                                pid = cursor.lastrowid
                            else:
                                pid = pres[0]
                            cursor.execute("SELECT 1 FROM movie_platform WHERE movie_id=%s AND platform_id=%s", (mid, pid))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO movie_platform (movie_id, platform_id, availability_date) VALUES (%s,%s,%s)", (mid, pid, avail))
                            inserted += 1

                        elif typ in ('distribution', 'movie_distribution'):
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            sname = (row.get('studio_name') or row.get('studio') or '').strip()
                            pname = (row.get('platform_name') or row.get('platform') or '').strip()
                            dist_date = parse_date(row.get('distribution_date') or row.get('date') or '')
                            territory = (row.get('territory') or row.get('region') or '').strip() or 'worldwide'
                            if not title or not sname or not pname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            cursor.execute("SELECT studio_id FROM studios WHERE studio_name=%s", (sname,))
                            sres = cursor.fetchone()
                            if not sres:
                                cursor.execute("INSERT INTO studios (studio_name) VALUES (%s)", (sname,))
                                sid = cursor.lastrowid
                            else:
                                sid = sres[0]
                            cursor.execute("SELECT platform_id FROM streaming_platforms WHERE platform_name=%s", (pname,))
                            pres = cursor.fetchone()
                            if not pres:
                                cursor.execute("INSERT INTO streaming_platforms (platform_name) VALUES (%s)", (pname,))
                                pid = cursor.lastrowid
                            else:
                                pid = pres[0]
                            cursor.execute("INSERT INTO movie_distribution (movie_id, studio_id, platform_id, distribution_date, territory) VALUES (%s,%s,%s,%s,%s)", (mid, sid, pid, dist_date, territory))
                            inserted += 1

                        elif typ in ('follow', 'user_follow'):
                            follower = (row.get('follower') or row.get('follower_username') or row.get('follower_id') or '').strip()
                            followed = (row.get('followed') or row.get('followed_username') or row.get('followed_id') or '').strip()
                            if not follower or not followed:
                                skipped += 1
                                continue
                            # support usernames or ids; prefer username
                            def resolve_user(val):
                                if val.isdigit():
                                    return int(val)
                                cursor.execute("SELECT user_id FROM users WHERE username=%s", (val,))
                                r = cursor.fetchone()
                                if r:
                                    return r[0]
                                cursor.execute("INSERT INTO users (username, password) VALUES (%s,%s)", (val, 'changeme'))
                                return cursor.lastrowid
                            fid = resolve_user(follower)
                            tid = resolve_user(followed)
                            if fid == tid:
                                skipped += 1
                                continue
                            try:
                                cursor.execute("INSERT INTO user_follow (follower_id, followed_id) VALUES (%s,%s)", (fid, tid))
                                inserted += 1
                            except Exception:
                                skipped += 1

                        elif typ in ('donation', 'donations'):
                            uname = (row.get('username') or row.get('user') or row.get('user_id') or '').strip()
                            amount = row.get('donation_amount') or row.get('amount') or 0
                            comment = (row.get('comment') or '').strip() or None
                            if not uname:
                                skipped += 1
                                continue
                            cursor.execute("SELECT user_id FROM users WHERE username=%s", (uname,))
                            r = cursor.fetchone()
                            if not r:
                                cursor.execute("INSERT INTO users (username, password) VALUES (%s,%s)", (uname, 'changeme'))
                                uid = cursor.lastrowid
                            else:
                                uid = r[0]
                            cursor.execute("INSERT INTO donations (user_id, donation_amount, comment) VALUES (%s,%s,%s)", (uid, amount, comment))
                            inserted += 1

                        elif typ in ('contains_episode',):
                            eid = row.get('episode_id') or row.get('episode') or ''
                            title = (row.get('title') or row.get('movie_name') or '').strip()
                            if not eid or not title:
                                skipped += 1
                                continue
                            cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (title,))
                            mres = cursor.fetchone()
                            if not mres:
                                cursor.execute("INSERT INTO movies (movie_name) VALUES (%s)", (title,))
                                mid = cursor.lastrowid
                            else:
                                mid = mres[0]
                            # ensure episode exists
                            try:
                                eid_int = int(eid)
                            except:
                                skipped += 1
                                continue
                            cursor.execute("SELECT 1 FROM episodes WHERE episode_id=%s", (eid_int,))
                            if not cursor.fetchone():
                                # cannot link to non-existent episode, skip
                                skipped += 1
                                continue
                            cursor.execute("SELECT 1 FROM contains_episodes WHERE episode_id=%s AND movie_id=%s", (eid_int, mid))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO contains_episodes (episode_id, movie_id) VALUES (%s,%s)", (eid_int, mid))
                                inserted += 1

                        else:
                            # unknown type
                            skipped += 1

                    except Exception as e:
                        failed += 1
                        print(f"Import row error for type '{typ}': {e}")
                        # Optionally print the row: print(row)

            conn.commit()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import CSV: {e}")
            return (0, 0, 1)

        return (inserted, skipped, failed)

    def _movie_card_grid(self):
        # Scrollable canvas for grid
        grid_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        grid_frame.pack(fill='both', expand=True, padx=20, pady=12)

        canvas = ctk.CTkCanvas(grid_frame, bg=IMDB_DARK_BG, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(grid_frame, orientation='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = ctk.CTkFrame(canvas, fg_color=IMDB_DARK_BG)
        # create_window requires a tk widget; get underlying tk widget
        canvas.create_window((0,0), window=inner, anchor='nw')

        # Query movies
        cursor.execute("""
            SELECT m.movie_id, m.movie_name, YEAR(m.release_date) as yr, m.language,
                GROUP_CONCAT(DISTINCT g.genre_name) as genres,
                ROUND(AVG(r.rating),1) as avg_rating
            FROM movies m
            LEFT JOIN movie_genre mg ON m.movie_id=mg.movie_id
            LEFT JOIN genres g ON mg.genre_id=g.genre_id
            LEFT JOIN reviews_ratings r ON m.movie_id=r.movie_id
            GROUP BY m.movie_id
            ORDER BY m.release_date DESC
        """)
        rows = cursor.fetchall()

        # Use batched rendering to avoid creating all widgets at once
        def render_movie_card(idx, r, parent):
            cid = r[0]
            title = r[1]
            year = r[2]
            lang = r[3]
            genres = r[4] or ''
            rating = r[5] or 'N/A'

            cols = 4
            padx = 12
            pady = 12
            card = ctk.CTkFrame(parent, fg_color=IMDB_GRAY, corner_radius=10, width=240, height=360)
            card.grid(row=idx//cols, column=idx%cols, padx=padx, pady=pady)
            poster = ctk.CTkLabel(card, text="", bg_color=IMDB_GRAY)
            poster.pack(pady=(8,2))
            ctk.CTkLabel(card, text=title, font=("Arial Black", 12), text_color=IMDB_YELLOW, wraplength=220).pack()
            ctk.CTkLabel(card, text=f"{year} • {lang or ''}", font=FONT_NORMAL, text_color="white").pack()
            ctk.CTkLabel(card, text=genres, font=("Arial", 10, "italic"), text_color="#cccccc", wraplength=220).pack(pady=(4,8))
            ctk.CTkLabel(card, text=f"Rating: {rating}", font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack()
            ctk.CTkButton(card, text="Details", fg_color=IMDB_YELLOW, command=lambda mid=cid: self.show_movie_detail(mid), width=160).pack(pady=(10,8))

        # Use a manual "Load more" button that loads items in batches of 20
        render_next, has_more = self._create_scroll_batch(canvas, inner, rows, render_movie_card, batch_size=20)

        controls = ctk.CTkFrame(grid_frame, fg_color=IMDB_DARK_BG)
        controls.pack(fill='x', pady=(6,12))
        load_btn = ctk.CTkButton(controls, text="Load more", fg_color=IMDB_YELLOW, width=140)
        load_btn.pack(anchor='center')

        def on_load_clicked():
            try:
                more = render_next()
                if not more:
                    load_btn.configure(state='disabled', text='All loaded')
            except Exception:
                # disable on unexpected error to avoid infinite clicks
                load_btn.configure(state='disabled')

        load_btn.configure(command=on_load_clicked)
        # If initial render already loaded everything, disable immediately
        try:
            if not has_more():
                load_btn.configure(state='disabled', text='All loaded')
        except Exception:
            pass

    # ========== MOVIE CARD ==========
    def _movie_card(self, master, movie_row):
        card = ctk.CTkFrame(master, fg_color=IMDB_GRAY, corner_radius=18)
        card.pack(padx=8, pady=8, side="left")
        # Placeholder for poster - replace with real img logic
        poster = ctk.CTkLabel(card, text="🎞️", font=("Arial", 42), text_color=IMDB_YELLOW)
        poster.pack(pady=6)
        # Details
        ctk.CTkLabel(card, text=movie_row[1], font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack()
        year = movie_row[2].year if movie_row[2] else ""
        ctk.CTkLabel(card, text=f"{year} • {movie_row[3]}", font=FONT_NORMAL, text_color="white").pack()
        ctk.CTkLabel(card, text=movie_row[4] or "", font=("Arial Italic", 11), text_color="#aaaaaa", wraplength=230).pack(pady=(2,8))

    def _create_scroll_batch(self, canvas, inner_frame, items, render_fn, batch_size=100, threshold=200):
        """Render items in explicit batches and return a loader function.

        This helper no longer auto-loads on scroll. Instead it renders the first
        batch immediately and returns a tuple (render_next_batch, has_more_fn).

        - render_next_batch(): when called, renders the next batch and returns
          True if more items remain after the render, False if everything is loaded.
        - has_more_fn(): returns True if more items remain to be loaded.

        canvas: the scrolling canvas widget
        inner_frame: the frame that holds item widgets
        items: list of data rows
        render_fn: function(idx, item, parent) -> creates UI for one item
        batch_size: how many items to create per click
        """
        total = len(items)
        state = {'next_idx': 0}

        def render_next_batch():
            start = state['next_idx']
            if start >= total:
                return False
            end = min(total, start + batch_size)
            for i in range(start, end):
                render_fn(i, items[i], inner_frame)
            state['next_idx'] = end
            inner_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox('all'))
            return state['next_idx'] < total

        def has_more():
            return state['next_idx'] < total

        # initial batch
        render_next_batch()

        # keep automatic scrollregion updates but do not auto-load more items
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        return render_next_batch, has_more

    def show_movie_detail(self, movie_id):
        self.clear_page()
        # Get full details
        cursor.execute("""
            SELECT m.movie_name, m.release_date, m.description, m.language,
                ROUND(AVG(r.rating),1),
                GROUP_CONCAT(DISTINCT g.genre_name)
            FROM movies m
            LEFT JOIN reviews_ratings r ON m.movie_id=r.movie_id
            LEFT JOIN movie_genre mg ON m.movie_id=mg.movie_id
            LEFT JOIN genres g ON mg.genre_id=g.genre_id
            WHERE m.movie_id=%s
            GROUP BY m.movie_id
        """, (movie_id,))
        row = cursor.fetchone()
        if not row:
            imdb_heading(self.page, "Movie not found!")
            return
        imdb_heading(self.page, row[0])
        imdb_subheading(self.page, f"Released: {row[1]} • {row[3] or ''}")
        ctk.CTkLabel(self.page, text=row[2] or "(No summary available)", wraplength=750, font=FONT_NORMAL, text_color="white", anchor="w", bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20)

        ctk.CTkLabel(self.page, text="Genres: " + (row[5] or ""), font=FONT_NORMAL, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20)
        ctk.CTkLabel(self.page, text="Avg Rating: " + (str(row[4]) if row[4] else "N/A"), font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20)

        # Cast table
        ctk.CTkLabel(self.page, text="Cast:", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20, pady=(20,4))
        cast_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        cast_frame.pack(anchor="w", padx=20)
        cast_cols = ("Name", "Character", "Age")
        tree = ttk.Treeview(cast_frame, columns=cast_cols, show="headings", height=6)
        for col in cast_cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=140)
        self._style_treeview(tree, heading_font=("Arial", 11, "bold"), cell_font=("Arial", 10), rowheight=28)
        # add vertical scrollbar
        tree_scroll = ttk.Scrollbar(cast_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side='right', fill='y')
        tree.pack(anchor="w", fill='both', expand=True)
        cursor.execute("""
            SELECT c.name, mc.character_name, calc_age(c.dob) FROM movie_cast mc
            JOIN cast_members c ON mc.cast_id = c.cast_id
            WHERE mc.movie_id=%s
        """, (movie_id,))
        for i, cr in enumerate(cursor.fetchall()):
            tag = 'even' if i % 2 == 0 else 'odd'
            tree.insert('', 'end', values=cr, tags=(tag,))

        # Reviews table
        ctk.CTkLabel(self.page, text="User Reviews:", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20, pady=(32,4))
        review_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        review_frame.pack(anchor="w", padx=20)
        rev_cols = ("User", "Rating", "Comment")
        rtree = ttk.Treeview(review_frame, columns=rev_cols, show="headings", height=8)
        for col in rev_cols:
            rtree.heading(col, text=col)
            rtree.column(col, anchor="center", width=220)
        self._style_treeview(rtree, heading_font=("Arial", 11, "bold"), cell_font=("Arial", 10), rowheight=28)
        rtree_scroll = ttk.Scrollbar(review_frame, orient='vertical', command=rtree.yview)
        rtree.configure(yscrollcommand=rtree_scroll.set)
        rtree_scroll.pack(side='right', fill='y')
        rtree.pack(anchor="w", fill='both', expand=True)
        cursor.execute("""
            SELECT u.username, r.rating, r.comment FROM reviews_ratings r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.movie_id=%s
            ORDER BY r.review_date DESC
        """, (movie_id,))
        for i, rv in enumerate(cursor.fetchall()):
            tag = 'even' if i % 2 == 0 else 'odd'
            rtree.insert('', 'end', values=rv, tags=(tag,))

        # Streaming platforms
        ctk.CTkLabel(self.page, text="Available On:", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor='w', padx=20, pady=(18,4))
        plat_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        plat_frame.pack(anchor='w', padx=20)
        pcols = ('Platform', 'Subscription', 'Available Since')
        ptre = ttk.Treeview(plat_frame, columns=pcols, show='headings', height=6)
        for c in pcols:
            ptre.heading(c, text=c)
            ptre.column(c, anchor='center', width=200)
        self._style_treeview(ptre, heading_font=("Arial", 11, "bold"), cell_font=("Arial", 10), rowheight=24)
        pscroll = ttk.Scrollbar(plat_frame, orient='vertical', command=ptre.yview)
        ptre.configure(yscrollcommand=pscroll.set)
        pscroll.pack(side='right', fill='y')
        ptre.pack(anchor='w', fill='x')
        try:
            cursor.execute('''
                SELECT sp.platform_name, sp.subscription_type, mp.availability_date
                FROM movie_platform mp
                JOIN streaming_platforms sp ON mp.platform_id=sp.platform_id
                WHERE mp.movie_id=%s
            ''', (movie_id,))
            for i, pr in enumerate(cursor.fetchall()):
                tag = 'even' if i%2==0 else 'odd'
                ptre.insert('', 'end', values=(pr[0], pr[1] or '', pr[2]), tags=(tag,))
        except Exception:
            pass

        # Distribution territories
        ctk.CTkLabel(self.page, text='Distribution:', font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor='w', padx=20, pady=(12,4))
        df = ctk.CTkFrame(self.page)
        df.pack(anchor='w', padx=20)
        dcols = ('Studio', 'Platform', 'Territory', 'Date')
        dtree = ttk.Treeview(df, columns=dcols, show='headings', height=6)
        for c in dcols:
            dtree.heading(c, text=c)
            dtree.column(c, anchor='center', width=180)
        self._style_treeview(dtree)
        dscroll = ttk.Scrollbar(df, orient='vertical', command=dtree.yview)
        dtree.configure(yscrollcommand=dscroll.set)
        dscroll.pack(side='right', fill='y')
        dtree.pack(anchor='w', fill='x')
        try:
            cursor.execute('''
                SELECT s.studio_name, sp.platform_name, md.territory, md.distribution_date
                FROM movie_distribution md
                LEFT JOIN studios s ON md.studio_id=s.studio_id
                LEFT JOIN streaming_platforms sp ON md.platform_id=sp.platform_id
                WHERE md.movie_id=%s
            ''', (movie_id,))
            for i, dr in enumerate(cursor.fetchall()):
                tag = 'even' if i%2==0 else 'odd'
                dtree.insert('', 'end', values=(dr[0] or '', dr[1] or '', dr[2] or '', dr[3] or ''), tags=(tag,))
        except Exception:
            pass

        # Watchlist action
        wf = ctk.CTkFrame(self.page)
        wf.pack(anchor='e', padx=20, pady=(12,12))
        def add_watchlist():
            if not self.current_user:
                messagebox.showerror('Auth', 'Login to add to watchlist')
                return
            try:
                self._ensure_watchlist_table()
                cursor.execute('INSERT INTO user_watchlist (user_id, movie_id) VALUES (%s,%s)', (self.current_user[0], movie_id))
                conn.commit()
                messagebox.showinfo('Added', 'Added to your watchlist')
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        def remove_watchlist():
            if not self.current_user:
                messagebox.showerror('Auth', 'Login to remove from watchlist')
                return
            try:
                cursor.execute('DELETE FROM user_watchlist WHERE user_id=%s AND movie_id=%s', (self.current_user[0], movie_id))
                conn.commit()
                messagebox.showinfo('Removed', 'Removed from your watchlist')
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        ctk.CTkButton(wf, text='Add to Watchlist', fg_color=IMDB_YELLOW, command=add_watchlist, width=160).pack(side='left', padx=6)
        ctk.CTkButton(wf, text='Remove from Watchlist', fg_color=IMDB_YELLOW, command=remove_watchlist, width=200).pack(side='left', padx=6)

    # ========== CAST ==========
    def show_cast(self):
        """Show cast members using the same batched/grid rendering as movies.

        This renders cast in a card grid and provides a "Load more" button to
        progressively render items (to avoid creating all widgets at once).
        """
        self.clear_page()
        imdb_heading(self.page, "Cast & Crew")
        ctk.CTkLabel(self.page, text="Browse All", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20, pady=5)

        grid_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        grid_frame.pack(fill='both', expand=True, padx=20, pady=12)

        canvas = ctk.CTkCanvas(grid_frame, bg=IMDB_DARK_BG, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(grid_frame, orientation='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = ctk.CTkFrame(canvas, fg_color=IMDB_DARK_BG)
        canvas.create_window((0,0), window=inner, anchor='nw')

        # Query cast members
        cursor.execute("SELECT cast_id, name, dob, bio FROM cast_members ORDER BY name")
        rows = cursor.fetchall()

        def render_person_card(idx, r, parent):
            pid = r[0]
            name = r[1]
            dob = r[2]
            bio = r[3] or ''

            cols = 4
            padx = 12
            pady = 12
            card = ctk.CTkFrame(parent, fg_color=IMDB_GRAY, corner_radius=10, width=220, height=260)
            card.grid(row=idx//cols, column=idx%cols, padx=padx, pady=pady)
            photo = ctk.CTkLabel(card, text="🙂", font=("Arial", 34), text_color=IMDB_YELLOW, bg_color=IMDB_GRAY)
            photo.pack(pady=(8,2))
            ctk.CTkLabel(card, text=name, font=("Arial Black", 12), text_color=IMDB_YELLOW, wraplength=200).pack()
            age_text = self.calc_age(dob) if dob else ''
            ctk.CTkLabel(card, text=f"Age: {age_text}", font=FONT_NORMAL, text_color="white").pack()
            ctk.CTkLabel(card, text=(bio[:110] + '...') if len(bio) > 110 else bio, font=("Arial", 10, "italic"), text_color="#cccccc", wraplength=200).pack(pady=(6,8))
            ctk.CTkButton(card, text="Filmography", fg_color=IMDB_YELLOW, command=lambda pid=pid: self.show_filmography(pid), width=140).pack(pady=(6,8))

        render_next, has_more = self._create_scroll_batch(canvas, inner, rows, render_person_card, batch_size=20)

        controls = ctk.CTkFrame(grid_frame, fg_color=IMDB_DARK_BG)
        controls.pack(fill='x', pady=(6,12))
        load_btn = ctk.CTkButton(controls, text="Load more", fg_color=IMDB_YELLOW, width=140)
        load_btn.pack(anchor='center')

        def on_load_clicked():
            try:
                more = render_next()
                if not more:
                    load_btn.configure(state='disabled', text='All loaded')
            except Exception:
                load_btn.configure(state='disabled')

        load_btn.configure(command=on_load_clicked)
        try:
            if not has_more():
                load_btn.configure(state='disabled', text='All loaded')
        except Exception:
            pass

    def _person_card(self, master, pid, name, dob, bio):
        card = ctk.CTkFrame(master, fg_color=IMDB_GRAY, corner_radius=12)
        card.pack(padx=12, pady=8, anchor="w")
        # Placeholder for profile img
        photolabel = ctk.CTkLabel(card, text="🙂", font=("Arial", 38), text_color=IMDB_YELLOW)
        photolabel.pack(side="left", padx=8, pady=8)
        # Person details
        ctk.CTkLabel(card, text=name, font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack(anchor="w")
        if dob:
            ctk.CTkLabel(card, text=f"Age: {self.calc_age(dob)}", font=FONT_NORMAL, text_color="white").pack(anchor="w")
        if bio:
            ctk.CTkLabel(card, text=bio, font=("Arial Italic", 11), text_color="#cccccc", wraplength=230).pack(anchor="w", pady=(0,8))

        ctk.CTkButton(card, text="Filmography", fg_color=IMDB_YELLOW, command=lambda: self.show_filmography(pid), width=120).pack(anchor="e", side="bottom", padx=9)

    def calc_age(self, dob):
        from datetime import datetime
        try:
            year = int(str(dob)[:4])
            return datetime.now().year - year
        except:
            return ""

    def show_filmography(self, pid):
        self.clear_page()
        imdb_heading(self.page, "Filmography")
        imdb_subheading(self.page, "Movies and Roles")
        table_frame = ctk.CTkFrame(self.page)
        table_frame.pack(fill="both", padx=20)
        cols = ("Movie", "Role", "Year")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=270)
        self._style_treeview(tree, heading_font=("Arial", 11, "bold"), cell_font=("Arial", 10), rowheight=28)
        tree_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side='right', fill='y')
        tree.pack(fill="both", expand=True)
        cursor.execute("""
            SELECT m.movie_name, mc.role, m.release_date
            FROM movie_cast mc
            JOIN movies m ON mc.movie_id = m.movie_id
            WHERE mc.cast_id=%s
            ORDER BY m.release_date DESC
        """, (pid,))
        for i, row in enumerate(cursor.fetchall()):
            tag = 'even' if i % 2 == 0 else 'odd'
            tree.insert('', 'end', values=(row[0], row[1], row[2]), tags=(tag,))

    # ========== SERIES/TV ==========
    def show_series(self):
        # Use the same card-grid UI as Movies/Cast for a consistent look
        self.clear_page()
        imdb_heading(self.page, "TV & Web Series")
        imdb_subheading(self.page, "Browse all series")

        grid_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        grid_frame.pack(fill='both', expand=True, padx=20, pady=12)

        canvas = ctk.CTkCanvas(grid_frame, bg=IMDB_DARK_BG, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(grid_frame, orientation='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = ctk.CTkFrame(canvas, fg_color=IMDB_DARK_BG)
        canvas.create_window((0,0), window=inner, anchor='nw')

        # Query series (movies that have episodes). Include some extra metadata for cards.
        cursor.execute("""
            SELECT m.movie_id, m.movie_name, YEAR(m.release_date) as yr, m.language,
                GROUP_CONCAT(DISTINCT g.genre_name) as genres,
                ROUND(AVG(r.rating),1) as avg_rating, COUNT(e.episode_id) as ep_count,
                MAX(e.season_number) as seasons
            FROM movies m
            JOIN episodes e ON m.movie_id = e.movie_id
            LEFT JOIN movie_genre mg ON m.movie_id=mg.movie_id
            LEFT JOIN genres g ON mg.genre_id=g.genre_id
            LEFT JOIN reviews_ratings r ON m.movie_id=r.movie_id
            GROUP BY m.movie_id
            HAVING COUNT(e.episode_id) > 0
            ORDER BY m.release_date DESC
        """)
        rows = cursor.fetchall()

        def render_series_card(idx, r, parent):
            sid = r[0]
            title = r[1]
            year = r[2]
            lang = r[3]
            genres = r[4] or ''
            rating = r[5] or 'N/A'
            ep_count = r[6] or 0
            seasons = r[7] or 1

            cols = 4
            padx = 12
            pady = 12
            card = ctk.CTkFrame(parent, fg_color=IMDB_GRAY, corner_radius=10, width=240, height=360)
            card.grid(row=idx//cols, column=idx%cols, padx=padx, pady=pady)
            poster = ctk.CTkLabel(card, text="📺", bg_color=IMDB_GRAY)
            poster.pack(pady=(8,2))
            ctk.CTkLabel(card, text=title, font=("Arial Black", 12), text_color=IMDB_YELLOW, wraplength=220).pack()
            ctk.CTkLabel(card, text=f"{year} • {lang or ''}", font=FONT_NORMAL, text_color="white").pack()
            ctk.CTkLabel(card, text=f"Seasons: {seasons} • Episodes: {ep_count}", font=("Arial", 10, "italic"), text_color="#cccccc").pack(pady=(4,4))
            ctk.CTkLabel(card, text=genres, font=("Arial", 10, "italic"), text_color="#cccccc", wraplength=220).pack()
            ctk.CTkLabel(card, text=f"Rating: {rating}", font=FONT_SUBHEADER, text_color=IMDB_YELLOW).pack()
            ctk.CTkButton(card, text="Details", fg_color=IMDB_YELLOW, command=lambda mid=sid: self.show_series_detail(mid), width=160).pack(pady=(10,8))

        render_next, has_more = self._create_scroll_batch(canvas, inner, rows, render_series_card, batch_size=20)

        controls = ctk.CTkFrame(grid_frame, fg_color=IMDB_DARK_BG)
        controls.pack(fill='x', pady=(6,12))
        load_btn = ctk.CTkButton(controls, text="Load more", fg_color=IMDB_YELLOW, width=140)
        load_btn.pack(anchor='center')

        def on_load_clicked():
            try:
                more = render_next()
                if not more:
                    load_btn.configure(state='disabled', text='All loaded')
            except Exception:
                load_btn.configure(state='disabled')

        load_btn.configure(command=on_load_clicked)
        try:
            if not has_more():
                load_btn.configure(state='disabled', text='All loaded')
        except Exception:
            pass

    def show_series_detail(self, series_id):
        """Display series-level detail and episode list (seasons/episodes)."""
        self.clear_page()
        cursor.execute("""
            SELECT m.movie_name, m.release_date, m.description, m.language,
                ROUND(AVG(r.rating),1), GROUP_CONCAT(DISTINCT g.genre_name)
            FROM movies m
            LEFT JOIN reviews_ratings r ON m.movie_id=r.movie_id
            LEFT JOIN movie_genre mg ON m.movie_id=mg.movie_id
            LEFT JOIN genres g ON mg.genre_id=g.genre_id
            WHERE m.movie_id=%s
            GROUP BY m.movie_id
        """, (series_id,))
        row = cursor.fetchone()
        if not row:
            imdb_heading(self.page, "Series not found!")
            return
        imdb_heading(self.page, row[0])
        imdb_subheading(self.page, f"Started: {row[1]} • {row[3] or ''}")
        ctk.CTkLabel(self.page, text=row[2] or "(No summary available)", wraplength=850, font=FONT_NORMAL, text_color="white", anchor="w", bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20)
        ctk.CTkLabel(self.page, text="Genres: " + (row[5] or ""), font=FONT_NORMAL, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20, pady=(6,0))
        ctk.CTkLabel(self.page, text="Avg Rating: " + (str(row[4]) if row[4] else "N/A"), font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20, pady=(0,12))

        # Episodes table grouped by season
        ctk.CTkLabel(self.page, text="Episodes:", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor="w", padx=20)
        ep_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        ep_frame.pack(fill='both', padx=20, pady=(6,12))
        cols = ("Season", "Episode", "Title", "Air Date")
        tree = ttk.Treeview(ep_frame, columns=cols, show="headings", height=18)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=180)
        self._style_treeview(tree, heading_font=("Arial", 11, "bold"), cell_font=("Arial", 10), rowheight=26)
        ep_scroll = ttk.Scrollbar(ep_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=ep_scroll.set)
        ep_scroll.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        cursor.execute("""
            SELECT season_number, episode_number, title, air_date
            FROM episodes
            WHERE movie_id=%s
            ORDER BY season_number, episode_number
        """, (series_id,))
        for i, er in enumerate(cursor.fetchall()):
            tag = 'even' if i % 2 == 0 else 'odd'
            tree.insert('', 'end', values=er, tags=(tag,))

        # Watchlist action for series (same behavior as movies)
        wf = ctk.CTkFrame(self.page)
        wf.pack(anchor='e', padx=20, pady=(12,12))
        def add_watchlist_series():
            if not self.current_user:
                messagebox.showerror('Auth', 'Login to add to watchlist')
                return
            try:
                self._ensure_watchlist_table()
                cursor.execute('INSERT INTO user_watchlist (user_id, movie_id) VALUES (%s,%s)', (self.current_user[0], series_id))
                conn.commit()
                messagebox.showinfo('Added', 'Added to your watchlist')
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        def remove_watchlist_series():
            if not self.current_user:
                messagebox.showerror('Auth', 'Login to remove from watchlist')
                return
            try:
                cursor.execute('DELETE FROM user_watchlist WHERE user_id=%s AND movie_id=%s', (self.current_user[0], series_id))
                conn.commit()
                messagebox.showinfo('Removed', 'Removed from your watchlist')
            except Exception as e:
                conn.rollback()
                messagebox.showerror('DB', f'Failed: {e}')

        ctk.CTkButton(wf, text='Add to Watchlist', fg_color=IMDB_YELLOW, command=add_watchlist_series, width=160).pack(side='left', padx=6)
        ctk.CTkButton(wf, text='Remove from Watchlist', fg_color=IMDB_YELLOW, command=remove_watchlist_series, width=200).pack(side='left', padx=6)

    def import_series_csv(self):
        """Import series/episodes from a CSV file.

        Expected CSV headers (flexible names accepted):
        - title or series_name (series title) [required]
        - season or season_number (int, default 1)
        - episode_number or episode (int) [recommended]
        - episode_title (title of the episode) [optional]
        - release_date (YYYY-MM-DD or YYYY) [optional]
        - language [optional]
        - description (series-level) [optional]
        - genres (comma/|/; separated) [optional]

        Each row represents a single episode. If the parent series (movie) doesn't exist it will be created.
        Episodes that already exist (same movie_id + season + episode_number) are skipped.
        """
        file_path = filedialog.askopenfilename(title="Select Series CSV file", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        inserted, skipped, failed = self.import_series_csv_from_path(file_path)
        messagebox.showinfo("Import Complete", f"Inserted episodes: {inserted}\nSkipped: {skipped}\nFailed: {failed}")

    def import_series_csv_from_path(self, file_path):
        """Helper to import a series CSV from a given file path. Returns (inserted, skipped, failed)."""
        inserted = 0
        skipped = 0
        failed = 0
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    series_title = (row.get('title') or row.get('series_name') or row.get('movie_name') or '').strip()
                    season_raw = (row.get('season') or row.get('season_number') or '').strip()
                    ep_raw = (row.get('episode') or row.get('episode_number') or '').strip()
                    ep_title = (row.get('episode_title') or row.get('ep_title') or '').strip()
                    release_date = (row.get('release_date') or row.get('episode_date') or row.get('date') or row.get('year') or '').strip()
                    language = (row.get('language') or '').strip()
                    description = (row.get('description') or row.get('summary') or '').strip()
                    genres_raw = (row.get('genres') or row.get('genre') or '').strip()

                    if not series_title:
                        skipped += 1
                        continue

                    # normalize season and episode numbers
                    try:
                        season = int(season_raw) if season_raw else 1
                    except:
                        season = 1
                    try:
                        episode_number = int(ep_raw) if ep_raw else None
                    except:
                        episode_number = None

                    # If year-only provided, convert to YYYY-01-01
                    if release_date and re.fullmatch(r"\d{4}$", release_date):
                        release_date = release_date + "-01-01"

                    try:
                        # ensure parent series exists as a movie row
                        cursor.execute("SELECT movie_id FROM movies WHERE movie_name=%s", (series_title,))
                        res = cursor.fetchone()
                        if res:
                            movie_id = res[0]
                        else:
                            cursor.execute("INSERT INTO movies (movie_name, release_date, language, description) VALUES (%s,%s,%s,%s)",
                                           (series_title, release_date or None, language or None, description or None))
                            movie_id = cursor.lastrowid

                        # skip if episode number exists
                        if episode_number is not None:
                            cursor.execute("SELECT episode_id FROM episodes WHERE movie_id=%s AND season_number=%s AND episode_number=%s",
                                           (movie_id, season, episode_number))
                            if cursor.fetchone():
                                skipped += 1
                                continue

                        # insert episode (DB schema uses columns: title, air_date, episode_number, season_number)
                        cursor.execute("INSERT INTO episodes (movie_id, episode_number, season_number, title, air_date) VALUES (%s,%s,%s,%s,%s)",
                                       (movie_id, episode_number, season, ep_title or None, release_date or None))

                        # handle genres at series level
                        if genres_raw:
                            parts = [p.strip() for p in re.split(r'[,|;]', genres_raw) if p.strip()]
                            for g in parts:
                                cursor.execute("SELECT genre_id FROM genres WHERE genre_name=%s", (g,))
                                gres = cursor.fetchone()
                                if gres:
                                    gid = gres[0]
                                else:
                                    cursor.execute("INSERT INTO genres (genre_name) VALUES (%s)", (g,))
                                    gid = cursor.lastrowid
                                try:
                                    cursor.execute("INSERT INTO movie_genre (movie_id, genre_id) VALUES (%s,%s)", (movie_id, gid))
                                except Exception:
                                    pass

                        inserted += 1
                    except Exception as e:
                        failed += 1
                        print("Error importing series row:", e)

            conn.commit()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import Series CSV: {e}")
            return (0, 0, 1)

        return (inserted, skipped, failed)

    def import_examples_series(self):
        """Import the two example CSVs present in the workspace and show a combined summary."""
        paths = [r"d:\\Coading\\comprehensive_tv_episodes_india_us_1975_2025.csv",
                 r"d:\\Coading\\streaming_series_episodes_netflix_prime_hbo_disney.csv"]
        total_inserted = total_skipped = total_failed = 0
        for p in paths:
            if not os.path.exists(p):
                messagebox.showwarning("File missing", f"File not found: {p}")
                continue
            ins, sk, fa = self.import_series_csv_from_path(p)
            total_inserted += ins
            total_skipped += sk
            total_failed += fa

        messagebox.showinfo("Example Import Complete", f"Inserted episodes: {total_inserted}\nSkipped: {total_skipped}\nFailed: {total_failed}")

    # ========== SEARCH ==========
    def show_search(self, initial_query=None, initial_cast=False):
        self.clear_page()
        imdb_heading(self.page, "Search Movies & Cast")
        imdb_subheading(self.page, "Advanced filtering available")
        search_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        search_frame.pack(anchor="w", padx=20, pady=9)

        # Basic search fields
        search_title = ctk.CTkEntry(search_frame, width=260, placeholder_text="Movie Title", font=FONT_NORMAL)
        search_title.grid(row=0, column=0, padx=6)
        search_genre = ctk.CTkEntry(search_frame, width=150, placeholder_text="Genre", font=FONT_NORMAL)
        search_genre.grid(row=0, column=1, padx=6)
        search_platform = ctk.CTkEntry(search_frame, width=160, placeholder_text="Platform", font=FONT_NORMAL)
        search_platform.grid(row=0, column=4, padx=6)
        search_year = ctk.CTkEntry(search_frame, width=110, placeholder_text="Year", font=FONT_NORMAL)
        search_year.grid(row=0, column=2, padx=6)
        search_cast = ctk.CTkEntry(search_frame, width=150, placeholder_text="Cast Name", font=FONT_NORMAL)
        search_cast.grid(row=0, column=3, padx=6)
        search_button = ctk.CTkButton(search_frame, text="Search", fg_color=IMDB_YELLOW, font=FONT_SUBHEADER, command=lambda: self._run_search(search_title.get(), search_genre.get(), search_year.get(), search_cast.get(), search_platform.get()))
        search_button.grid(row=0, column=5, padx=8)

        # Bind Enter to the search fields to perform the search
        for ent in (search_title, search_genre, search_year, search_cast, search_platform):
            ent.bind('<Return>', lambda e, st=search_title, sg=search_genre, sy=search_year, sc=search_cast, sp=search_platform: self._run_search(st.get(), sg.get(), sy.get(), sc.get(), sp.get()))

        # If `initial_query` provided (from header), pre-fill title and run search
        if initial_query:
            try:
                search_title.insert(0, initial_query)
                if initial_cast:
                    search_cast.insert(0, initial_query)
                self._run_search(search_title.get(), search_genre.get(), search_year.get(), search_cast.get(), search_platform.get())
            except Exception:
                pass

        self.search_results = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        self.search_results.pack(fill="both", padx=13, pady=8, expand=True)

    def _run_search(self, title, genre, year, cast, platform=None):
        # Clear prev
        for child in self.search_results.winfo_children():
            child.destroy()
        # Layout two columns: left for Cast results, right for Movies/TV
        container = ctk.CTkFrame(self.search_results, fg_color=IMDB_DARK_BG)
        container.pack(fill='both', expand=True)
        left = ctk.CTkFrame(container, fg_color=IMDB_DARK_BG)
        right = ctk.CTkFrame(container, fg_color=IMDB_DARK_BG)
        left.pack(side='left', fill='both', expand=True, padx=(12,6), pady=8)
        right.pack(side='right', fill='both', expand=True, padx=(6,12), pady=8)

        # Cast panel
        ctk.CTkLabel(left, text='Cast Results', font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor='w', padx=6, pady=(6,4))
        cast_tree = ttk.Treeview(left, columns=('Name','Age','Bio'), show='headings', height=18)
        for col in ('Name','Age','Bio'):
            cast_tree.heading(col, text=col)
            cast_tree.column(col, anchor='w', width=220)
        self._style_treeview(cast_tree, heading_font=("Arial",11,"bold"), cell_font=("Arial",10), rowheight=26)
        cast_scr = ttk.Scrollbar(left, orient='vertical', command=cast_tree.yview)
        cast_tree.configure(yscrollcommand=cast_scr.set)
        cast_scr.pack(side='right', fill='y')
        cast_tree.pack(fill='both', expand=True)
        # attach tooltip for bio column
        try:
            self._attach_treeview_tooltip(cast_tree, col_index=2, wrap=420)
        except Exception:
            pass

        # Movies/TV panel
        ctk.CTkLabel(right, text='Movies & TV Results', font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor='w', padx=6, pady=(6,4))
        movies_canvas = ctk.CTkFrame(right, fg_color=IMDB_DARK_BG)
        movies_canvas.pack(fill='both', expand=True)

        # If a cast name is provided, populate cast results
        if cast:
            query = "SELECT cast_id, name, dob, bio FROM cast_members WHERE name LIKE %s"
            params = [f"%{cast}%"]
            cursor.execute(query, params)
            for i, r in enumerate(cursor.fetchall()):
                age = self.calc_age(r[2]) if r[2] else ''
                tag = 'even' if i%2==0 else 'odd'
                cast_tree.insert('', 'end', values=(r[1], age, (r[3] or '')[:200]), tags=(tag,))

        # Always search movies/TV as well (use title/genre/year/platform filters)
        query = """
            SELECT m.movie_id, m.movie_name, YEAR(m.release_date) as yr, m.language,
                GROUP_CONCAT(DISTINCT g.genre_name) as genres,
                ROUND(AVG(r.rating),1) as avg_rating
            FROM movies m
            LEFT JOIN movie_genre mg ON m.movie_id=mg.movie_id
            LEFT JOIN genres g ON mg.genre_id=g.genre_id
            LEFT JOIN reviews_ratings r ON m.movie_id=r.movie_id
            LEFT JOIN movie_platform mp ON m.movie_id=mp.movie_id
            LEFT JOIN streaming_platforms sp ON mp.platform_id=sp.platform_id
            WHERE 1=1
        """
        params = []
        if title:
            query += " AND m.movie_name LIKE %s "
            params.append(f"%{title}%")
        if genre:
            query += " AND g.genre_name LIKE %s "
            params.append(f"%{genre}%")
        if year:
            query += " AND YEAR(m.release_date)=%s "
            params.append(year)
        if platform:
            query += " AND sp.platform_name LIKE %s "
            params.append(f"%{platform}%")
        query += " GROUP BY m.movie_id "
        cursor.execute(query, params)
        rows = cursor.fetchall()

        def render_movie_card(idx, r, parent):
            cid = r[0]
            title = r[1]
            year = r[2]
            lang = r[3]
            genres = r[4] or ''
            rating = r[5] or 'N/A'

            cols = 2
            padx = 12
            pady = 12
            card = ctk.CTkFrame(parent, fg_color=IMDB_GRAY, corner_radius=10, width=420, height=120)
            card.grid(row=idx//cols, column=idx%cols, padx=padx, pady=pady)
            ctk.CTkLabel(card, text=title, font=("Arial Black", 12), text_color=IMDB_YELLOW, wraplength=360).pack(anchor='w', padx=8)
            ctk.CTkLabel(card, text=f"{year} • {lang or ''}", font=FONT_NORMAL, text_color="white").pack(anchor='w', padx=8)
            ctk.CTkLabel(card, text=genres, font=("Arial", 10, "italic"), text_color="#cccccc", wraplength=360).pack(anchor='w', padx=8)
            btnframe = ctk.CTkFrame(card, fg_color=IMDB_GRAY)
            btnframe.pack(anchor='e', pady=(6,8), padx=8)
            ctk.CTkButton(btnframe, text="Details", fg_color=IMDB_YELLOW, command=lambda mid=cid: self.show_movie_detail(mid), width=100).pack(side='left', padx=6)
            ctk.CTkButton(btnframe, text="Add Watchlist", fg_color=IMDB_YELLOW, command=lambda mid=cid: self._add_to_watchlist(mid), width=120).pack(side='left', padx=6)

        render_next, has_more = self._create_scroll_batch(movies_canvas, movies_canvas, rows, render_movie_card, batch_size=8)

        controls = ctk.CTkFrame(right, fg_color=IMDB_DARK_BG)
        controls.pack(fill='x', pady=(6,12))
        load_btn = ctk.CTkButton(controls, text="Load more", fg_color=IMDB_YELLOW, width=140)
        load_btn.pack(anchor='center')

        def on_load_clicked():
            try:
                more = render_next()
                if not more:
                    load_btn.configure(state='disabled', text='All loaded')
            except Exception:
                load_btn.configure(state='disabled')

        load_btn.configure(command=on_load_clicked)
        try:
            if not has_more():
                load_btn.configure(state='disabled', text='All loaded')
        except Exception:
            pass

    def _add_to_watchlist(self, movie_id):
        if not self.current_user:
            messagebox.showerror('Auth','Login to add')
            return
        try:
            self._ensure_watchlist_table()
            cursor.execute('INSERT INTO user_watchlist (user_id, movie_id) VALUES (%s,%s)', (self.current_user[0], movie_id))
            conn.commit()
            messagebox.showinfo('Added','Movie added to your watchlist')
        except Exception as e:
            conn.rollback()
            messagebox.showerror('DB', f'Failed: {e}')

    def show_donations(self):
        """Display donations summary, top donors and a small form to add donations."""
        self.clear_page()
        imdb_heading(self.page, "Donations & Support")
        imdb_subheading(self.page, "Support CineTrack — view donors or add a donation")

        # Summary frame
        summary_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        summary_frame.pack(anchor="w", padx=20, pady=(8,6))

        cursor.execute("SELECT IFNULL(SUM(donation_amount),0) FROM donations")
        total = cursor.fetchone()[0] or 0.0
        total_label = ctk.CTkLabel(summary_frame, text=f"Total Donations: {total:.2f}", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG)
        total_label.pack(anchor='w')

        # Top donors
        donors_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        donors_frame.pack(fill='both', padx=20, pady=(6,12), expand=False)
        ctk.CTkLabel(donors_frame, text="Top Donors:", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).pack(anchor='w')

        cols = ("User", "Total", "Last Donation", "Comment")
        tree = ttk.Treeview(donors_frame, columns=cols, show="headings", height=8)
        for col in cols:
            tree.heading(col, text=col)
            # make Comment column wider
            if col == 'Comment':
                tree.column(col, anchor="w", width=420)
            else:
                tree.column(col, anchor="center", width=160)
        self._style_treeview(tree, heading_font=("Arial", 11, "bold"), cell_font=("Arial", 10), rowheight=26)
        donors_scroll = ttk.Scrollbar(donors_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=donors_scroll.set)
        donors_scroll.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, pady=(6,0))

        # Fetch total, latest donation date, and the most recent non-null comment for each user
        cursor.execute(
            """
            SELECT u.username,
                   IFNULL(SUM(d.donation_amount),0) AS total,
                   MAX(d.donation_date) AS last_date,
                   (
                       SELECT d2.comment
                       FROM donations d2
                       WHERE d2.user_id = u.user_id AND d2.comment IS NOT NULL
                       ORDER BY d2.donation_date DESC
                       LIMIT 1
                   ) AS recent_comment
            FROM donations d
            JOIN users u ON d.user_id = u.user_id
            GROUP BY u.user_id
            ORDER BY total DESC
            LIMIT 50
            """
        )
        rows = cursor.fetchall()
        for i, r in enumerate(rows):
            tag = 'even' if i % 2 == 0 else 'odd'
            recent_comment = r[3] or ''
            tree.insert('', 'end', values=(r[0], f"{r[1]:.2f}", r[2], recent_comment), tags=(tag,))

        # Donation form
        form_frame = ctk.CTkFrame(self.page, fg_color=IMDB_DARK_BG)
        form_frame.pack(anchor='w', padx=20, pady=(8,12))
        ctk.CTkLabel(form_frame, text="Add Donation", font=FONT_SUBHEADER, text_color=IMDB_YELLOW, bg_color=IMDB_DARK_BG).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0,6))

        # Username selector (combobox) - list all usernames
        cursor.execute("SELECT username FROM users ORDER BY username")
        users = [r[0] for r in cursor.fetchall()]
        ttk.Label(form_frame, text="User:").grid(row=1, column=0, sticky='w', padx=(0,6))
        username_cb = ttk.Combobox(form_frame, values=users, width=30)
        username_cb.grid(row=1, column=1, sticky='w', padx=(0,6))
        # If a user is logged in, auto-select them and disable the combobox so
        # donations are always performed as the authenticated user.
        if self.current_user:
            try:
                username_cb.set(self.current_user[1])
                username_cb.configure(state='disabled')
            except Exception:
                pass

        # Amount entry
        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, sticky='w', padx=(0,6), pady=(6,0))
        amount_entry = ctk.CTkEntry(form_frame, width=180, placeholder_text="0.00", font=FONT_NORMAL)
        amount_entry.grid(row=2, column=1, sticky='w', padx=(0,6), pady=(6,0))

        # Comment entry
        ttk.Label(form_frame, text="Comment:").grid(row=3, column=0, sticky='w', padx=(0,6), pady=(6,0))
        comment_entry = ctk.CTkEntry(form_frame, width=420, placeholder_text="Optional message", font=FONT_NORMAL)
        comment_entry.grid(row=3, column=1, columnspan=2, sticky='w', pady=(6,0))

        donate_btn = ctk.CTkButton(form_frame, text="Donate", fg_color=IMDB_YELLOW, width=140)
        donate_btn.grid(row=4, column=0, columnspan=2, pady=(10,0))

        def submit_donation():
            # Donation must be from a logged-in user
            if not self.current_user:
                messagebox.showerror('Auth', 'Please login to make a donation.')
                return
            amt_text = amount_entry.get().strip()
            comment = comment_entry.get().strip() or None
            if not amt_text:
                messagebox.showerror("Input Error", "Please enter an amount.")
                return
            try:
                amt = float(amt_text)
                if amt <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror("Input Error", "Enter a valid positive amount.")
                return
            uid = self.current_user[0]

            try:
                cursor.execute("INSERT INTO donations (user_id, donation_amount, comment) VALUES (%s,%s,%s)", (uid, amt, comment))
                conn.commit()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("DB Error", f"Failed to save donation: {e}")
                return

            messagebox.showinfo("Thank you!", "Donation recorded successfully.")

            # refresh totals and donor list
            cursor.execute("SELECT IFNULL(SUM(donation_amount),0) FROM donations")
            new_total = cursor.fetchone()[0] or 0.0
            total_label.configure(text=f"Total Donations: {new_total:.2f}")

            for iid in tree.get_children():
                tree.delete(iid)
            cursor.execute(
                """
                SELECT u.username, IFNULL(SUM(d.donation_amount),0) AS total, MAX(d.donation_date)
                FROM donations d
                JOIN users u ON d.user_id = u.user_id
                GROUP BY u.user_id
                ORDER BY total DESC
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
            for i, r in enumerate(rows):
                tag = 'even' if i % 2 == 0 else 'odd'
                tree.insert('', 'end', values=(r[0], f"{r[1]:.2f}", r[2]), tags=(tag,))

            amount_entry.delete(0, 'end')
            comment_entry.delete(0, 'end')

        donate_btn.configure(command=submit_donation)

    def on_closing(self):
        cursor.close()
        conn.close()
        self.destroy()

if __name__ == "__main__":
    app = CineTrackIMDB()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
