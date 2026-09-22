# Hands-On Exercise — Observe HTTP, TCP, and TLS

> **Time:** approximately 45–60 minutes  
> **Goal:** Follow one request through connection setup, the HTTP exchange, and (for HTTPS) TLS setup.

You will reuse the Product API from Topic 05. There is no new endpoint to implement and no new Python dependency.

## Before You Start

Run commands in a **WSL or Linux shell** from the repository root. You need `uv`, `curl`, and a working internet connection for the HTTPS step. If you use Windows PowerShell, use `curl.exe` instead of `curl`; the output-only examples using `/dev/null` below are written for WSL/Linux.

Start the previous Product API in terminal 1:

```bash
uv run uvicorn main:app --app-dir modules/01_Backend_Engineering/05_Status_Codes_And_Errors/Hands_On --host 127.0.0.1 --port 8000
```

Leave it running. Open terminal 2 for the following commands.

> A line starting with `*` in `curl -v` is curl's diagnostic output. A line starting with `>` shows HTTP sent by curl; `<` shows HTTP received. The exact output can vary across systems.

## 1. Observe One Plain HTTP Request

Run:

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/101
```

Find these observations in the output:

- Where curl says it connects to `127.0.0.1` on port `8000`.
- The request line `> GET /products/101 HTTP/1.1` and its request headers.
- The response status, `Content-Type`, and JSON body.

In your own words, identify which part tells the server **what product to get**, which part describes **the response format**, and which part reports **success or failure**.

At this point you have seen a readable HTTP request and response. The local URL starts with `http://`; this step does not set up TLS.

## 2. Observe Connection Reuse

Send **two URLs in the same curl command**:

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/101 http://127.0.0.1:8000/products/102
```

Look for two request lines, two response status lines, and a reuse message before the second request. Depending on curl's version, wording such as “Re-using existing connection” may vary. Both requests should use the same client-to-server connection if it remains available.

Now run the two requests in **separate** curl commands:

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/101
```

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/102
```

A fresh command-line `curl` process normally has no access to the previous process's connection pool. Explain why the first pair can reuse a connection and this pair generally cannot.

> If the single-command pair does not reuse a connection, record what the verbose output says about closing it. A proxy, server policy, or different curl behavior can affect the result; do not assume your code is wrong.

## 3. Distinguish an HTTP Error from a Connection Error

First, request a product that is absent from the store:

```bash
curl -v --http1.1 http://127.0.0.1:8000/products/999
```

You should see an HTTP response with `404`. The client successfully connected and the server processed the request.

Next, try a port on which you have **no server listening** (for example `8001`):

```bash
curl -v --connect-timeout 3 http://127.0.0.1:8001/products/101
```

You should see a connection error **without an HTTP status line**. If port `8001` is in use on your machine, choose another unused port. Explain why your FastAPI endpoint cannot return `404` in this case.

## 4. Observe an HTTPS Handshake

Use a public site for this step. Your local Uvicorn command above serves plain HTTP, so changing its URL to `https://` would not turn on TLS.

```bash
curl -v -o /dev/null https://example.com/
```

Search the diagnostic output for:

- The hostname resolution or proxy connection information, depending on your network.
- The connection to the destination or your organization's proxy.
- A negotiated TLS version, certificate verification information, or equivalent TLS details.
- The HTTP request and response once the secure connection is ready.
- The HTTP version shown in the request/response, if your curl build displays it.

Curl shows the HTTP request **in readable form inside its own diagnostic output** because it knows the request before encryption and the response after decryption. These lines do **not** prove that a network observer could read the same HTTP messages on the wire.

The exact certificate lines and HTTP version differ by operating system, curl build, server, and corporate proxy. If the request fails due to an untrusted company proxy certificate or blocked internet access, record that error rather than bypassing certificate verification.

**Optional comparison:** Try `curl -v https://127.0.0.1:8000/products/101`. It should fail during TLS negotiation because the local Uvicorn server was started for plain HTTP. No FastAPI endpoint needs to be changed to explain the result.

## Record Your Findings

Add a short file named `observations.md` inside this `Hands_On` directory and fill in **your own observations**:

| Scenario | Did a connection succeed? | HTTP status, if any | What layer explains the result? |
|---|---|---|---|
| `/products/101` on port 8000 |  |  |  |
| Two requests in one curl command |  |  |  |
| `/products/999` on port 8000 |  |  |  |
| Request to an unused port |  |  |  |
| HTTPS request to `example.com` |  |  |  |

Also answer briefly:

1. Which component defines the meaning of `GET` and `404`?
2. Which component manages the server's listening port and idle client connections: your FastAPI endpoint or Uvicorn?
3. In the HTTPS test, at what point can the server understand the HTTP request?
4. Why can curl show readable HTTP text even though the HTTPS exchange is protected in transit?

## Completion

Push `observations.md` to the repository and share that it is ready. I will review your **observations and explanations** in GitHub. Then we will do Topic 06 interview questions one at a time here in chat and create `Interview.md` after reviewing your answers.

### Reference

- [curl manual — verbose output and connection reuse](https://curl.se/docs/manpage.html)
