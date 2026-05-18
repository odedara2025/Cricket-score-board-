import sqlite3
import os
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu

from kivymd.uix.appbar import MDTopAppBar

# KV डिज़ाइन
KV = '''
ScreenManager:
    id: sm
    Screen:
        name: 'setup'
        BoxLayout:
            orientation: 'vertical'
            padding: 20
            spacing: 15
            MDLabel:
                text: '🏏 मैच सेटअप'
                halign: 'center'
                font_style: 'H4'
            MDTextField:
                id: host
                hint_text: 'मेज़बान टीम का नाम'
            MDTextField:
                id: opponent
                hint_text: 'विरोधी टीम का नाम'
            MDTextField:
                id: overs
                hint_text: 'कुल ओवर'
                input_filter: 'int'
            MDTextField:
                id: toss_winner
                hint_text: 'टॉस विनर का नाम'
            MDTextField:
                id: toss_decision
                hint_text: 'बल्लेबाजी / क्षेत्ररक्षण'
                on_focus: if self.focus: app.show_toss_menu(self)
            MDRaisedButton:
                text: 'अगला कदम →'
                on_release: app.save_match_setup()
    Screen:
        name: 'players'
        BoxLayout:
            orientation: 'vertical'
            padding: 20
            spacing: 15
            MDLabel:
                text: '👥 पहली पारी के खिलाड़ी'
            MDTextField:
                id: striker
                hint_text: 'स्ट्राइकर का नाम'
            MDTextField:
                id: non_striker
                hint_text: 'नॉन-स्ट्राइकर का नाम'
            MDTextField:
                id: bowler
                hint_text: 'वर्तमान गेंदबाज'
            MDRaisedButton:
                text: 'स्कोरबोर्ड शुरू करें'
                on_release: app.start_innings()
    Screen:
        name: 'scoreboard'
        BoxLayout:
            orientation: 'vertical'
            MDToolbar:
                title: '📊 लाइव स्कोर'
                elevation: 5
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: 15
                    spacing: 10
                    MDLabel:
                        id: match_label
                        text: ''
                    MDLabel:
                        id: total_score
                        text: '0/0'
                        font_style: 'H2'
                    MDLabel:
                        id: overs_runrate
                        text: 'ओवर: 0.0   रन रेट: 0.0'
                    MDLabel:
                        id: target_label
                        text: ''
                    MDLabel:
                        id: striker_info
                        text: 'स्ट्राइकर: -- (0 रन, 0 गेंद)'
                    MDLabel:
                        id: non_striker_info
                        text: 'नॉन-स्ट्राइकर: -- (0 रन, 0 गेंद)'
                    MDLabel:
                        id: bowler_info
                        text: 'गेंदबाज: -- (0.0-0-0)'
                    GridLayout:
                        cols: 4
                        spacing: 8
                        size_hint_y: None
                        height: 200
                        MDRaisedButton:
                            text: '0'
                            on_release: app.add_runs(0)
                        MDRaisedButton:
                            text: '1'
                            on_release: app.add_runs(1)
                        MDRaisedButton:
                            text: '2'
                            on_release: app.add_runs(2)
                        MDRaisedButton:
                            text: '3'
                            on_release: app.add_runs(3)
                        MDRaisedButton:
                            text: '4'
                            on_release: app.add_runs(4)
                        MDRaisedButton:
                            text: '6'
                            on_release: app.add_runs(6)
                        MDRaisedButton:
                            text: 'वाइड'
                            md_bg_color: 1, 0.8, 0, 1
                            on_release: app.wide_ball()
                        MDRaisedButton:
                            text: 'नो बॉल'
                            md_bg_color: 1, 0.5, 0, 1
                            on_release: app.no_ball()
                        MDRaisedButton:
                            text: 'विकेट'
                            md_bg_color: 1, 0, 0, 1
                            on_release: app.wicket_fall()
'''

class CricketScoreboardApp(MDApp):
    # प्रॉपर्टीज
    match_id = None
    innings = 1
    target = 0
    runs = 0
    wickets = 0
    balls = 0  # 0 से 5
    overs_done = 0
    total_overs = 0
    striker = ''
    non_striker = ''
    bowler = ''
    striker_runs = 0
    striker_balls = 0
    non_striker_runs = 0
    non_striker_balls = 0
    bowler_runs = 0
    bowler_wickets = 0
    bowler_overs = 0
    bowler_balls_in_over = 0
    host = ''
    opponent = ''
    toss_winner = ''
    toss_decision = ''

    def build(self):
        self.sm = Builder.load_string(KV)
        self.init_db()
        return self.sm

    def init_db(self):
        """SQLite डेटाबेस और टेबल बनाएँ"""
        self.conn = sqlite3.connect('cricket.db')
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_team TEXT,
                opponent_team TEXT,
                total_overs INTEGER,
                toss_winner TEXT,
                toss_decision TEXT,
                target INTEGER,
                match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                player_name TEXT,
                runs INTEGER DEFAULT 0,
                balls INTEGER DEFAULT 0,
                wickets INTEGER DEFAULT 0,
                runs_conceded INTEGER DEFAULT 0,
                overs_bowled REAL DEFAULT 0,
                is_batsman BOOLEAN,
                is_bowler BOOLEAN
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ball_by_ball (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                over_no INTEGER,
                ball_no INTEGER,
                runs INTEGER,
                is_wide BOOLEAN,
                is_noball BOOLEAN,
                is_wicket BOOLEAN,
                striker TEXT,
                bowler TEXT
            )
        ''')
        self.conn.commit()

    def show_toss_menu(self, textfield):
        menu_items = [
            {"text": "बल्लेबाजी", "viewclass": "OneLineListItem", "on_release": lambda x="Batting": self.set_toss_decision(textfield, x)},
            {"text": "क्षेत्ररक्षण", "viewclass": "OneLineListItem", "on_release": lambda x="Fielding": self.set_toss_decision(textfield, x)}
        ]
        self.menu = MDDropdownMenu(caller=textfield, items=menu_items, width_mult=4)
        self.menu.open()

    def set_toss_decision(self, textfield, decision):
        textfield.text = decision
        self.menu.dismiss()

    def save_match_setup(self):
        screen = self.sm.get_screen('setup')
        self.host = screen.ids.host.text
        self.opponent = screen.ids.opponent.text
        self.total_overs = int(screen.ids.overs.text)
        self.toss_winner = screen.ids.toss_winner.text
        self.toss_decision = screen.ids.toss_decision.text

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO matches (host_team, opponent_team, total_overs, toss_winner, toss_decision) VALUES (?, ?, ?, ?, ?)",
            (self.host, self.opponent, self.total_overs, self.toss_winner, self.toss_decision)
        )
        self.conn.commit()
        self.match_id = cursor.lastrowid
        self.sm.current = 'players'

    def start_innings(self):
        screen = self.sm.get_screen('players')
        self.striker = screen.ids.striker.text
        self.non_striker = screen.ids.non_striker.text
        self.bowler = screen.ids.bowler.text

        score_screen = self.sm.get_screen('scoreboard')
        score_screen.ids.match_label.text = f"{self.host} vs {self.opponent}"
        if self.innings == 2:
            score_screen.ids.target_label.text = f"लक्ष्य: {self.target} रन"
        else:
            score_screen.ids.target_label.text = ""
        self.update_scoreboard_ui()
        self.sm.current = 'scoreboard'

    def add_runs(self, runs):
        self.runs += runs
        if runs % 2 == 1:
            self.striker_runs += runs
            self.striker_balls += 1
            self.rotate_strike()
        else:
            self.striker_runs += runs
            self.striker_balls += 1
        self.bowler_runs += runs
        self.bowler_balls_in_over += 1
        self.balls += 1
        self.check_over()
        self.update_scoreboard_ui()
        self.save_ball_to_db(runs, False, False, False)

    def wide_ball(self):
        self.runs += 1
        self.bowler_runs += 1
        self.update_scoreboard_ui()
        self.save_ball_to_db(1, True, False, False)

    def no_ball(self):
        self.runs += 1
        self.bowler_runs += 1
        self.striker_balls += 1
        self.striker_runs += 1
        self.bowler_balls_in_over += 1
        self.balls += 1
        self.check_over()
        self.update_scoreboard_ui()
        self.save_ball_to_db(1, False, True, False)

    def wicket_fall(self):
        self.wickets += 1
        self.bowler_wickets += 1
        self.bowler_balls_in_over += 1
        self.balls += 1
        self.check_over()
        # नए बल्लेबाज का पॉपअप
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        name_input = MDTextField(hint_text="नया बल्लेबाज")
        content.add_widget(name_input)
        dialog = MDDialog(
            title="विकेट गिरा",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="रद्द", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="जोड़ें", on_release=lambda x: self.add_new_batsman(name_input.text, dialog))
            ]
        )
        dialog.open()
        self.save_ball_to_db(0, False, False, True)

    def add_new_batsman(self, name, dialog):
        if name:
            self.striker = name
            self.striker_runs = 0
            self.striker_balls = 0
            dialog.dismiss()
            self.update_scoreboard_ui()
        else:
            # त्रुटि दिखाएँ
            pass

    def rotate_strike(self):
        self.striker, self.non_striker = self.non_striker, self.striker
        self.striker_runs, self.non_striker_runs = self.non_striker_runs, self.striker_runs
        self.striker_balls, self.non_striker_balls = self.non_striker_balls, self.striker_balls

    def check_over(self):
        if self.bowler_balls_in_over == 6:
            self.overs_done += 1
            self.balls = 0
            self.bowler_overs += 1
            self.bowler_balls_in_over = 0
            self.rotate_strike()  # ओवर खत्म होने पर स्ट्राइक बदलें
            # नए गेंदबाज का पॉपअप
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            name_input = MDTextField(hint_text="नया गेंदबाज")
            content.add_widget(name_input)
            dialog = MDDialog(
                title="ओवर समाप्त",
                type="custom",
                content_cls=content,
                buttons=[
                    MDRaisedButton(text="रद्द", on_release=lambda x: dialog.dismiss()),
                    MDRaisedButton(text="सेट करें", on_release=lambda x: self.change_bowler(name_input.text, dialog))
                ]
            )
            dialog.open()

    def change_bowler(self, name, dialog):
        if name:
            self.bowler = name
            self.bowler_runs = 0
            self.bowler_wickets = 0
            self.bowler_balls_in_over = 0
            dialog.dismiss()
            self.update_scoreboard_ui()

    def update_scoreboard_ui(self):
        screen = self.sm.get_screen('scoreboard')
        overs_display = self.overs_done + (self.balls / 10.0)
        total_overs_bowled = self.overs_done + (self.balls / 6.0)
        run_rate = self.runs / total_overs_bowled if total_overs_bowled > 0 else 0
        screen.ids.total_score.text = f"{self.runs}/{self.wickets}"
        screen.ids.overs_runrate.text = f"ओवर: {overs_display:.1f}   रन रेट: {run_rate:.2f}"
        screen.ids.striker_info.text = f"स्ट्राइकर: {self.striker} ({self.striker_runs} रन, {self.striker_balls} गेंद)"
        screen.ids.non_striker_info.text = f"नॉन-स्ट्राइकर: {self.non_striker} ({self.non_striker_runs} रन, {self.non_striker_balls} गेंद)"
        bowler_over_display = self.bowler_overs + (self.bowler_balls_in_over / 10.0)
        screen.ids.bowler_info.text = f"गेंदबाज: {self.bowler} ({bowler_over_display:.1f}-{self.bowler_runs}-{self.bowler_wickets})"
        if self.innings == 2:
            target_needed = self.target - self.runs
            screen.ids.target_label.text = f"लक्ष्य: {self.target} रन, और चाहिए {target_needed} रन"

    def save_ball_to_db(self, runs, is_wide, is_noball, is_wicket):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO ball_by_ball (match_id, over_no, ball_no, runs, is_wide, is_noball, is_wicket, striker, bowler) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (self.match_id, self.overs_done, self.balls, runs, is_wide, is_noball, is_wicket, self.striker, self.bowler)
        )
        self.conn.commit()

        # जाँचें कि पारी खत्म हुई या नहीं
        if self.wickets >= 10 or (self.overs_done >= self.total_overs and self.balls == 0):
            self.end_innings()

    def end_innings(self):
        if self.innings == 1:
            self.target = self.runs + 1
            # पहली पारी के आँकड़े सेव करें
            self.save_player_stats()
            # डेटाबेस में टारगेट अपडेट करें
            cursor = self.conn.cursor()
            cursor.execute("UPDATE matches SET target = ? WHERE id = ?", (self.target, self.match_id))
            self.conn.commit()
            # दूसरी पारी के लिए रीसेट
            self.innings = 2
            self.runs = 0
            self.wickets = 0
            self.balls = 0
            self.overs_done = 0
            self.striker_runs = 0
            self.striker_balls = 0
            self.non_striker_runs = 0
            self.non_striker_balls = 0
            self.bowler_runs = 0
            self.bowler_wickets = 0
            self.bowler_overs = 0
            self.bowler_balls_in_over = 0
            # दूसरी पारी के लिए प्लेयर इनपुट दिखाएँ
            self.sm.current = 'players'
        else:
            # मैच समाप्त
            self.save_player_stats()
            self.show_match_result()

    def save_player_stats(self):
        cursor = self.conn.cursor()
        # स्ट्राइकर
        cursor.execute("INSERT INTO player_stats (match_id, player_name, runs, balls, is_batsman, is_bowler) VALUES (?, ?, ?, ?, ?, ?)",
                       (self.match_id, self.striker, self.striker_runs, self.striker_balls, True, False))
        # नॉन-स्ट्राइकर
        cursor.execute("INSERT INTO player_stats (match_id, player_name, runs, balls, is_batsman, is_bowler) VALUES (?, ?, ?, ?, ?, ?)",
                       (self.match_id, self.non_striker, self.non_striker_runs, self.non_striker_balls, True, False))
        # गेंदबाज
        overs_bowled = self.bowler_overs + (self.bowler_balls_in_over / 6.0)
        cursor.execute("INSERT INTO player_stats (match_id, player_name, wickets, runs_conceded, overs_bowled, is_batsman, is_bowler) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (self.match_id, self.bowler, self.bowler_wickets, self.bowler_runs, overs_bowled, False, True))
        self.conn.commit()

    def show_match_result(self):
        winner = self.host if self.runs > self.target else self.opponent
        dialog = MDDialog(
            title="🏆 मैच समाप्त",
            text=f"विजेता: {winner}\n{self.runs}/{self.wickets}\nलक्ष्य: {self.target}",
            buttons=[MDRaisedButton(text="बंद करें", on_release=lambda x: self.stop())]
        )
        dialog.open()

    def on_stop(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == '__main__':
    CricketScoreboardApp().run()