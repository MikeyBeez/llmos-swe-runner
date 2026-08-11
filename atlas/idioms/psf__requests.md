- NEVER hit the network. Requests bugs are observable OFFLINE: build a
  Request and call .prepare() -- headers, URL encoding, body, cookies and
  auth are all decided at prepare time and can be asserted on directly.
  A reproduction that needs a live server will hang or flake in this
  environment and proves nothing about the library.
- For session/adapter behaviour, mount a custom adapter whose send()
  records the PreparedRequest and returns a canned Response -- the
  recorded object is the evidence.
