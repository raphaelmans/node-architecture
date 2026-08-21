---
status: accepted
---

# Keep tool specializations thin and version-resolved

This repository owns durable architecture conventions, while authoritative vendor sources own version-sensitive tool behavior and syntax. Tool specializations will remain thin and resolve implementation details from sources matching the detected or selected version at execution time, accepting less embedded convenience in exchange for accuracy and avoiding stale configuration guidance.
