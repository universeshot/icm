"""
Module docstring: brief description of the module's purpose.

This file defines the MyClass class and related functionalities.
"""

# Standard library imports
import sys

# Third-party imports
# import third_party_module

# Local application/library specific imports
# from my_package.other_module import helper_function

class Breaker:
    """
    Class docstring: brief summary of the class's purpose and behavior.

    This class serves as a template with a constructor, methods, and attributes.
    Follows [PEP 8](https://realpython.com/python-pep8/) conventions for naming.
    """
    
    def __init__(self, attribute_one: str, attribute_two: int):
        """
        Constructor method to initialize instance attributes.

        Args:
            attribute_one: A string description for the first attribute.
            attribute_two: An integer value for the second attribute.
        """
        self.attribute_one = attribute_one
        self.attribute_two = attribute_two

    def example_method(self, optional_param: bool = False) -> str:
        """
        An example instance method.

        Args:
            optional_param: An optional boolean parameter (default False).

        Returns:
            A string based on the class attributes and parameters.
        """
        if optional_param:
            return f"Option enabled: {self.attribute_one}"
        return f"Option disabled: {self.attribute_two}"

    @classmethod
    def create_default(cls):
        """
        A class method to create a default instance.
        """
        return cls("Default", 0)

def main():
    """
    Main function to demonstrate class usage.
    """
    # Create an instance of the class
    instance = MyClass.create_default()
    print(f"Created a default instance: {instance.attribute_one}, {instance.attribute_two}")
    
    # Use an instance method
    result = instance.example_method(optional_param=True)
    print(f"Method result: {result}")

if __name__ == "__main__":
    # Entry point of the script
    main()
