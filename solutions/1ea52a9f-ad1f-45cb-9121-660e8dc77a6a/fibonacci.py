import math
import sys

def fibonacci(n):
    """Calculate fibonacci number using dynamic programming."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    print("Fibonacci Calculator")
    for i in range(10):
        print(f"  fib({i}) = {fibonacci(i)}")

    # Also demonstrate math module usage
    print(f"  pi = {math.pi:.6f}")
    print(f"  sqrt(144) = {math.sqrt(144)}")
    print("Done!")

if __name__ == "__main__":
    main()
