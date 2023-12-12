"""This is an example python file"""


class ExampleClass:
    def __init__(self, arg, *args, **kwargs):
        """First doc str

        :parameter arg: Arg
        :type kwargs: dict
        :param args: Args
        :param kwargs: Kwargs but with a really long description that will need to be
            rewrapped because it is really long and won't fit in the default 88
            characters.
        :returns: Returns
        :type args: list

        :var arg: Arg
        :vartype arg: str

        """
