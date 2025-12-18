from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

class Dog(Animal):
    def make_sound(self):
        print("Woof!")

class Cat(Animal):
    def make_sound(self):
        print("Meow!")

# animal = Animal()  # Error: Can't instantiate abstract class
dog = Dog()
dog.make_sound()  # Output: Woof!
cat = Cat()
cat.make_sound()  # Output: Meow!