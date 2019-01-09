/*
Given an array of integers, return indices of the two numbers such that they add up to a specific target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

Example:

Given nums = [2, 7, 11, 15], target = 9,

Because nums[0] + nums[1] = 2 + 7 = 9,
return [0, 1].
*/


package main

import "fmt"


/* ==================== body ==================== */


func twoSum(nums []int, target int) []int {
	cache := map[int]int{}
	for i, v := range nums {
		sub := target - v
		if j, ok := cache[sub]; ok {
			return []int{j, i}
		}
		cache[v] = i
	}

	return []int{}
}


/* ==================== body ==================== */


func main() {
	result := twoSum([]int{2, 7, 11, 15}, 9)
	fmt.Println(result)
}
