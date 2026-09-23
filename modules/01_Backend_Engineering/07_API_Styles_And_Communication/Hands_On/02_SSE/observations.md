1. Who initiated the SSE connection?
Ans: a browser or curl client initiates a SSE connection
2. How many HTTP requests did curl make while several events arrived?
Ans: One request for the one event stream
3. Did the HTTP response finish after the first event?
Ans: No , HTTP reponse does not finish after first event. it only close when client or server or network is closed
4. In which direction did data travel after the connection was opened?
Ans: Data travels from server to client 
5. Could the browser send a stock-change command through the same SSE stream?
Ans: No, for another set of information new SSE needs to be initiated
6. What is the purpose of `Content-Type: text/event-stream`?
Ans: it tells the server that client will prefer text/event-stream response
7. What happened when you pressed `Ctrl+C` or closed the browser tab?
Ans: It will end the connect and stream will be ended
8. Explain the most important difference between SSE and a webhook.
Ans: Each event occurs on seperate HTTP call in webhook while Single HTTP remains open for receiveing multi event steams
9. Why might an event contain an `id` field?
Ans It identifies the event and what changes are associated with it