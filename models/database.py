from titles import Titles

class Database:
    def __init__(self):
        self.titles = {}
        self._last_title_key = 0


    def add_title(self, title):
        self._last_title_key += 1
        self.titles[self._last_title_key] = title
        return self._last_title_key
    
    def del_title(self, title_key):
        if title_key in self.titles:
            del self.titles[title_key]

    def get_title(self, title_key):
        if title_key in self.titles:
            return self.titles[title_key]
        else:
            print("title not found in database.")


    def get_titles(self):
        titles = []
        for title_id, title in self.titles.items():
            title_= Titles(title.title_id, title.primary_title, title.original_title, title.is_adult, title.start_year, title.end_year, title.runtime_mins, title.genres)
            titles.append((title_id, title_))

        return titles