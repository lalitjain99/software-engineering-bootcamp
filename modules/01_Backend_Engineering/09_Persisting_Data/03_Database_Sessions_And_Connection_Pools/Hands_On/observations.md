1. What is the pool's maximum number of connections?

Ans: 2

2. Why does one worker receive a checkout timeout?

Ans: two request was already keeping all the connection available to the pool busy for more than checkout timeout hence the next request was not able to find any availabe with in checkout timeout limit hence received error PoolTimeOut error

3. What is the difference between an idle and an in-use connection?

Ans: idle connection means network is open between application and database server and ready to serve a request while in use connection means connection is serving a connection at this point of time.

4. Which transaction is committed and which is rolled back?

Ans: The transaction in `request-A` is committed. It starts a transaction, runs `UPDATE products SET price = 2400 WHERE id = 101`, and calls `commit()`. The transaction in `request-B` is rolled back. It starts a transaction, tries to insert `KEY-101`, raises a `ValueError`, and the pool's `connection()` context manager triggers `rollback()` before returning the connection to the pool.

5. What happens to the broken connection?

Ans: A broken connection is discarded and is replaced by a new connection with different id where pool manages the overall connection limit

6. Why is the replacement connection given a new ID?

Ans: so that request can know that this is new connection rather than a previous fixed connection

7. What would happen if `checkout_timeout` were increased?

Ans if checkout_timeout is increased than request can wait longer for available connections. It will be particularly helpful if the request/query is taking longer to complete. So rather than request failing with pooltimeout error it can get a connection available to be executed

8. What production behavior does this simulation simplify?

Ans: this simulation mimic the pool behaviour.
1. Pool running as max connection limit
2. What happens to a request is all connection are busy
3. What action does pool and application take in case of broken connection and incompleted transactions
4. Connection being available to pool again once finished with transaction


9. Why should application code avoid holding a database connection while calling an external service?

Ans: A database connection is a scarce shared resource. If the app keeps a connection checked out while waiting for an external API or another slow network dependency, that connection stays idle and unavailable for other requests. This reduces throughput, increases latency, and can trigger pool timeouts under load. The app should release the DB work quickly and do the external call outside the database transaction.

10. Why would increasing `max_size` not necessarily improve performance?

Ans: Increasing `max_size` only allows more requests to run at the same time; it does not make each query faster. If the database, app, or network is already saturated, more open connections can create lock contention, higher CPU and memory usage, and more context switching. In production, a larger pool can hurt performance if the system cannot handle the added concurrency efficiently.