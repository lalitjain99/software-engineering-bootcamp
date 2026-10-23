# Observations — Blocking Synchronous and Asynchronous calls

1. What is the difference between a coroutine function and a coroutine object?
Ans: Coroutine function is function which is defined using async def while coroutine object is awaitable asynchronous object

2. When does the body of a coroutine start executing?
Ans: when coroutine object is awaited then body of a coroutine starts execution

3. What difference did you observe between `time.sleep()` and `await asyncio.sleep()`?
Ans: time.sleep is a synchronous call while asyncio.sleep is coroutine function which is awaitable

4. Why is the concurrent elapsed time close to the longest individual delay rather than the sum of all delays?
Ans: In the concurrent calls all the 3 task (products, inventory, reviews) started simultaneously then gather waited for all to task to be completed before returning the result. On other hand sequential task were executed one by one hence the total time is close to addition of all the delays

5. What does `asyncio.gather()` coordinate?
Ans: it coordinate all the task declared/assigned by the gather function

6. What does `asyncio.Semaphore(2)` limit?
Ans it limit maximum number of active task at a give time

7. Did the script create all tasks at once, and did all of them run at the same time? Explain the difference.
Ans: No, Script does not create all task at once rather it run them at same time

8. What production resources could be protected with a semaphore?
Ans: CPU , memory

9. Why is a semaphore not a replacement for timeouts and retries?
Ans semaphore only control maximum active task at a particular time, it does not do anything is a task fail or controls the time take by a task or what happens to waiting task.

10. In a real FastAPI application, which parts of this lab would correspond to database or HTTP calls?
Ans asyncio sleep would correspond to databse or http calls