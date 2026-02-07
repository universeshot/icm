
class TranslationUnit:
    
    def __init__(self):
        self.txn = {}
        self.r_txn = {}
        self.units = [self]

    def set(self, txn):
        self.txn = txn
        self.r_txn = {value: key for key, value in txn.items()}
    
    @staticmethod
    def _find_ultimate_val(units, input):
        ultimate_val = input
        
        for unit in units:
            if ultimate_val in unit:
                ultimate_val = unit[ultimate_val]
        
        # print(f"input={input}; found={ultimate_val}")
        return ultimate_val

    def drive(self, input):
        return TranslationUnit._find_ultimate_val([unit.txn for unit in self.units], input)

    def reverse(self, input):
        return TranslationUnit._find_ultimate_val([unit.r_txn for unit in reversed(self.units)], input)

    def attach(self, txn_unit: TranslationUnit):
        self.units.append(txn_unit)

    def detach(self, unit: TranslationUnit):
        if unit in self.units:
            print("handle remove")

    @staticmethod
    def combine(txn_units):
        new_unit = TranslationUnit()
        for unit in txn_units:
            new_unit.add(unit)
        
        return new_unit

    def show_chains(self):
        trees = []

        for unit in self.units:
            for key, value in unit.txn.items():
                value_added = False

                for tree in trees:
                    if key == tree[-1] and not value_added:
                        tree.append(value)
                        value_added = True
                
                if not value_added:
                    trees += [[key, value]]
        
        print("\n/// chains\n")

        i = 0
        for tree in trees:
            print(f"{i}: {tree}")
            i += 1

        print("\n\\\\\ chains\n")

def main():
    insta = TranslationUnit()
    print("/// insta")
    print(insta.drive("hello"))
    print(insta.reverse("hello"))

    insta.set({"hello": "greetings", "goodbye": "farewell"})

    print(insta.drive("hello"))
    print(insta.drive("goodbye"))

    print("/// insta backwards")
    print(insta.reverse("greetings"))

    insta.show_chains()

    instb = TranslationUnit()
    print("--- Handling instb")
    print(instb.drive("hello"))
    print(instb.reverse("hello"))

    instb.set({"greetings": "good day", "good day": "hi"})

    print(instb.drive("hello"))
    print(instb.drive("greetings"))

    print("--- Testing backwards")
    print(instb.reverse("good day"))

    insta.attach(instb)

    print("--- Handling insta joined instb")
    print(insta.drive("hello"))
    print(instb.drive("hello"))

    print("--- Testing backwards")
    print(insta.reverse("greetings"))
    print(insta.reverse("good day"))

    
    insta.show_chains()


if __name__ == "__main__":
    # Entry point of the script
    main()
