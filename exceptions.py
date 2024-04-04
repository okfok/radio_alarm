class RadioAlarmException(Exception):
    def __str__(self):
        return f'{self.__class__.__name__} {" ".join(self.args)}'


class TriggerException(RadioAlarmException):
    pass


class AlertTypeNotConfiguredException(TriggerException):
    pass


class OutOfTimeTableException(TriggerException):
    pass


class WinWindowNotFoundException(TriggerException):
    pass
