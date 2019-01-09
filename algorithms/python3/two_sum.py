# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Given an array of integers, return indices of the two numbers such that they add up to a specific target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

Example:

Given nums = [2, 7, 11, 15], target = 9,

Because nums[0] + nums[1] = 2 + 7 = 9,
return [0, 1].
"""

""" ==================== body ==================== """


class Solution:
    def twoSum(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """

        cache = {}
        for i, v in enumerate(nums):
            sub = target - v
            if sub in cache:
                return [cache[sub], i]
            cache[v] = i


""" ==================== body ==================== """


if __name__ == '__main__':
    sln = Solution()
    print(sln.twoSum(nums=[2, 7, 11, 15], target=9))
    print(sln.twoSum(nums=[2, 7, 11, 15, 18, 29, 37], target=26))
