from functools import cache

# def di():
#     print("decorator initiated")

# def mongocache(f, l=10):
#     di()
#     def wf(*args, **kwargs):
#         print("decorator", *args, **kwargs)
#         return f(*args, **kwargs)
    
#     return wf

# @mongocache(l=10)
# def f(a):
#     print("function f", a)

# @mongocache(l=5)
# def g(a):
#     print("function g", a)

# f(1)
# f(2)

# g(1)
# g(2)



def decoratorFunctionWithArguments(arg1, arg2, arg3):
    print("Outside wrap()")
    def wrap(f):
        print("Inside wrap()")
        def wrapped_f(*args):
            print("Inside wrapped_f()")
            print("Decorator arguments:", arg1, arg2, arg3)
            val = f(*args)
            print(val)
            print("After f(*args)")
        return wrapped_f
    return wrap

@decoratorFunctionWithArguments("hello", "world", 42)
def sayHello(a1, a2, a3, a4):
    print('sayHello arguments:', a1, a2, a3, a4)
    return "return value"

print("After decoration")
print("Preparing to call sayHello()")
sayHello("say", "hello", "argument", "list")
print("after first sayHello() call")
sayHello("a", "different", "set of", "arguments")
print("after second sayHello() call")
