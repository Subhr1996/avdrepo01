#search a number in a list useing binary search
#a = [10, 20, 30, 40, 50]
def binary_search(a, key):
    low, high = 0, len(a)-1
    while low <= high:
        mid = (low+high)//2
        if a[mid] == key:
            return mid
        elif a[mid] > key:
            high = mid - 1
        else:
            low = mid + 1
    return -1 
a = [10, 20, 30, 40, 50]
key = int(input("Enter your number : "))
res = binary_search(a, key)
if res != -1:
    print(f"{key} is present inside the list")
else:
    print(f"{key} is not present in the list") #answer