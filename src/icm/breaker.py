import sys
from router import Router

class Breaker:
    
    def __init__(self, attribute_one: str, attribute_two: int):
        self.attribute_one = attribute_one
        self.attribute_two = attribute_two
        self.router = None

    def example_method(self, optional_param: bool = False) -> str:
        if optional_param:
            return f"Option enabled: {self.attribute_one}"
        return f"Option disabled: {self.attribute_two}"

    @classmethod
    def create_default(cls):
        """
        A class method to create a default instance.
        """
        return cls("Default", 0)

    @staticmethod
    def disperse(input, txn_mux, target: Router):
        return ""

    @staticmethod
    def reassemble(input, in_mux, out_mux, target: Router):
        return ""
    

def main():
    """
    Main function to demonstrate class usage.
    """
    # Create an instance of the class
    instance = Breaker.create_default()
    print(f"Created a default instance: {instance.attribute_one}, {instance.attribute_two}")

    instance.route("new router")
    
    # Use an instance method
    result = instance.example_method(optional_param=True)
    print(f"Method result: {result}")

    instance.check_router()

if __name__ == "__main__":
    # Entry point of the script
    main()
