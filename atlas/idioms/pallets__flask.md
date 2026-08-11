- The observable is the RESPONSE. Build a minimal app in the script, use
  app.test_client() (no server, no network), and assert on response
  status/headers/data. Internals like url_map or config are inputs, not
  evidence -- exercise a request through the stack.
- For app-context bugs (g, current_app, teardown), the reproduction must
  actually enter and exit the context (with app.app_context(): ...);
  reading attributes outside a context observes a different code path.
