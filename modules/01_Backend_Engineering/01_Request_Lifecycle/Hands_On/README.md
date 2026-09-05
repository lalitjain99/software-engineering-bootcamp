# Hands-On Exercise — Observe a Real FastAPI Request

> **Time:** approximately 30–45 minutes  
> **Goal:** Observe the request-response flow instead of only reading about it.

## What You Will Verify

By the end, you should be able to point to:

- The host and port receiving the request
- The FastAPI route that matches it
- Input conversion and validation
- The Python function's return value
- The response status line, headers, and JSON body

Nothing beyond Topic 01 is required.

---

## 1. Open the Repository Root

All Python exercises share the root-level `pyproject.toml` and `uv.lock`. Run the remaining commands from the repository root.

## 2. Install the Shared Dependencies

```bash
uv sync
```

## 3. Start the Server

```bash
uv run uvicorn app.main:app --app-dir modules/01_Backend_Engineering/01_Request_Lifecycle/Hands_On --reload --host 127.0.0.1 --port 8000
```

Read the startup message and identify:

- Host: `127.0.0.1`
- Port: `8000`
- Application import: `app.main:app`

Keep this terminal running. Use another terminal for the requests.

---

## 4. Successful Request

Before running the command, predict the status code, one response header, and the body.

```bash
curl -i http://127.0.0.1:8000/products/101
```

The `-i` option displays the response status line and headers as well as the body.

Identify these three sections:

```text
Status line
Response headers
Response body
```

Then connect the output to the code:

```python
@app.get("/products/{product_id}")
def get_product(product_id: int):
    ...
```

---

## 5. Input Validation

Predict whether the function body will run:

```bash
curl -i http://127.0.0.1:8000/products/abc
```

Observe that FastAPI cannot convert `abc` into the declared integer parameter.

Compare it with:

```bash
curl -i http://127.0.0.1:8000/products/101
```

---

## 6. Product Not Found

Run:

```bash
curl -i http://127.0.0.1:8000/products/999
```

Here, `999` is a valid integer, so the function runs. The function then decides that the product does not exist and raises `HTTPException`.

Notice the difference:

| Request | Does validation pass? | Does the function run? |
|---|:---:|:---:|
| `/products/abc` | No | No |
| `/products/999` | Yes | Yes |

---

## 7. Prove the Role of the Port

Stop the server with `Ctrl+C`, then restart it on port `8001`:

```bash
uv run uvicorn app.main:app --app-dir modules/01_Backend_Engineering/01_Request_Lifecycle/Hands_On --reload --host 127.0.0.1 --port 8001
```

First try the old port:

```bash
curl -i http://127.0.0.1:8000/products/101
```

Then try the new port:

```bash
curl -i http://127.0.0.1:8001/products/101
```

The machine has not changed—both URLs use `127.0.0.1`. The application moved from port `8000` to `8001`, so only the second request reaches it.

---

## 8. Trace One Request in Your Own Words

Complete this flow for the successful request:

```text
The client sends ________________________________

The operating system uses _______________________

FastAPI matches _________________________________

FastAPI converts ________________________________

The function returns ____________________________

FastAPI creates _________________________________
```

## Completion Check

Share the following after completing the exercise:

1. The status line from the successful request
2. The `Content-Type` response header
3. Why `/products/abc` does not execute the function
4. Why `/products/999` does execute the function
5. What changed when the server moved to port `8001`

When these are clear, Topic 01 is complete and Topic 02—HTTP methods—can begin.
