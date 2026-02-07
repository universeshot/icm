import sys
from channel import Channel

class Mux:
    
    def __init__(self):
        self.channels = {}

    def register(self, channel: Channel):
        self.channels[channel.get_name()] = channel

    def check(self):
        print(f"Channels are: {self.channels}")
    

def main():
    """
    Main function to demonstrate class usage.
    """
    # Create an instance of the class
    instance = Mux()
    
    instance.register(Channel("a"))
    
    instance.check()

if __name__ == "__main__":
    # Entry point of the script
    main()
