import asyncio

async def increment():
    return 1

async def decrement():
    return -1

async def onehundred():
    num = 0
    for i in range(100):
        num += await increment()
        num += await decrement()
    return num

if __name__ == "__main__":
    print(asyncio.run(onehundred()))
