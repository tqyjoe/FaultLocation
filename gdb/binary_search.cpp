#include <iostream>
using std::cout;
using std::endl;

int binary_search(int *ary, unsigned int ceiling, int target)
{
    unsigned int floor = 0;
    while (ceiling > floor) {
        unsigned int pivot = (ceiling + floor) / 2;
        if (ary[pivot] < target)
            floor = pivot + 1;
        else if (ary[pivot] > target)
            ceiling = pivot - 1;
        else
            return pivot;
    }
    return -1;
}

int main()
{
    int a[] = {1, 2, 4, 5, 6};
    cout << binary_search(a, 5, 7) << endl; // -1
    cout << binary_search(a, 5, 6) << endl; // 4
    cout << binary_search(a, 5, 5) << endl; // 期望3，实际运行结果是-1
    return 0;
}