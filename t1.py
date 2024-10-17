import traceback
import inspect

def func1():
    print("In func1:")
    print_stack_trace()

def func2():
    print("In func2:")
    print_stack_trace()
    func1()

def func3():
    print("In func3:")
    print_stack_trace()
    func2()

def print_stack_trace():
    # This will print the stack trace of the current function call
    stack = inspect.stack()
    traceback.print_stack(f=stack[1][0])

# Call the top-level function
func3()
