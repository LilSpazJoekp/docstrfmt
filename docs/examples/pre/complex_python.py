"""This is a module docstring that will be formatted by docstrfmt.

This module provides data processing capabilities with support for various
data types and processing methods. It includes performance optimizations
and comprehensive error handling.

.. versionadded:: 1.0.0
.. versionchanged:: 1.1.0
   Added support for custom processing methods

.. note::
   This module requires Python 3.8 or higher.

.. warning::
   Large datasets may require significant memory usage.

.. seealso::
   :class:`DataProcessor` for the main processing class
   :func:`process_data` for a standalone processing function

.. todo::
   Add support for parallel processing
   Implement data validation
"""


class DataProcessor:
    """A class for processing data with various methods.

    This class provides a flexible interface for processing different types
    of data structures. It supports multiple processing algorithms and
    includes built-in error handling and validation.

    .. versionadded:: 1.0.0

    Attributes
    ----------
    data : list or dict
        The data to be processed
    processed_count : int
        Number of items processed (read-only)

    Examples
    --------
    Basic usage::

        processor = DataProcessor([1, 2, 3])
        result = processor.process("sort")
        print(result)  # [1, 2, 3]

    With custom data::

        processor = DataProcessor({"a": 1, "b": 2})
        result = processor.process("reverse")
        print(result)  # {"b": 2, "a": 1}

    .. note::
       The processor automatically validates input data types.

    .. warning::
       Processing large datasets may take significant time.
    """

    def __init__(self, data):
        """Initialize the DataProcessor with data.

        :param data: The data to process
        :type data: list or dict
        :raises ValueError: If data is not a list or dict
        :raises TypeError: If data is None

        Examples
        --------
        >>> processor = DataProcessor([1, 2, 3])
        >>> processor.data
        [1, 2, 3]

        >>> processor = DataProcessor({"key": "value"})
        >>> processor.data
        {"key": "value"}
        """
        self.data = data
        self.processed_count = 0

    def process(self, method="default"):
        """Process the data using the specified method.

        This method applies the specified processing algorithm to the data
        and returns the result. The method supports various algorithms
        including sorting, reversing, and custom transformations.

        :param method: The processing method to use
        :type method: str
        :returns: The processed data
        :rtype: list or dict
        :raises ValueError: If method is not supported
        :raises TypeError: If data cannot be processed

        Supported Methods
        -----------------
        - "default": Returns data unchanged
        - "sort": Sorts the data (for lists)
        - "reverse": Reverses the data order
        - "unique": Removes duplicates (for lists)

        Examples
        --------
        Basic processing::

            processor = DataProcessor([3, 1, 2])
            result = processor.process("sort")
            print(result)  # [1, 2, 3]

        With error handling::

            try:
                result = processor.process("invalid")
            except ValueError as e:
                print(f"Error: {e}")

        .. note::
           The original data is not modified during processing.

        .. warning::
           Some methods may not work with all data types.
        """
        if method == "default":
            result = self.data
        elif method == "sort":
            if isinstance(self.data, list):
                result = sorted(self.data)
            else:
                raise TypeError("Sort method only works with lists")
        elif method == "reverse":
            if isinstance(self.data, list):
                result = list(reversed(self.data))
            elif isinstance(self.data, dict):
                result = dict(reversed(list(self.data.items())))
            else:
                raise TypeError("Reverse method requires list or dict")
        elif method == "unique":
            if isinstance(self.data, list):
                result = list(dict.fromkeys(self.data))
            else:
                raise TypeError("Unique method only works with lists")
        else:
            raise ValueError(f"Unknown method: {method}")

        self.processed_count += 1
        return result
