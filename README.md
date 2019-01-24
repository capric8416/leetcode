# LeetCode

## algorithms

### install
```bash
cd leetcode
python3 -m venv leetcode
leetcode/bin/python -m pip install -r requirements.txt
```


### pull
#### pull toc
```bash
leetcode/bin/python cli.py pull toc
```
#### pull content
```bash
leetcode/bin/python cli.py pull content
```
#### pull source
```bash
leetcode/bin/python cli.py pull source
```
#### pull jupyter
```bash
leetcode/bin/python cli.py pull jupyter
```


### account
#### conf
```bash
# open .conf/account.yml
# update account - user section, place your leetcode account
```
#### sign in
```bash
leetcode/bin/python cli.py account sign_in
```
#### sign out
```bash
leetcode/bin/python cli.py account sign_out
```


### push
#### submit
```bash
leetcode/bin/python cli.py push submit algorithms/python3/two_sum.py
```
