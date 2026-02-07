import sys

class Channel:
    
    def __init__(self, name):
        self.name = name



    def get_name(self):
        return self.name



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
