import json

DEFAULT_CFG_FILE = {
    'region_id': 1,
    'source_files': {

    },
    'destination_folder': '',
    'check_interval': 10,
    'timetable': {
        'Monday': [
            ('00:00', '08:00'),
            ('20:00', '24:00')
        ]
    }
}


class File(dict):
    def __init__(self, file_name: str, data: dict = None):
        self.file_name = file_name
        if data is None:
            with open(self.file_name, 'r') as fl:
                super().__init__(json.loads(fl.read()))
        else:
            super().__init__(data)

    def __del__(self):
        with open(self.file_name, 'w') as fl:
            fl.write(json.dumps(self))


class CFGFile(File):
    def __init__(self, file_name: str = 'conf.json'):
        try:
            super().__init__(file_name)
        except FileNotFoundError:
            super().__init__(file_name, DEFAULT_CFG_FILE)


cfg = CFGFile()
del cfg
