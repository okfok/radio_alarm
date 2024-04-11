class RadioAlarmException(Exception):
    def __str__(self):
        return f'{self.__class__.__name__} {" ".join(self.args)}'


class EventActionException(RadioAlarmException):
    pass


class AlertTypeNotConfiguredException(EventActionException):
    pass


class OutOfTimeTableException(EventActionException):
    pass


class WinWindowNotFoundException(EventActionException):
    pass
