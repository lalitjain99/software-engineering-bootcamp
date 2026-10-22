# Observations — Blocking Synchronous and Asynchronous calls

1. What is the difference between a coroutine function and a coroutine object?
Ans: Coroutine function is function which is defined using async def while coroutine object is awaitable asynchronous object

2. When does the body of a coroutine start executing?
Ans: when is awaited

3. What difference did you observe between `time.sleep()` and `await asyncio.sleep()`?
Ans: time.sleep is a synchronous call while asyncio.sleep is coroutine function which is awaitable

4. Why is the concurrent elapsed time close to the longest individual delay rather than the sum of all delays?
Ans: In the concurrent calls all the 3 task (products, inventory, reviews) started simultaneously then gather waited for all to task to be completed before returning the result. On other hand sequential task were executed one by one hence the total time is close to addition of all the delays

5. What does `asyncio.gather()` coordinate?
Ans: it coordinate all the task declared/assigned by the gather function

6. What does `asyncio.Semaphore(2)` limit?
Ans it limit maximum number of active task at a give time

7. Did the script create all tasks at once, and did all of them run at the same time? Explain the difference.
Ans: 
8. What production resources could be protected with a semaphore?
9. Why is a semaphore not a replacement for timeouts and retries?
10. In a real FastAPI application, which parts of this lab would correspond to database or HTTP calls?