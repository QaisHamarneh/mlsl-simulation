# from scenarios.test_scenarios import *

def calc(n: int, m: int, sum:int = 0):
    if n > 0:
        return calc(n - m, m, sum + n)
    else:
        return sum
    

def calc_2(n: int, m: int):
    sum = 0
    while n > 0:
        sum += n
        n -= m
    return sum

def main():
    # setup_2_car_scenarios(**CHANGE_TO_RIGHT_LANESEGMENT_LEFT_AND_RIGHT)
    for i in range(10, 101, 10):
        for j in range(1, 6, 1):
            assert calc(i, j) == calc_2(i, j), f"{i}, {j}, {calc(i, j)}"

if __name__ == '__main__':
    main()
