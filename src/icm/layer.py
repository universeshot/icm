import sys
from channel import Channel

class Layer:
    
    def __init__(self):
        self.contents = set({})

    def add(self, *items: str):
        for i in items:
            self.contents.add(i)

    def remove(self, *items: str):
        for i in items:
            self.contents.discard(i)

    def check(self):
        print(f"Layer contents: {self.contents}")
    

def main():
    instance = Layer()
    instance.add("a", "b")

    instance.add("c", "d")
    
    print("Checking after adding all")
    instance.check()

    instance.remove("b", "c")

    print("Checking after partial removal")
    instance.check()

if __name__ == "__main__":
    main()
