## 1. Observe One Plain HTTP Request
### Request Response
```
* Trying 127.0.0.1:8000...
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 53345 
* using HTTP/1.x
> GET /products/101 HTTP/1.1
> Host: 127.0.0.1:8000
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off

< HTTP/1.1 200 OK
< date: Tue, 22 Sep 2026 10:49:08 GMT
< server: uvicorn
< content-length: 90
< content-type: application/json
< 
{"product_id":101,"sku":"KEY-001","name":"Keyboard","price":2500,"category":"electronics"}* Connection #0 to host 127.0.0.1:8000 left intact
```

Q1: identify which part tells the server **what product to get**?

Ans: Request line of the request tell us about what product to get 

   `GET /products/101 HTTP/1.1`

Q2: which part describes **the response format**?

Ans: content-type in the response line tell us the response format

`content-type: application/json`


Q3: which part reports **success or failure**.

Ans: Response line tell us the success or failer

`HTTP/1.1 200 OK`


## 2. Observe Connection Reuse
### Two Request Simlutaneously
```
curl -v --http1.1 http://127.0.0.1:8000/products/101 http://127.0.0.1:8000/products/102
* Trying 127.0.0.1:8000...
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 56913 
* using HTTP/1.x
> GET /products/101 HTTP/1.1
> Host: 127.0.0.1:8000
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 200 OK
< date: Tue, 22 Sep 2026 10:50:17 GMT
< server: uvicorn
< content-length: 90
< content-type: application/json
< 
{"product_id":101,"sku":"KEY-001","name":"Keyboard","price":2500,"category":"electronics"}* Connection #0 to host 127.0.0.1:8000 left intact
*Reusing existing http: connection with host 127.0.0.1*
> GET /products/102 HTTP/1.1
> Host: 127.0.0.1:8000
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 200 OK
< date: Tue, 22 Sep 2026 10:50:17 GMT
< server: uvicorn
< content-length: 83
< content-type: application/json
< 
{"product_id":102,"sku":"KEY-002","name":"Shirt","price":1500,"category":"Apperal"}* Connection #0 to host 127.0.0.1:8000 left intact
```
### Individual Request 1

```
curl -v --http1.1 http://127.0.0.1:8000/products/101
*   Trying 127.0.0.1:8000...
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 55757 
* using HTTP/1.x
> GET /products/101 HTTP/1.1
> Host: 127.0.0.1:8000
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 200 OK
< date: Tue, 22 Sep 2026 10:56:51 GMT
< server: uvicorn
< content-length: 90
< content-type: application/json
< 
{"product_id":101,"sku":"KEY-001","name":"Keyboard","price":2500,"category":"electronics"}* Connection #0 to host 127.0.0.1:8000 left intact
```
### Individual Request 2

```
curl -v --http1.1 http://127.0.0.1:8000/products/102
*   Trying 127.0.0.1:8000...
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 55759 
* using HTTP/1.x
> GET /products/102 HTTP/1.1
> Host: 127.0.0.1:8000
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 200 OK
< date: Tue, 22 Sep 2026 10:56:58 GMT
< server: uvicorn
< content-length: 83
< content-type: application/json
< 
{"product_id":102,"sku":"KEY-002","name":"Shirt","price":1500,"category":"Apperal"}* Connection #0 to host 127.0.0.1:8000 left intact
```

Q: Explain why the first pair can reuse a connection and this pair generally cannot.
Ans Reusing existing http: connection with host 127.0.0.1* this line show that 2nd request used the existing tcp connection.
So basically tcp connection remain live for certain time period after completion of the request. So if new request arrives with in that time frame then it used the same tcp connection rather than buidling new one. in the second case where we are making two separate request , second request didnot arrived with in the timeframe hence it created its own tcp connection

## 3. Distinguish an HTTP Error from a Connection Error

```
curl -v --http1.1 http://127.0.0.1:8000/products/999
*   Trying 127.0.0.1:8000...
* Established connection to 127.0.0.1 (127.0.0.1 port 8000) from 127.0.0.1 port 55760 
* using HTTP/1.x
> GET /products/999 HTTP/1.1
> Host: 127.0.0.1:8000
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 404 Not Found
< date: Tue, 22 Sep 2026 10:57:29 GMT
< server: uvicorn
< content-length: 108
< content-type: application/json
< 
{"detail":{"code":"PRODUCT_NOT_FOUND","message":"Product 999 does not exists","details":{"product_id":999}}}* Connection #0 to host 127.0.0.1:8000 left intact

(software-engineering-bootcamp) D:\software-engineering-bootcamp>curl -v --connect-timeout 3 http://127.0.0.1:8001/products/101
*   Trying 127.0.0.1:8001...
* connect to 127.0.0.1 port 8001 from 0.0.0.0 port 55763 failed: Connection refused
* Failed to connect to 127.0.0.1:8001 after 2024 ms: Could not connect to server
* closing connection #0
curl: (7) Failed to connect to 127.0.0.1:8001 after 2024 ms: Could not connect to server
```
Q: when used port `8001` on your machine. Explain why your FastAPI endpoint cannot return `404` in this case.

Ans: In the first case when application server is listening on the port 8000 , request throws an error 404. In this case it is valid request and reached the correct port where a socket is listening but since resource with product id 999 is not found hence error is generated with status code 404

while in second case there is no application server is listening at port 8001 hence it never reached to the application. Since no 8001 server port is available hence got the error as connection refused 

## 4. Observe an HTTPS Handshake

```
curl -v -o NUL https://example.com/
* Host example.com:443 was resolved.
* IPv6: 2606:4700:90c5:72db:f264:4:ef6b:ff98
* IPv4: 172.66.147.243, 104.20.23.154
*   Trying [2606:4700:90c5:72db:f264:4:ef6b:ff98]:443...
* schannel: disabled automatic use of client certificate
* ALPN: curl offers http/1.1
* ALPN: server accepted http/1.1
* Established connection to example.com (2606:4700:90c5:72db:f264:4:ef6b:ff98 port 443) from 2405:201:4025:40da:487a:285d:43b4:1fe0 port 49180 
  % Total    % Received % Xferd  Average Speed  Time    Time    Time   Current
                                 Dload  Upload  Total   Spent   Left   Speed
  0      0   0      0   0      0      0      0                              0* using HTTP/1.x
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/8.21.0
> Accept: */*
> 
* Request completely sent off
* schannel: remote party requests renegotiation
* schannel: renegotiating SSL/TLS connection
* schannel: SSL/TLS connection renegotiated
< HTTP/1.1 200 OK
< Date: Tue, 22 Sep 2026 12:49:43 GMT
< Content-Type: text/html
< Transfer-Encoding: chunked
< Connection: keep-alive
< Server: cloudflare
< last-modified: Tue, 15 Sep 2026 23:41:26 GMT
< allow: GET, HEAD
< Accept-Ranges: bytes
< Age: 5751
< cf-cache-status: HIT
< CF-RAY: a3f16e6998870997-DEL
< 
{ [571 bytes data]
100    559   0    559   0      0   3202      0                              0
* Connection #0 to host example.com:443 left intact

```
- The hostname resolution or proxy connection information, depending on your network.
Ans: Below line shows that hostname has been resolved 
```
* Host example.com:443 was resolved.
* IPv6: 2606:4700:90c5:72db:f264:4:ef6b:ff98
* IPv4: 172.66.147.243, 104.20.23.154

```

- The connection to the destination or your organization's proxy.
Ans: Below lines from the logs shows that connection has been established via port 443

```
Established connection to example.com (2606:4700:90c5:72db:f264:4:ef6b:ff98 port 443) from 2405:201:4025:40da:487a:285d:43b4:1fe0 port 49180 
```

- A negotiated TLS version, certificate verification information, or equivalent TLS details.
Ans: Below line from the request logs shows the TSL version and certificate verification
```
* schannel: disabled automatic use of client certificate
* ALPN: curl offers http/1.1
* ALPN: server accepted http/1.1
* schannel: remote party requests renegotiation
* schannel: renegotiating SSL/TLS connection
* schannel: SSL/TLS connection renegotiated
```
The handshake is successful when curl finishes negotiating security parameters and proceeds to send application data without throwing a certificate validation error.

- The HTTP request and response once the secure connection is ready.
Ans: Below logs shows that https request and reponse 
```
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/8.21.0
> Accept: */*

< HTTP/1.1 200 OK
< Date: Tue, 22 Sep 2026 12:49:43 GMT
< Content-Type: text/html
< Transfer-Encoding: chunked
< Connection: keep-alive
< Server: cloudflare
< last-modified: Tue, 15 Sep 2026 23:41:26 GMT
< allow: GET, HEAD
```
Seeing lines starting with > (sent by you) and < (received from the server) confirms the secure tunnel is passing HTTP data.

- The HTTP version shown in the request/response, if your curl build displays it.
Ans: Below logs shows the details of https version request and response version
```
> GET / HTTP/1.1

< HTTP/1.1 200 OK

```

| Scenario | Did a connection succeed? | HTTP status, if any | What layer explains the result? |
|---|---|---|---|
| `/products/101` on port 8000 | Yes | 200 | Request line in response |
| Two requests in one curl command | Yes  | 200  | Request line in response |
| `/products/999` on port 8000 | Yes | 404 |Request line in response  |
| Request to an unused port | No  | No | NA |
| HTTPS request to `example.com` | Yes | 200 | Request line in response  |




1. Which component defines the meaning of `GET` and `404`?
Ans:0 Request line in HTTP request defines the meaning of "GET" and status code defines the meaning of "404".

2. Which component manages the server's listening port and idle client connections: your FastAPI endpoint or Uvicorn?
Ans Uvicorn. It create a operating system object called socket which listen to a particular port.

3. In the HTTPS test, at what point can the server understand the HTTP request?
Ans: when HTTP client decrypt the bytes received via tcp

4. Why can curl show readable HTTP text even though the HTTPS exchange is protected in transit?
Ans: curl can show the readable HTTP text because it performs the encryption before sending the data and the decryption after receiving it.Because curl has access to the unencrypted data at the very edges of the connection (right before encryption and right after decryption), its -v (verbose) flag can print the readable HTTP messages for your convenience.



