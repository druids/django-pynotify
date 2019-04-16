class BaseDispatcher:
    """
    Base class for sending notification over a communication channel (e.g. e-mail, sms, push).
    """
    def dispatch(self, notification):
        """
        This method should implement actual sending of ``notification``.
        """
        raise NotImplementedError()  # pragma: no cover
