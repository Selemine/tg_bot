def decorator(func):

    def wrapper(*args, **kwargs):

        print(" A", end=' ')

        result = func(*args, **kwargs)

        print("B ", end=' ')

        return result

    return wrapper

 

@decorator

def greet(name: str) -> None:

    print(f"Hello, {name}!", end=' ')

 

greet("Alice")