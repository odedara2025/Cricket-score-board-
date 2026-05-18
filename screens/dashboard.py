from kivy.uix.screenmanager import Screen


class DashboardScreen(Screen):

    def create_tournament(self):
        print('Create Tournament Screen')

    def create_team(self):
        print('Create Team Screen')

    def start_match(self):
        print('Start Match Screen')