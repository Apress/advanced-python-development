num = 0

def increment():
    global num
    num += 1          # 5	0	LOAD_GLOBAL              0 (num)
                      # 	2	LOAD_CONST               1 (1)
                      # 	4	INPLACE_ADD
                      # 	6	STORE_GLOBAL             0 (num)

    return None       # 10	8	LOAD_CONST               0 (None)
                      # 	10	RETURN_VALUE

if __name__ == "__main__":
   import dis
   dis.dis(increment)