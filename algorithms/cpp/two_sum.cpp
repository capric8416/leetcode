/*
Given an array of integers, return indices of the two numbers such that they add up to a specific target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

Example:

Given nums = [2, 7, 11, 15], target = 9,

Because nums[0] + nums[1] = 2 + 7 = 9,
return [0, 1].
*/


#include <iostream>
#include <map>
#include <vector>

using namespace std;


/* ==================== body ==================== */


class Solution {
public:
    vector<int> twoSum(vector<int> &nums, int target) {
        map<int, int> cache;
        for (int i = 0; i < nums.size(); i++) {
            int v = nums[i];
            int sub = target - v;
            if (cache.find(sub) != cache.end()) {
                vector<int> result = {cache[sub], i};
                return result;
            }
            cache[v] = i;
        }

        return vector<int>();
    }
};


/* ==================== body ==================== */


int main() {
    auto sln = Solution();
    vector<int> n{2, 7, 11, 5};
    auto res = sln.twoSum(n, 9);

    for (auto item: res) {
        cout << item << ", ";
    }
    cout << endl;

    return 0;
}
