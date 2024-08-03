"""This is an example python file"""

test = "value"


class ExampleClass:
    """Class docstring example

    Test table

    ===== ================ ======================================================================================================
    A     B                A or B
    ===== ================ ======================================================================================================
    False False            False
    True  False            True
    False True             True
    True      True         has note block

          This has a list: .. note::

          - list item 1        Note
          - list item 2
          - list item 3
          - list item 4
    True                   .. code-block:: python

                               print(
                                   "This code block is really long and won't be able to be wrapped in the default 88 characters."
                               )
    ===== ================ ======================================================================================================

    """

    def __init__(self, *args, **kwargs):
        """First doc str"""

        self.test = "value"
        """Test attr docstring

        .. thisdirectivedoesnotexit:: arguments but with white space
            :field1: value1
            :field2: value2
            :field3:

            some
                text
                    that
                        shouldn't change

        This is an unknown role :lolno:`dolphin` but it's okay.

        .. code-block:: python

            print("Hello world")

        ..

        """

        self.test2 = "value"
        r"""Duis :func:`elementum`\ s ac |subs|__ ex, nec |ultrices| est vestibulum__.

        .. |subs| replace:: ``SUBS``

        .. |ultrices| replace:: Really long text that needs wrapped. Duis vel nulla ac
            risus semper fringilla vel non mauris. In elementum viverra arcu sed
            commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper eros
            ac gravida.

        """

    def method(self, attr1, attr2):
        """Test method docstring.

        :param str attr1: attr1 description.
        :param str attr2: attr2 description.

        :returns: This returns something.
        :rtype: str

        :raises ValueError: This raises a ValueError.

        :var attr1: attr1 description.

        :standard_field: Standard field

        """

    def method2(self, attr1, attr2):
        r"""Test method docstring summary that is really really really really really really really long.

        Test method docstring description that is really really really really really
        really really long.

            :standard_field: Standard field

        :param str attr1: attr1 description.
        :param str attr2: Test method docstring description that is really really really
            really really really really long.

            :standard_field: Standard field, but nested

        :returns: This returns something.
        :rtype: str

        :raises ValueError: This raises a ValueError.

        """
        my_position, im_active = 1, True
        match my_position, im_active:
            case [1, True]:
                print("Hello world")
